import requests


def persist_via_api(**context):
    """Send parsed papers to the FastAPI endpoint instead of inserting directly into DB."""
    ti = context["ti"]
    papers = ti.xcom_pull(key="parsed_papers", task_ids="parse_records")
    if not papers:
        print("⚠️ No papers found to persist.")
        return

    for paper in papers:
        try:
            resp = requests.post("http://api:8000/papers/", json=paper, timeout=10)
            if resp.status_code in (200, 201):
                print(f"✅ Inserted {paper.get('arxiv_id')}")
            else:
                print(
                    f"❌ Failed ({resp.status_code}) for {paper.get('arxiv_id')}: {resp.text}"
                )
        except Exception as e:
            print(f"❌ Error inserting {paper.get('arxiv_id')}: {e}")
