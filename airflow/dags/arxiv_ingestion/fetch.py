import logging
import os
import urllib.request

log = logging.getLogger(__name__)

ARXIV_API = "http://export.arxiv.org/api/query"


def fetch_arxiv_data(**context):
    search_query = os.getenv("ARXIV_SEARCH_QUERY", "all:electron")
    max_results = os.getenv("ARXIV_MAX_RESULTS", "10")
    
    url = f"{ARXIV_API}?search_query={search_query}&max_results={max_results}"
    
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read().decode("utf-8")
        
        if not data:
            log.warning("Empty response from arXiv")
            return ""
        
        log.info("Fetched %d bytes from arXiv", len(data))
        context["ti"].xcom_push(key="arxiv_xml_data", value=data)
        return data
        
    except Exception as e:
        log.error("arXiv fetch failed: %s", e)
        return ""
