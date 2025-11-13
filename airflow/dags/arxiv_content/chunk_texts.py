import json
from pathlib import Path

from llama_index.core.node_parser import TokenTextSplitter


def chunk_texts(**context):
    """
    Split extracted text files into semantic chunks using LlamaIndex Recursive Splitter.
    """
    extracted_dir = Path("/opt/airflow/data/texts")
    chunks_dir = Path("/opt/airflow/data/chunks")
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # Recursive splitter : gère automatiquement paragraphes / phrases / espaces
    splitter = TokenTextSplitter(
        chunk_size=800,  # nombre de tokens par chunk
        chunk_overlap=100,  # overlap pour garder le contexte
        separator="\n\n",  # commence par couper aux paragraphes
        backup_separators=["\n", ".", " "],  # fallback multi-niveau
        tokenizer=None,  # LlamaIndex gère ça automatiquement
    )

    for txt_file in extracted_dir.glob("*.txt"):
        text = txt_file.read_text(encoding="utf-8")
        if not text.strip():
            print(f"⚠️ Empty text file: {txt_file.name}")
            continue

        chunks = splitter.split_text(text)

        json_path = chunks_dir / f"{txt_file.stem}.json"
        json_path.write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        print(f"🦙 {len(chunks)} recursive chunks created for {txt_file.stem}")
