"""Text chunking utility for brand document ingestion.

Splits extracted text into overlapping chunks suitable for embedding and
vector storage. Chunk size and overlap are configurable to balance retrieval
quality against context-size limits imposed by local inference (4GB VRAM constraint).

Every chunk preserves full metadata (business_id, document_id, template_id,
section_id, version, approval state) so that RAG retrieval can filter precisely.
"""

from __future__ import annotations

import re

from brand_os.schemas import ChunkContent


def extract_sections_from_text(text: str) -> dict[str, str]:
    """Very simple section splitter: looks for headings like '## Section Name'.

    Returns a dict of section_id -> section_text. This is a fallback; real
    ingestion may use PDF/DOCX structure or user-mapped template sections.
    """
    sections: dict[str, str] = {}
    # Match headings: "## Heading" or "# Heading" or "### Heading"
    pattern = r"^(#{1,3}\s+.+)$"
    lines = text.split("\n")
    current_heading = None
    current_text: list[str] = []

    for line in lines:
        m = re.match(pattern, line)
        if m:
            # Save previous section
            if current_heading and current_text:
                sections[current_heading] = "\n".join(current_text)
            current_heading = m.group(1).strip()
            current_text = []
        else:
            if current_heading is not None:
                current_text.append(line)

    # Last section
    if current_heading:
        sections[current_heading] = "\n".join(current_text) if current_text else current_heading

    return sections


def chunk_by_token_budget(
    text: str,
    max_chars: int = 800,
    overlap_chars: int = 150,
    model_name: str = "all-MiniLM-L6-v2",
    max_chars_per_chunk: int | None = None,
) -> list[str]:
    """Split text into chunks that respect a token budget for the given model.

    For all-MiniLM-L6-v2, ~1 token ≈ ~3 characters for typical English text.
    This is a rough approximation; real token counts require the tokenizer.
    """
    if not text or not text.strip():
        return []

    effective_max = max(1, max_chars_per_chunk or max_chars)
    effective_overlap = max(0, overlap_chars)

    if len(text) <= effective_max:
        return [text.strip()]

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + effective_max
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        # Move start forward, accounting for overlap
        start += effective_max - effective_overlap

    # Don't return empty chunks at the end
    return [c for c in chunks if c]


def enrich_chunk_with_metadata(
    chunk_text: str,
    business_id: str,
    document_id: str,
    template_id: str,
    section_id: str,
    version: str,
    chunk_id: str,
    approved: bool = False,
    missing: bool = False,
    verified: bool = False,
    source_name: str = "unknown",
) -> ChunkContent:
    """Create a ChunkContent instance with full metadata.

    The chunk_id is generated if not provided; otherwise use the given one.
    """
    import uuid as _uuid

    if not chunk_id:
        chunk_id = str(_uuid.uuid4())

    return ChunkContent(
        business_id=business_id,
        document_id=document_id,
        template_id=template_id,  # type: ignore[arg-type]  # accepted by schema as StrictStr
        section_id=section_id,
        chunk_id=chunk_id,
        version=version,
        content=chunk_text,
        approved=approved,
        missing=missing,
        verified=verified,
        source_attribution={
            "source_name": source_name,
            "source_type": "ingested",
            "chunk_id": chunk_id,
        },
    )


class MarkerDetection(dict):
    """Dict that unpacks as (missing_bool, verify_bool)."""

    def __iter__(self):
        return iter((self["missing"], self["verify"]))


def detect_missing_verify_markers(text: str) -> MarkerDetection:
    """Scan text for [MISSING] and [VERIFY] markers.

    Returns MarkerDetection indicating whether each marker was found.
    Unpacks as (has_missing: bool, has_verify: bool).
    """
    has_missing = "[MISSING]" in text
    has_verify = "[VERIFY]" in text
    return MarkerDetection({"missing": has_missing, "verify": has_verify})