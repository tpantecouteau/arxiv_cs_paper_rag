from datetime import datetime, timedelta

from airflow.operators.python import (
    PythonOperator,  # pyright: ignore[reportMissingImports]
)
from arxiv_ingestion.fetch import fetch_arxiv_data
from arxiv_ingestion.index import index_metadata_llama
from arxiv_ingestion.parse import parse_arxiv_data
from arxiv_ingestion.persist_to_db import persist_via_api
from utils import critical_task

from airflow import DAG  # pyright: ignore[reportAttributeAccessIssue]

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=3),
}


@critical_task
def fetch_safe(**context):
    fetch_arxiv_data(**context)


@critical_task
def parse_safe(**context):
    parse_arxiv_data(**context)


@critical_task
def persist_safe(**context):
    persist_via_api(**context)


@critical_task
def index_safe(**context):
    index_metadata_llama(**context)


with DAG(
    dag_id="arxiv_paper_ingestion",
    default_args=default_args,
    start_date=datetime(2025, 11, 1),
    description="Fetch and index arXiv metadata into Postgres and OpenSearch",
    schedule_interval="@daily",
    catchup=False,
    tags=["arxiv", "metadata", "ingestion"],
) as dag:
    fetch_task = PythonOperator(task_id="fetch_arxiv_data", python_callable=fetch_safe)
    parse_task = PythonOperator(
        task_id="parse_records", python_callable=parse_safe, provide_context=True
    )
    persist_task = PythonOperator(
        task_id="persist_to_db", python_callable=persist_safe, provide_context=True
    )
    index_task = PythonOperator(
        task_id="index_metadata_opensearch",
        python_callable=index_safe,
        provide_context=True,
    )

    fetch_task >> parse_task >> persist_task >> index_task
