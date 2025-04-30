"""Utilities for splitting long texts into overlapping chunks.

Each chunk contains up to *chunk_size* words; sliding window overlap length *overlap*.

Used by enhanced_document_processor to bypass context limits.
"""
from typing import List

def chunk_document(text: str, chunk_size: int = 1500, overlap: int = 200, max_chunks: int = 5) -> List[str]:
    """Split *text* into a list of chunks with word overlap.

    Args:
        text: full document text.
        chunk_size: maximum number of words in each chunk.
        overlap: number of words from previous chunk to repeat at the start of the next chunk.
        max_chunks: stop after this many chunks to bound cost.

    Returns:
        List of chunk strings.
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words) and len(chunks) < max_chunks:
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end == len(words):
            break
        start = end - overlap  # slide with overlap
    return chunks
