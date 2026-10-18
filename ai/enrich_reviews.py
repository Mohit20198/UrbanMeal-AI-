import os
import json
import redshift_connector
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
BASE_URL = "https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else None
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b") if os.getenv("GROQ_API_KEY") else "gpt-4o-mini"

SAMPLE_N = int(os.getenv("SAMPLE_N", "5"))
TOPICS = ["food quality", "delivery", "pricing", "service", "packaging", "other"]

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

SYSTEM_PROMPT = f"""
You classify customer reviews for a food delivery app.

For the review you are given, return:
- sentiment_label: positive, negative, or neutral
- sentiment_score: a number between -1.0 and 1.0
- topic: one of {TOPICS}
- key_issue: a short phrase of 6 words or less that describes the main issue in the review, if any. If there is no issue, return null

Reply as JSON in this exact format:
{{
    "sentiment_label": "<sentiment_label>",
    "sentiment_score": <sentiment_score>,
    "topic": "<topic>",
    "key_issue": "<key_issue>"
}}
"""

def get_connection():
    return redshift_connector.connect(
        host=os.getenv("REDSHIFT_HOST"),
        port=int(os.getenv("REDSHIFT_PORT", "5439")),
        database=os.getenv("REDSHIFT_DATABASE", "dev"),
        user=os.getenv("REDSHIFT_USER"),
        password=os.getenv("REDSHIFT_PASSWORD"),
        ssl=True
    )

def create_output_table(cursor):
    cursor.execute("CREATE SCHEMA IF NOT EXISTS ai;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai.review_enriched (
            review_id VARCHAR(64),
            sentiment_label VARCHAR(32),
            sentiment_score FLOAT,
            topic VARCHAR(64),
            key_issue VARCHAR(256),
            model VARCHAR(64),
            enriched_at TIMESTAMP DEFAULT SYSDATE
        );
    """)

def get_reviews_to_enrich(cursor):
    cursor.execute(f"""
        SELECT review_id, comment
        FROM "raw".reviews
        WHERE cast(review_id as varchar) NOT IN (SELECT review_id FROM ai.review_enriched)
          AND comment IS NOT NULL
        LIMIT {SAMPLE_N};
    """)
    return cursor.fetchall()

def classify_review(comment):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": comment}
        ]
    )
    answer = response.choices[0].message.content
    return json.loads(answer)

def save_results(cursor, results):
    """Insert all the enriched rows into Redshift."""
    print(f"Saving {len(results)} enriched reviews to Redshift...")
    cursor.executemany(
        """
        INSERT INTO ai.review_enriched
            (review_id, sentiment_label, sentiment_score, topic, key_issue, model)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        results,
    )

def main():
    conn = get_connection()
    cursor = conn.cursor()
    create_output_table(cursor)
    reviews = get_reviews_to_enrich(cursor)

    if len(reviews) == 0:
        print("No new reviews to enrich.")
        cursor.close()
        conn.close()
        return

    print(f"Enriching {len(reviews)} reviews using {MODEL} on Groq...")

    results = []
    for review_id, comment in reviews:
        print(f"Classifying review {review_id}: {comment}")
        try:
            labels = classify_review(comment)
            print(f"Labels for review {review_id}: {labels}")
            results.append((
                str(review_id),
                labels.get("sentiment_label", "neutral"),
                float(labels.get("sentiment_score", 0.0)),
                labels.get("topic", "other"),
                labels.get("key_issue"),
                MODEL
            ))
        except Exception as e:
            print(f"Error occurred while classifying review {review_id}: {e}")

    if results:
        save_results(cursor, results)
        print(f"Successfully saved {len(results)} enriched reviews to Redshift.")
        conn.commit()

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()