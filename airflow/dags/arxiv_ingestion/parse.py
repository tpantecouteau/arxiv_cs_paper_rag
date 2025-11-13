import xml.etree.ElementTree as ET


def parse_arxiv_data(**context) -> list[dict]:
    """Parse arXiv XML data into a list of dictionaries."""
    ti = context["ti"]
    xml_data = ti.xcom_pull(key="arxiv_xml_data", task_ids="fetch_arxiv_data")
    print(xml_data)
    if not xml_data:
        print("⚠️ No XML data found in XCom.")
        return []

    papers = []
    root = ET.fromstring(xml_data)

    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        # Namespaces dans le XML arXiv
        ns = "{http://www.w3.org/2005/Atom}"

        arxiv_id = entry.find(f"{ns}id").text.split("/")[-1]
        title = entry.find(f"{ns}title").text.strip()
        summary = entry.find(f"{ns}summary").text.strip()

        # auteurs et catégories
        authors = [
            author.find(f"{ns}name").text.strip()
            for author in entry.findall(f"{ns}author")
        ]
        categories = [cat.attrib.get("term") for cat in entry.findall(f"{ns}category")]
        published = entry.find(f"{ns}published").text

        pdf_link = None
        for link in entry.findall(f"{ns}link"):
            if "pdf" in link.attrib.get("href", ""):
                pdf_link = link.attrib.get("href")

        paper = {
            "arxiv_id": arxiv_id,
            "title": title,
            "summary": summary,
            "authors": ", ".join(authors),
            "categories": ", ".join(categories),
            "pdf_url": pdf_link,
            "published_at": published,
        }

        papers.append(paper)

    print(f"✅ Parsed {len(papers)} papers.")
    ti.xcom_push(key="parsed_papers", value=papers)

    return papers
