import pytest
from unittest.mock import MagicMock, patch


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

    header_span = {"text": "Introduction", "size": 12.0}
    body_span = {"text": "This is body text.", "size": 10.0}
    body_span_2 = {"text": "More body text.", "size": 10.0}

    block1 = {
        "type": 0,
        "bbox": (0, 0, 100, 20),
        "lines": [{"spans": [header_span]}],
    }
    block2 = {
        "type": 0,
        "bbox": (0, 30, 100, 100),
        "lines": [{"spans": [body_span]}],
    }
    block3 = {
        "type": 0,
        "bbox": (0, 110, 100, 150),
        "lines": [{"spans": [body_span_2]}],
    }

    mock_page.get_text.return_value = {"blocks": [block1, block2, block3]}
    mock_page.rect.width = 600
    mock_doc.__iter__.return_value = [mock_page]
    mock_fitz_open.return_value = mock_doc

    with (
        patch("pathlib.Path.glob") as mock_glob,
        patch("pathlib.Path.mkdir"),
        patch("pathlib.Path.write_text") as mock_write,
        patch("pathlib.Path.exists") as mock_exists,
    ):
        mock_exists.return_value = False
        mock_pdf = MagicMock()
        mock_pdf.stem = "paper1"
        mock_glob.return_value = [mock_pdf]

        extract_texts()

        content = mock_write.call_args[0][0]
        assert "## Introduction" in content
        assert "This is body text." in content
