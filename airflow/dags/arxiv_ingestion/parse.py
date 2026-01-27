import logging
import xml.etree.ElementTree as ET

log = logging.getLogger(__name__)

ATOM_NS = "{http://www.w3.org/2005/Atom}"


def parse_arxiv_data(**context):
    ti = context["ti"]
    xml_data = ti.xcom_pull(key="arxiv_xml_data", task_ids="fetch_arxiv_data")
    
    if not xml_data:
        log.warning("No XML data to parse")
        return {}

    papers = {}
    root = ET.fromstring(xml_data)

    for entry in root.findall(f"{ATOM_NS}entry"):
        arxiv_id = entry.find(f"{ATOM_NS}id").text.split("/")[-1]
        
        authors = [
            a.find(f"{ATOM_NS}name").text.strip()
            for a in entry.findall(f"{ATOM_NS}author")
        ]
        categories = [
            c.attrib.get("term") for c in entry.findall(f"{ATOM_NS}category")
        ]
        
        pdf_url = None
        for link in entry.findall(f"{ATOM_NS}link"):
            href = link.attrib.get("href", "")
            if "pdf" in href:
                pdf_url = href
                break

        papers[arxiv_id] = {
            "arxiv_id": arxiv_id,
            "title": entry.find(f"{ATOM_NS}title").text.strip(),
            "summary": entry.find(f"{ATOM_NS}summary").text.strip(),
            "authors": ", ".join(authors),
            "categories": ", ".join(categories),
            "pdf_url": pdf_url,
            "published_at": entry.find(f"{ATOM_NS}published").text,
        }

    log.info("Parsed %d papers", len(papers))
    ti.xcom_push(key="parsed_papers", value=papers)
    return papers
