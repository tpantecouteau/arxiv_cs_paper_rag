import logging

import requests

log = logging.getLogger(__name__)

API_BASE = "http://api:8000"


def persist_via_api(**context):
    ti = context["ti"]
    papers = ti.xcom_pull(key="parsed_papers", task_ids="parse_records")
    
    if not papers:
        log.warning("No papers to persist")
        return

    for paper_id, paper in papers.items():
        paper["status"] = "pending"
        
        try:
            resp = requests.post(f"{API_BASE}/papers/", json=paper, timeout=10)
            
            if resp.status_code in (200, 201):
                log.info("Inserted %s", paper_id)
            elif resp.status_code == 400:
                log.debug("Already exists: %s", paper_id)
            else:
                log.error("Insert failed for %s: %s %s", paper_id, resp.status_code, resp.text)
                
        except requests.RequestException as e:
            log.error("Insert failed for %s: %s", paper_id, e)
