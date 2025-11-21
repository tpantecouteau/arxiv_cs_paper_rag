import asyncio
import csv
import logging
from datetime import datetime, timedelta
import nest_asyncio
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from llama_index.core.evaluation import (
    generate_question_context_pairs,
    FaithfulnessEvaluator,
    RelevancyEvaluator,
    RetrieverEvaluator,
)
from llama_index.core import VectorStoreIndex, PromptTemplate
from src.dependencies import get_index, get_llm
from src.config import settings
from llama_index.llms.ollama import Ollama

# Apply nest_asyncio to allow nested event loops (needed for LlamaIndex in Airflow)
nest_asyncio.apply()

logger = logging.getLogger(__name__)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def run_rag_evaluation(**context):
    """
    Orchestrates the RAG evaluation process:
    1. Generates a dataset of questions/contexts from existing documents.
    2. Evaluates Retrieval (Hit Rate, MRR).
    3. Evaluates Response (Faithfulness, Relevancy).
    4. Saves results to a CSV report.
    """
    logger.info("Starting RAG evaluation...")
    
    # Initialize components
    # FORCE llama3.2:1b to avoid OOM if env var is stale
    llm = Ollama(
        model="llama3.2:1b",
        base_url=settings.OLLAMA_HOST,
        request_timeout=settings.OLLAMA_TIMEOUT,
        temperature=settings.OLLAMA_TEMPERATURE,
    )
    index = get_index()
    
    # 1. Dataset Generation
    # Retrieve a sample of nodes to generate questions from
    retriever = index.as_retriever(similarity_top_k=10)
    nodes = retriever.retrieve("machine learning deep learning artificial intelligence")
    
    logger.info(f"Retrieved {len(nodes)} documents for dataset generation.")
    
    # Define strict prompt for question generation
    qa_template = PromptTemplate(
        "Context information is below.\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Given the context information and not prior knowledge, "
        "generate {num_questions_per_chunk} questions based on the context.\n"
        "The questions should be precise and answerable.\n" 
        "CRITICAL: Output ONLY the questions, one per line. Do NOT include any introductory text like 'Here is a question'.\n"
        "Questions:"
    )

    # Generate Question-Context Pairs
    qa_dataset = generate_question_context_pairs(
        nodes,
        llm=llm,
        num_questions_per_chunk=1,  # Keep it small for now to avoid OOM/timeouts
        qa_generate_prompt_tmpl=qa_template
    )
    logger.info(f"Generated {len(qa_dataset.queries)} questions.")
    
    # 2. Retrieval Evaluation
    logger.info("Running Retrieval Evaluation (Hit Rate, MRR)...")
    retriever_evaluator = RetrieverEvaluator.from_metric_names(
        ["mrr", "hit_rate"], retriever=retriever
    )
    
    # Evaluate retrieval asynchronously
    # We need to run this in a way compatible with Airflow's loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    retrieval_results = loop.run_until_complete(retriever_evaluator.aevaluate_dataset(qa_dataset))
    
    # Process Retrieval Results
    retrieval_metrics = []
    for res in retrieval_results:
        retrieval_metrics.append(res.metric_vals_dict)
    
    retrieval_df = pd.DataFrame(retrieval_metrics)
    avg_hit_rate = retrieval_df["hit_rate"].mean() if not retrieval_df.empty else 0.0
    avg_mrr = retrieval_df["mrr"].mean() if not retrieval_df.empty else 0.0
    
    logger.info(f"Retrieval Evaluation Complete. Avg Hit Rate: {avg_hit_rate}, Avg MRR: {avg_mrr}")

    # 3. Response Evaluation (Faithfulness & Relevancy)
    logger.info("Running Response Evaluation (Faithfulness, Relevancy)...")
    
    faithfulness_evaluator = FaithfulnessEvaluator(llm=llm)
    relevancy_evaluator = RelevancyEvaluator(llm=llm)
    query_engine = index.as_query_engine(llm=llm)
    
    results_data = []
    
    for query_id, query in qa_dataset.queries.items():
        logger.info(f"Evaluating query: {query}")
        
        # Generate Response
        response = query_engine.query(query)
        
        # Evaluate Faithfulness
        faith_result = faithfulness_evaluator.evaluate_response(response=response)
        
        # Evaluate Relevancy
        rel_result = relevancy_evaluator.evaluate_response(
            query=query, response=response
        )
        
        results_data.append({
            "query": query,
            "response": str(response),
            "faithfulness_score": faith_result.score,
            "faithfulness_reason": faith_result.feedback,
            "relevancy_score": rel_result.score,
            "relevancy_reason": rel_result.feedback,
            "source_nodes": [n.node.get_content()[:200] + "..." for n in response.source_nodes],
            "global_hit_rate": avg_hit_rate,
            "global_mrr": avg_mrr
        })

    # 4. Save Report
    df = pd.DataFrame(results_data)
    output_path = "src/rag_eval_report.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Evaluation report saved to {output_path}")

with DAG(
    dag_id="rag_evaluation_dag",
    default_args=default_args,
    description="Evaluate RAG system using LLM as Judge",
    schedule_interval=None, # Trigger manually
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["rag", "evaluation"],
) as dag:

    evaluation_task = PythonOperator(
        task_id="run_rag_evaluation",
        python_callable=run_rag_evaluation,
    )