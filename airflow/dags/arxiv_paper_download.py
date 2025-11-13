from datetime import datetime, timedelta

from airflow.models import DagRun, TaskInstance
from airflow.operators.python import PythonOperator
from arxiv_content.chunk_texts import chunk_texts
from arxiv_content.download_pdfs import download_pfds
from arxiv_content.extract_texts import extract_texts
from arxiv_content.index import index_opensearch
from utils import critical_task, safe_task

from airflow import DAG

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
}


@critical_task
def download_safe(**context):
    download_pfds(**context)


@critical_task
def extract_safe(**context):
    extract_texts(**context)


@safe_task
def chunk_safe(**context):
    chunk_texts(**context)


@critical_task
def index_safe(**context):
    index_opensearch(**context)


with DAG(
    dag_id="arxiv_paper_fulltext",
    start_date=datetime(2025, 11, 1),
    default_args=default_args,
    description="Download and index full arXiv paper content",
    schedule_interval="@daily",
    catchup=False,
    tags=["arxiv", "rag", "pdf"],
) as dag:
    download_task = PythonOperator(
        task_id="download_pdfs", python_callable=download_safe
    )
    extract_task = PythonOperator(task_id="extract_texts", python_callable=extract_safe)
    chunk_task = PythonOperator(task_id="chunk_texts", python_callable=chunk_safe)
    index_task = PythonOperator(
        task_id="index_paper_chunks", python_callable=index_safe
    )
    download_task >> extract_task >> chunk_task >> index_task
