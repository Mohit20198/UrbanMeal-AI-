import os
import numpy as np
import pandas as pd
import streamlit as st
import redshift_connector
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
BASE_URL = "https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else None
CHAT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b") if os.getenv("GROQ_API_KEY") else "gpt-4o-mini"

NEW_REVIEWS = 500
TOK_K = 5
CACHE_FILE = "ai/review_embeddings.parquet"

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

def read_reviews_from_redshift():
    conn = redshift_connector.connect(
        host=os.getenv("REDSHIFT_HOST"),
        port=int(os.getenv("REDSHIFT_PORT", "5439")),
        database=os.getenv("REDSHIFT_DATABASE", "dev"),
        user=os.getenv("REDSHIFT_USER"),
        password=os.getenv("REDSHIFT_PASSWORD"),
        ssl=True
    )

    query = f"""
        SELECT review_id, city, rating, comment
        FROM staging.stg_reviews
        WHERE comment IS NOT NULL
        ORDER BY RANDOM()
        LIMIT {NEW_REVIEWS}
    """
    cursor = conn.cursor()
    cursor.execute(query)
    try:
        df = cursor.fetch_dataframe()
    except Exception:
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=cols)

    cursor.close()
    conn.close()

    df.columns = [col.lower() for col in df.columns]
    return df

def embed(texts):
    embedder = load_embedder()
    return embedder.encode(texts, show_progress_bar=False).tolist()

@st.cache_data()
def load_reviews():
    if os.path.exists(CACHE_FILE):
        return pd.read_parquet(CACHE_FILE)

    df = read_reviews_from_redshift()
    df['embedding'] = embed(df['comment'].tolist())
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    df.to_parquet(CACHE_FILE)
    return df

st.title("Chat with your UrbanMeal Reviews (Redshift + Groq)")
st.caption(f"Searching {NEW_REVIEWS} reviews from Redshift, answering with {CHAT_MODEL} on Groq")

def cosine_similarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

def find_similar_reviews(question, df):
    question_vector = embed([question])[0]

    scores = []
    for review_vector in df['embedding']:
        scores.append(cosine_similarity(question_vector, review_vector))

    df = df.copy()
    df['score'] = scores
    return df.nlargest(TOK_K, 'score')

def ask_llm(question, top_reviews):
    context = ""
    for _, row in top_reviews.iterrows():
        context += f" ({row['city']}, {row['rating']} stars) {row['comment']}\n"

    system_prompt = (
        "Answer ONLY using the customer reviews provided. "
        "Be concise. If the reviews don't cover it, say so."
    )

    user_prompt = f"Question: {question}\n\nReviews:\n{context}"

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content

review_df = load_reviews()

question = st.text_input(
    "Ask a question about your reviews:",
    placeholder="e.g. What are the most common complaints about delivery?"
)

if question:
    with st.spinner("Searching reviews and generating answer..."):
        top_reviews = find_similar_reviews(question, review_df)
        answer = ask_llm(question, top_reviews)

    st.markdown("**Answer:**")
    st.write(answer)

    with st.expander("Reviews used to build this answer"):
        st.dataframe(top_reviews[['city', 'rating', 'comment']], hide_index=True)