import sys
import os
import logging

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from airflow.dags.evaluation.evaluate import run_rag_evaluation

# Configure logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("Running evaluation test...")
    try:
        run_rag_evaluation()
        print("Evaluation completed successfully.")
    except Exception as e:
        print(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
