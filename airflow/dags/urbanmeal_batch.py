import os
from datetime import datetime
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.bash import BashOperator      # Airflow 3 import

DBT = "/opt/airflow/dbt_venv/bin/dbt"
DBT_PROJECT = "/opt/airflow/dbt/urbanmeal"

S3_BUCKET = os.getenv("S3_BUCKET", "urbanmeal")
S3_PREFIX = os.getenv("S3_PREFIX", "RAW")
ROLE_ARN = os.getenv("REDSHIFT_ROLE_ARN", "arn:aws:iam::<your-aws-account-id>:role/redshift-urbanmeal-role")

COPY_RAW = [
    f'COPY "raw".restaurants FROM \'s3://{S3_BUCKET}/{S3_PREFIX}/restaurant.csv\' IAM_ROLE \'{ROLE_ARN}\' FORMAT AS CSV IGNOREHEADER 1 ACCEPTINVCHARS BLANKSASNULL EMPTYASNULL MAXERROR 500;',
    f'COPY "raw".users       FROM \'s3://{S3_BUCKET}/{S3_PREFIX}/users.csv\'       IAM_ROLE \'{ROLE_ARN}\' FORMAT AS CSV IGNOREHEADER 1 ACCEPTINVCHARS BLANKSASNULL EMPTYASNULL MAXERROR 500;',
    f'COPY "raw".food        FROM \'s3://{S3_BUCKET}/{S3_PREFIX}/food.csv\'        IAM_ROLE \'{ROLE_ARN}\' FORMAT AS CSV IGNOREHEADER 1 ACCEPTINVCHARS BLANKSASNULL EMPTYASNULL MAXERROR 500;',
    f'COPY "raw".menu        FROM \'s3://{S3_BUCKET}/{S3_PREFIX}/menu (1).csv\'    IAM_ROLE \'{ROLE_ARN}\' FORMAT AS CSV IGNOREHEADER 1 ACCEPTINVCHARS BLANKSASNULL EMPTYASNULL MAXERROR 500;',
    f'COPY "raw".orders      FROM \'s3://{S3_BUCKET}/{S3_PREFIX}/orders.csv\'      IAM_ROLE \'{ROLE_ARN}\' FORMAT AS CSV IGNOREHEADER 1 TIMEFORMAT \'auto\' DATEFORMAT \'auto\';',
    f'COPY "raw".order_items FROM \'s3://{S3_BUCKET}/{S3_PREFIX}/order_items.csv\' IAM_ROLE \'{ROLE_ARN}\' FORMAT AS CSV IGNOREHEADER 1;',
    f'COPY "raw".reviews     FROM \'s3://{S3_BUCKET}/{S3_PREFIX}/reviews.csv\'     IAM_ROLE \'{ROLE_ARN}\' FORMAT AS CSV IGNOREHEADER 1 DATEFORMAT \'auto\' ACCEPTINVCHARS;',
]

with DAG(
    dag_id="urbanmeal_batch",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["urbanmeal", "dbt", "redshift"],
    doc_md=__doc__,
) as dag:

    reload_raw = SQLExecuteQueryOperator(
        task_id="reload_raw",
        conn_id="redshift_default",
        sql=COPY_RAW,
        split_statements=True,
        autocommit=True,
    )

    dbt_build_core = BashOperator(
        task_id="dbt_build_core",
        bash_command=f"{DBT} build --exclude tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}",
    )

    enrich_reviews = BashOperator(
        task_id="enrich_reviews",
        bash_command="python /opt/airflow/ai/enrich_reviews.py",
    )

    dbt_build_ai = BashOperator(
        task_id="dbt_build_ai",
        bash_command=f"{DBT} build --select tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}",
    )

    reload_raw >> dbt_build_core >> enrich_reviews >> dbt_build_ai