import os
import json
import time
import numpy as np
import pandas as pd
import streamlit as st
import redshift_connector
import plotly.express as px
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("ai/.env")
load_dotenv()

st.set_page_config(
    page_title="UrbanMeal AI Analytics Hub",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #FF4B4B, #FF8533);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1rem;
        color: #888888;
        margin-bottom: 25px;
    }
    .kpi-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .kpi-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FF8533;
    }
    .kpi-lbl {
        font-size: 0.85rem;
        color: #AAAAAA;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# API Configurations
API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
BASE_URL = "https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else None
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b") if os.getenv("GROQ_API_KEY") else "gpt-4o-mini"
PROVIDER_NAME = "Groq" if os.getenv("GROQ_API_KEY") else "OpenAI"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

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

@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

NEW_REVIEWS = 500
TOK_K = 5
CACHE_FILE = "ai/review_embeddings.parquet"

def read_reviews_from_redshift():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT review_id, city, rating, comment
        FROM staging.stg_reviews
        WHERE comment IS NOT NULL
        ORDER BY RANDOM()
        LIMIT {NEW_REVIEWS};
    """)
    try:
        df = cursor.fetch_dataframe()
    except Exception:
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=cols)
    cursor.close()
    df.columns = [c.lower() for c in df.columns]
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

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def find_similar_reviews(query, df):
    q_vec = embed([query])[0]
    scores = [cosine_similarity(q_vec, r_vec) for r_vec in df['embedding']]
    df_copy = df.copy()
    df_copy['score'] = scores
    return df_copy.nlargest(TOK_K, 'score')

def ask_rag_llm(question, top_reviews):
    context = ""
    for _, row in top_reviews.iterrows():
        context += f"• ({row['city']}, {row['rating']}★) \"{row['comment']}\"\n"
    prompt = f"Question: {question}\n\nCustomer Reviews:\n{context}"
    system = "You are a customer feedback analyst for UrbanMeal. Answer ONLY using the customer reviews provided. Be specific, actionable, and concise."
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content

SCHEMA_SQL = """
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

def generate_sql(question):
    sys_prompt = f"""You are an Amazon Redshift SQL expert. Write ONE valid SELECT query that answers the question.
Rules:
- SELECT queries only, never modify data.
- Use Redshift syntax (ANSI SQL, CASE WHEN, EXTRACT, DATEADD).
- Use bare table names without schema prefix.
- Add LIMIT 100 or less, unless aggregating a single total.
- Reply as JSON in this exact format: {{"sql": "your query here"}}

{SCHEMA_SQL}"""
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": question}]
    )
    sql = json.loads(resp.choices[0].message.content)["sql"]
    return sql.replace("marts.", "").replace("MARTS.", "").strip().rstrip(";")

def is_safe_sql(sql):
    lowered = sql.lower()
    if not lowered.startswith("select") and not lowered.startswith("with"):
        return False
    for bad in ['drop', 'delete', 'truncate', 'alter', 'update', 'insert', 'create', 'replace', 'grant', 'revoke']:
        if bad in lowered:
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

# Header
st.markdown('<div class="main-title">🍔 UrbanMeal AI Analytics Hub</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">Powered by <b>Amazon Redshift Serverless</b> & <b>{PROVIDER_NAME} ({MODEL})</b></div>', unsafe_allow_html=True)

# Sidebar info
with st.sidebar:
    st.image("https://img.icons8.com/color/96/amazon-redshift.png", width=50)
    st.title("Redshift Status")
    st.success("Connected to Amazon Redshift (dev)")
    st.info(f"LLM Engine: **{PROVIDER_NAME}**\nModel: `{MODEL}`")
    st.markdown("---")
    st.markdown("### 💡 Quick Navigation")
    st.markdown("Use the tabs on the right to switch between **Text-to-SQL**, **RAG Customer Feedback**, and **Live KPIs**.")

# Tabs
tab_sql, tab_rag, tab_analytics = st.tabs([
    "🔍 Chat with Data (Text-to-SQL)",
    "💬 Chat with Reviews (RAG)",
    "📈 Live Warehouse Analytics"
])

# =====================================================================
# TAB 1: TEXT-TO-SQL
# =====================================================================
with tab_sql:
    st.subheader("Query Redshift in Plain English")
    st.caption("Ask questions about orders, revenue, delivery times, or restaurants. Groq writes the Redshift SQL, runs it, and visualizes the results.")

    example_sql = [
        "Top 10 cities by GMV",
        "Which cuisine has the most orders?",
        "Average delivery time by city, worst first",
        "Cancel rate by payment method",
        "Top 5 restaurants by revenue in Bangalore"
    ]
    
    col_ex1, col_ex2 = st.columns([3, 1])
    with col_ex1:
        selected_ex = st.selectbox("Or choose an example question:", [""] + example_sql)
    
    sql_question = st.text_input(
        "Enter your question about UrbanMeal data:",
        value=selected_ex if selected_ex else "",
        placeholder="e.g. Top 10 cities by total revenue"
    )

    if sql_question:
        with st.spinner(f"Writing Redshift SQL with {PROVIDER_NAME}..."):
            generated_query = generate_sql(sql_question)

        st.markdown("**Generated Redshift SQL:**")
        st.code(generated_query, language="sql")

        if not is_safe_sql(generated_query):
            st.error("The generated SQL contains restricted modification statements.")
        else:
            try:
                t0 = time.time()
                with st.spinner("Executing query on Amazon Redshift..."):
                    result_df = run_query(generated_query)
                t_elapsed = time.time() - t0

                st.success(f"Returned {len(result_df)} rows in {t_elapsed:.2f}s")
                st.dataframe(result_df, use_container_width=True, hide_index=True)

                # Automatic Plotting
                if len(result_df.columns) >= 2:
                    col_x = result_df.columns[0]
                    col_y = result_df.columns[1]
                    if pd.api.types.is_numeric_dtype(result_df[col_y]):
                        fig = px.bar(
                            result_df,
                            x=col_x,
                            y=col_y,
                            title=f"{col_y.replace('_', ' ').title()} by {col_x.replace('_', ' ').title()}",
                            color_discrete_sequence=["#FF8533"]
                        )
                        st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error executing SQL on Redshift: {e}")

# =====================================================================
# TAB 2: RAG REVIEW CHAT
# =====================================================================
with tab_rag:
    st.subheader("Chat with Customer Reviews via RAG")
    st.caption("Vector similarity search on free-text reviews (SentenceTransformers) + LLM analysis (Groq).")

    with st.spinner("Connecting to Redshift and caching review vectors..."):
        reviews_data = load_reviews()

    rag_examples = [
        "What are the most common complaints about delivery?",
        "Why do customers give 1-star ratings?",
        "What do customers praise about food packaging?",
        "Are customers happy with the pricing?"
    ]
    selected_rag = st.selectbox("Choose an example question:", [""] + rag_examples, key="rag_select")
    
    rag_question = st.text_input(
        "Ask a question about customer reviews:",
        value=selected_rag if selected_rag else "",
        placeholder="e.g. What are the most common complaints about delivery?",
        key="rag_input"
    )

    if rag_question:
        with st.spinner("Finding similar reviews & generating synthesis..."):
            top_revs = find_similar_reviews(rag_question, reviews_data)
            answer = ask_rag_llm(rag_question, top_revs)

        st.markdown("### 🤖 Answer:")
        st.markdown(f"> {answer}")

        with st.expander(f"🔍 Top {TOK_K} Reviews Used as Evidence"):
            for _, r in top_revs.iterrows():
                st.markdown(f"**{r['city']}** · **{r['rating']}★** | *\"{r['comment']}\"* (Similarity: `{r['score']:.3f}`)")
                st.markdown("---")

# =====================================================================
# TAB 3: LIVE WAREHOUSE ANALYTICS (BI)
# =====================================================================
with tab_analytics:
    st.subheader("Executive KPIs from Amazon Redshift")
    st.caption("Live aggregations queried directly from `marts.mart_daily_city_revenune` and `marts.fct_orders`.")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # High level KPIs
        cursor.execute("SELECT count(*) FROM marts.fct_orders;")
        total_orders = cursor.fetchone()[0]

        cursor.execute("SELECT sum(gmv), sum(orders) FROM marts.mart_daily_city_revenune;")
        kpi_row = cursor.fetchone()
        total_gmv = float(kpi_row[0] or 0)

        cursor.execute("SELECT count(DISTINCT city) FROM marts.dim_restaurants;")
        total_cities = cursor.fetchone()[0]

        cursor.execute("SELECT count(*) FROM marts.dim_restaurants;")
        total_restaurants = cursor.fetchone()[0]

        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        with kpi_c1:
            st.metric("Total Fact Orders", f"{total_orders:,}")
        with kpi_c2:
            st.metric("Total GMV", f"₹{total_gmv:,.0f}")
        with kpi_c3:
            st.metric("Active Cities", f"{total_cities:,}")
        with kpi_c4:
            st.metric("Total Restaurants", f"{total_restaurants:,}")

        st.markdown("---")

        # Top 10 Cities by GMV Chart
        cursor.execute("""
            SELECT city, sum(gmv) as gmv, sum(orders) as orders
            FROM marts.mart_daily_city_revenune
            GROUP BY city
            ORDER BY gmv DESC
            LIMIT 10;
        """)
        city_df = cursor.fetch_dataframe()
        city_df.columns = [c.lower() for c in city_df.columns]

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_city = px.bar(
                city_df,
                x="city",
                y="gmv",
                title="Top 10 Cities by Delivered Revenue (GMV)",
                labels={"gmv": "GMV (₹)", "city": "City"},
                color="gmv",
                color_continuous_scale="Oranges"
            )
            st.plotly_chart(fig_city, use_container_width=True)

        with col_g2:
            fig_orders = px.pie(
                city_df,
                names="city",
                values="orders",
                title="Order Share across Top 10 Cities",
                hole=0.4
            )
            st.plotly_chart(fig_orders, use_container_width=True)

        cursor.close()
    except Exception as e:
        st.error(f"Error fetching analytics from Redshift: {e}")
