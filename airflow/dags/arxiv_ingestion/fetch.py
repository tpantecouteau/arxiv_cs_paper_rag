import os
import urllib
import urllib.request


def fetch_arxiv_data(**context) -> str:
    """Fetch data from arXiv API."""
    ARXIV_SEARCH_QUERY = os.getenv("ARXIV_SEARCH_QUERY", "all:electron")
    ARXIV_MAX_RESULTS = os.getenv("ARXIV_MAX_RESULTS", "10")
    try:
        url = f"http://export.arxiv.org/api/query?search_query={ARXIV_SEARCH_QUERY}&max_results={ARXIV_MAX_RESULTS}"
        data = urllib.request.urlopen(url)
        decoded_data = data.read().decode("utf-8")
        if len(decoded_data) == 0:
            print("⚠️ Warning: No data fetched from arXiv.")
            return ""
        print(f"✅ Fetched data from arXiv: {len(decoded_data)} characters.")
        context["ti"].xcom_push(key="arxiv_xml_data", value=decoded_data)
        return data.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching data from arXiv: {e}")
        return ""
