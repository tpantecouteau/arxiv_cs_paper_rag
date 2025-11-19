import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import fitz

@pytest.fixture
def mock_context():
    ti = MagicMock()
    ti.xcom_pull.return_value = {"paper1": {"title": "Test Paper"}}
    return {"ti": ti}

@patch("fitz.open")
def test_extract_texts_headers(mock_fitz_open):
    from airflow.dags.arxiv_ingestion.extract_texts import extract_texts
    
    mock_doc = MagicMock()
    mock_page = MagicMock()
    
    # Mock blocks with "dict" output for font size
    # Structure: {"blocks": [{"type": 0, "bbox": [...], "lines": [{"spans": [{"text": "...", "size": ...}]}]}]}
    
    body_span = {"text": "This is body text.", "size": 10.0}
    header_span = {"text": "Introduction", "size": 12.0}
    
    # Block 1: Header
    block1 = {
        "type": 0,
        "bbox": (0, 0, 100, 20),
        "lines": [{"spans": [header_span]}]
    }
    
    # Block 2: Body
    block2 = {
        "type": 0,
        "bbox": (0, 30, 100, 100),
        "lines": [{"spans": [body_span]}]
    }
    
    # Ensure get_text("dict") returns the structure
    mock_page.get_text.return_value = {"blocks": [block1, block2]}
    mock_page.rect.width = 600
    
    # The code iterates over the doc twice.
    # We need to ensure that iterating over mock_doc yields mock_page each time.
    # The standard MagicMock.__iter__ yields the return_value if it's an iterable, or creates one.
    # If we set return_value to a list, it yields from that list.
    # But if we iterate twice, we need it to be reusable.
    # A list is reusable.
    mock_doc.__iter__.return_value = [mock_page]
    
    # However, in the previous attempt, I used side_effect which returns a NEW iterator each time.
    # That should have worked.
    # Let's check why it might fail.
    # Maybe the code calls `page.get_text("dict")` which returns the SAME dict object.
    # That should be fine.
    
    # Let's verify the logic in extract_texts.py:
    # common_size = Counter(font_sizes).most_common(1)[0][0]
    # font_sizes = [12.0, 10.0] -> most common is 12.0 (if tie, picks first?)
    # Wait, Counter most_common with tie?
    # If 12.0 appears once and 10.0 appears once, order is arbitrary or insertion order.
    # If 12.0 is picked as common size, then 12.0 * 1.1 = 13.2.
    # Then 12.0 is NOT > 13.2, so it's NOT a header.
    
    # Ah! I need body text to be MORE FREQUENT.
    
    body_span_2 = {"text": "More body text.", "size": 10.0}
    block3 = {
        "type": 0,
        "bbox": (0, 110, 100, 150),
        "lines": [{"spans": [body_span_2]}]
    }
    
    mock_page.get_text.return_value = {"blocks": [block1, block2, block3]}
    
    mock_fitz_open.return_value = mock_doc
    
    with patch("pathlib.Path.glob") as mock_glob, \
         patch("pathlib.Path.mkdir"), \
         patch("pathlib.Path.write_text") as mock_write, \
         patch("pathlib.Path.exists") as mock_exists:
        
        mock_exists.return_value = False
        mock_pdf = MagicMock()
        mock_pdf.stem = "paper1"
        mock_glob.return_value = [mock_pdf]
        
        extract_texts()
        
        args, _ = mock_write.call_args
        content = args[0]
        
        assert "## Introduction" in content
        assert "This is body text." in content
