# UrbanMeal AI Data Engineering — End-to-End Project

## 📖 Project Overview
This project presents a complete batch data pipeline that processes UrbanMeal-style food delivery data from raw CSV files into an AI-powered analytics platform. 

The dataset lands in an Amazon S3 data lake and flows into Snowflake via a secure storage integration. From there, `dbt` transforms the data through a Medallion Architecture (Bronze, Silver, Gold). Apache Airflow orchestrates the entire pipeline through a daily DAG. Finally, an AI layer powered by OpenAI enriches the data, provides a RAG-based chat interface for customer reviews, and enables text-to-SQL capabilities.

### 🌟 Key Features
- **Automated Data Pipeline**: Orchestrated by Apache Airflow via Docker.
- **Medallion Architecture**: RAW (Bronze), STAGING (Silver), and MARTS (Gold) implemented using `dbt`.
- **AI-Enrichment**: Analyzes free-text reviews for sentiment and topic using OpenAI's LLMs.
- **Interactive Apps**: Built with Streamlit for RAG (Chat with Reviews) and Text-to-SQL (Chat with Data).
- **Secure Integration**: Keyless S3 to Snowflake handshake using AWS IAM roles.

---

## 🏗️ Architecture & Tech Stack
**Flow:** UrbanMeal Dataset → Amazon S3 → Snowflake → dbt → Airflow → AI (OpenAI/Streamlit)

![Architecture](docs/architecture.png)

- **Storage & Processing:** Amazon S3, Snowflake
- **Transformation:** dbt (dbt-snowflake)
- **Orchestration:** Apache Airflow 3 (Docker)
- **AI & Frontend:** Python, Pandas, OpenAI (`gpt-4o-mini`, `text-embedding-3-small`), Streamlit

---

## 📂 Dataset
> [Download the CSV files here](https://drive.google.com/drive/folders/1FEnGWMHhHzzTUCZOw1-YnH2v3DMuM-rs?usp=sharing) and place them under the `data/` directory. (Note: These files are too large to commit to the repository).

The dataset includes:
- **Dimensions (CSVs):** Restaurants, Users, Food, Menu.
- **Facts:** ~10M orders, ~23M order items, ~300K free-text reviews.

---

## 📁 Repository Structure
```text
├── airflow/                  # Airflow 3 on Docker (Snowflake + OpenAI providers)
│   ├── docker-compose.yaml   # Postgres + API + Scheduler
│   ├── example.env           # Template for SNOWFLAKE_* / OPENAI_API_KEY
│   └── dags/urbanmeal_batch.py  # Pipeline DAG
├── urbanmeal/                # dbt project (Medallion models & macros)
├── ai/                       # AI Layer (Enrichment, RAG Chat, Text-to-SQL)
├── snowflake/                # Snowflake SQL Setup (Warehouse, Integration, DDL)
├── aws/iam/                  # IAM Policies and Role Trust documents
└── docs/architecture.png     # Architecture diagram
```

---

## 🚀 Setup & Running Instructions

### Prerequisites
- Docker & Docker Compose
- AWS Account (S3 & IAM access)
- Snowflake Account
- OpenAI API Key

### Step 1: Data Storage (AWS S3)
1. Create an S3 Bucket.
2. Upload the downloaded dataset CSVs into your bucket under the path: `s3://<YOUR_BUCKET>/raw/<table>/` (e.g., `raw/restaurants/`, `raw/users/`).

### Step 2: Snowflake Setup
Run the SQL scripts located in the `snowflake/` directory sequentially within Snowflake (Snowsight):
1. Execute `01_setup.sql` to create the warehouse, database, and schemas.
2. Follow `02_storage_integration.sql` alongside the JSON policies in `aws/iam/` to create a keyless S3 storage integration.
3. Execute `03_stage_and_formats.sql`, `04_raw_tables.sql`, and `05_copy_into.sql` to load the data into the RAW (Bronze) layer.

### Step 3: Transformation (dbt)
1. Navigate to the dbt project:
   ```bash
   cd urbanmeal
   ```
2. Export your Snowflake credentials as environment variables:
   ```bash
   export SNOWFLAKE_ACCOUNT=<your-account>
   export SNOWFLAKE_USER=<your-username>
   export SNOWFLAKE_PASSWORD=<your-password>
   ```
3. Verify the connection and build the models:
   ```bash
   dbt debug
   dbt build --exclude tag:ai
   ```

### Step 4: Orchestration (Apache Airflow)
1. Navigate to the Airflow directory:
   ```bash
   cd airflow
   ```
2. Set up the environment variables:
   ```bash
   cp example.env .env
   # Edit .env and fill in SNOWFLAKE_*, OPENAI_API_KEY, and SAMPLE_N
   ```
3. Start the Airflow cluster:
   ```bash
   docker compose build
   docker compose up -d
   ```
4. Access the Airflow UI at `http://localhost:8080`, unpause the `urbanmeal_batch` DAG, and trigger it.

### Step 5: Run the AI Apps (Streamlit)
To interact with the data using AI, export your OpenAI API key and run the Streamlit apps:
```bash
export OPENAI_API_KEY=sk-...

# To run batch review enrichment:
python ai/enrich_reviews.py

# To chat with your reviews via RAG:
streamlit run ai/rag_chat.py

# To query the warehouse using natural language:
streamlit run ai/text_to_sql.py
```
