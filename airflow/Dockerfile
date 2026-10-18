# Airflow 3.x image + Amazon/Redshift provider + FAB auth (for admin/admin login) + dbt venv + openai + redshift-connector.
FROM apache/airflow:3.0.3

# Providers: amazon (Redshift/S3), common-sql, fab (classic username/password login), openai, redshift-connector
RUN pip install --no-cache-dir \
      apache-airflow-providers-amazon \
      apache-airflow-providers-common-sql \
      apache-airflow-providers-fab \
      redshift-connector \
      openai

# dbt in its own venv so it never clashes with Airflow's deps. DAG calls /opt/airflow/dbt_venv/bin/dbt
RUN python -m venv /opt/airflow/dbt_venv && \
    /opt/airflow/dbt_venv/bin/pip install --no-cache-dir "dbt-redshift==1.8.*"
