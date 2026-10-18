import os
import json
import numpy as np
import pandas as pd
import streamlit as st
import redshift_connector
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
BASE_URL = "https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else None
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b") if os.getenv("GROQ_API_KEY") else "gpt-4o-mini"

FORBIDDEN_WORDS = ['drop', 'delete', 'truncate', 'alter', 'update', 'insert', 'create', 'replace', 'grant', 'revoke']

EXAMPLE_QUESTIONS = [
    "Top 10 cities by GMV",
    "Which cuisine has the most orders?",
    "Average delivery time by city, worst first",
    "Cancel rate by payment method"
]

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

SCHEMA = """
Tables available in Amazon Redshift (schema 'marts'). Use bare table names, no schema prefix:
 
fct_orders(order_id, order_timestamp, order_date, customer_id, restaurant_id, city, cuisine,
           payment_method, order_status, is_delivered, sales_amount, discount,
           delivery_fee, gst, customer_rating, delivery_time_min)
dim_restaurants(restaurant_id, restaurant_name, city, cuisine, rating, rating_count, cost_for_two)
dim_customer(customer_id, customer_name, email, age, age_segment, gender, marital_status, occupation, income_band, education, family_size)
dim_food(f_id, food_name, veg_or_non_veg)
dim_date(date_day, year, month, month_name, day_name, is_weekend)
mart_daily_city_revenune(order_date, city, orders, delivered_orders, cancel_rate, gmv, aov)
mart_restaurant_performance(restaurant_id, restaurant_name, city, cuisine,
                            orders, revenue, avg_customer_rating, avg_delivery_min)
mart_delivery_sla(city, order_hour, delivered_orders, p50, p90)
mart_review_insights(city, topic, sentiment_label, reviews, avg_sentiment_score, avg_star_rating, flagged_issues)

Note: GMV means delivered revenue. Prefer the mart_ tables when they fit the question.
"""

SYSTEM_PROMPT = f"""
You are an Amazon Redshift SQL expert. Write ONE valid SELECT query that answers the question.
 
Rules:
- SELECT queries only, never modify data.
- Use Amazon Redshift SQL syntax (e.g., standard ANSI SQL, CASE statements, EXTRACT, DATEADD).
- Use bare table names without schema prefix (e.g. fct_orders, not marts.fct_orders).
- Add a LIMIT of 100 or less, unless the question asks for a single aggregated total.
- Reply as JSON in this exact format: {{"sql": "your query here"}}
 
{SCHEMA}
"""

@st.cache_resource
def get_connection():
    return redshift_connector.connect(
        host=os.getenv("REDSHIFT_HOST"),
        port=int(os.getenv("REDSHIFT_PORT", "5439")),
        database=os.getenv("REDSHIFT_DATABASE", "dev"),
        user=os.getenv("REDSHIFT_USER"),
        password=os.getenv("REDSHIFT_PASSWORD"),
        ssl=True
    )

def generate_sql(question):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]
    )
    answer = response.choices[0].message.content
    sql = json.loads(answer)["sql"]

    sql = sql.replace("marts.", "").replace("MARTS.", "")
    return sql.strip().rstrip(";")

def is_safe(sql):
    lowered = sql.lower()

    if not lowered.startswith("select") and not lowered.startswith("with"):
        return False

    for word in FORBIDDEN_WORDS:
        if word in lowered:
            return False

    return True

def run_query(sql):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SET search_path TO marts, public;")
    cursor.execute(sql)
    try:
        df = cursor.fetch_dataframe()
    except Exception:
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=cols)
    cursor.close()
    return df

st.title("Chat with your UrbanMeal Data (AWS Redshift + Groq)")
st.caption(f"Ask in English, {MODEL} on Groq writes the SQL, Amazon Redshift runs it")

with st.sidebar:
    st.header("Example Questions")
    for q in EXAMPLE_QUESTIONS:
        st.markdown(f" - {q}")

question = st.text_input(
    "Enter your question here", 
    placeholder="e.g. Top 10 restaurants by revenue in Bangalore"
)

if question:
    sql = generate_sql(question)
    st.code(sql, language="sql")

    if not is_safe(sql):
        st.error("The generated SQL is not safe to run. Please modify your question.")
    else:
        try:
            df = run_query(sql)
            st.success(f"{len(df)} rows returned")
            st.dataframe(df, hide_index=True)

            if len(df.columns) == 2 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
                st.bar_chart(df, x=df.columns[0], y=df.columns[1])

        except Exception as e:
            st.error(f"Error running query: {e}")
