from datetime import datetime, timedelta

from airflow.operators.python import (
    PythonOperator,  # pyright: ignore[reportMissingImports]
)
from arxiv_ingestion.chunk_texts import chunk_texts
from arxiv_ingestion.download_pdfs import download_pfds
from arxiv_ingestion.embed_index import embed_index_opensearch
from arxiv_ingestion.extract_texts import extract_texts
from arxiv_ingestion.fetch import fetch_arxiv_data
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
    embed_index_opensearch(**context)


@critical_task
def download_pdfs_safe(**context):
    download_pfds(**context)


@critical_task
def extract_texts_safe(**context):
    extract_texts(**context)


@critical_task
def chunk_texts_safe(**context):
    chunk_texts(**context)


@critical_task
def index_metadata_safe(**context):
    embed_index_opensearch(**context)


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
    download_task = PythonOperator(
        task_id="download_pdfs",
        python_callable=download_pdfs_safe,
        provide_context=True,
    )
    extract_task = PythonOperator(
        task_id="extract_texts",
        python_callable=extract_texts_safe,
        provide_context=True,
    )
    chunk_task = PythonOperator(task_id="chunk_texts", python_callable=chunk_texts_safe)
    index_task = PythonOperator(
        task_id="index_metadata",
        python_callable=index_metadata_safe,
        provide_context=True,
    )
    (
        fetch_task
        >> parse_task
        >> persist_task
        >> download_task
        >> extract_task
        >> chunk_task
        >> index_task
    )
