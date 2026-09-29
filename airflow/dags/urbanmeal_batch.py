from datetime import datetime
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.bash import BashOperator      # Airflow 3 import

DBT = "/opt/airflow/dbt_venv/bin/dbt"
DBT_PROJECT = "/opt/airflow/dbt/urbanmeal"

COPY_RAW = [
    "USE WAREHOUSE URBANMEAL_WH",
    "COPY INTO URBANMEAL.RAW.restaurants FROM @URBANMEAL.RAW.URBANMEAL_RAW_STAGE/restaurants/  ON_ERROR='CONTINUE'",
    "COPY INTO URBANMEAL.RAW.users       FROM @URBANMEAL.RAW.URBANMEAL_RAW_STAGE/users/        ON_ERROR='CONTINUE'",
    "COPY INTO URBANMEAL.RAW.food        FROM @URBANMEAL.RAW.URBANMEAL_RAW_STAGE/food/         ON_ERROR='CONTINUE'",
    "COPY INTO URBANMEAL.RAW.menu        FROM @URBANMEAL.RAW.URBANMEAL_RAW_STAGE/menu/         ON_ERROR='CONTINUE'",
    "COPY INTO URBANMEAL.RAW.orders      FROM @URBANMEAL.RAW.URBANMEAL_RAW_STAGE/orders/",
    "COPY INTO URBANMEAL.RAW.order_items FROM @URBANMEAL.RAW.URBANMEAL_RAW_STAGE/order_items/",
    "COPY INTO URBANMEAL.RAW.reviews     FROM @URBANMEAL.RAW.URBANMEAL_RAW_STAGE/reviews/",
]

with DAG(
    dag_id="urbanmeal_batch",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["urbanmeal", "dbt", "snowflake"],
    doc_md=__doc__,
) as dag:

    reload_raw = SQLExecuteQueryOperator(
        task_id="reload_raw", conn_id="snowflake_default",
        sql=COPY_RAW, split_statements=True, autocommit=True,
    )

    dbt_build_core = BashOperator(
        task_id="dbt_build_core",
        bash_command=f"{DBT} build --exclude tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}",
    )

    enrich_reviews = BashOperator(
        task_id="enrich_reviews",
        bash_command=f"python /opt/airflow/ai/enrich_reviews.py",
    )

    dbt_build_ai = BashOperator(
        task_id = "dbt_build_ai",
        bash_command=f"{DBT} build --select tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}"
    )

    reload_raw >> dbt_build_core >> enrich_reviews >> dbt_build_ai