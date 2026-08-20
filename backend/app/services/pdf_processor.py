"""Extracts text from an uploaded PDF and splits it into overlapping chunks
suitable for retrieval. Swap this out for a smarter chunker (headings-aware,
token-based) later if quality needs improving."""
from typing import List, Tuple
from pypdf import PdfReader


def extract_pages(file_path: str) -> List[Tuple[int, str]]:
    """Returns list of (page_number, page_text)."""
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append((i + 1, text))
    return pages


def chunk_text(pages: List[Tuple[int, str]], chunk_size: int = 900, overlap: int = 150):
    """Simple sliding-window chunker over each page's text.
    Returns list of dicts: {text, page, order_index}
    """
    chunks = []
    order_index = 0
    for page_num, text in pages:
        start = 0
        while start < len(text):
            end = start + chunk_size
            piece = text[start:end].strip()
            if piece:
                chunks.append({"text": piece, "page": page_num, "order_index": order_index})
                order_index += 1
            start += chunk_size - overlap
    return chunks
