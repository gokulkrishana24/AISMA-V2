"""Brand Operating System (Brand OS) + RAG engine for AISMA v2.

Provides persistent, business-scoped brand knowledge storage, 27-template
registry, document ingestion, local Sentence Transformer embeddings, ChromaDB
vector storage, and approved-only Retrieval-Augmented Generation (RAG) retrieval
with source attribution and tenant isolation.

All operations enforce business_id isolation. Draft and unverified knowledge
remains distinguishable via [MISSING] and [VERIFY] markers. Only approved
content is supplied to normal agent execution.
"""

from . import (  # noqa: F401
    attribution,
    chunking,
    embeddings,
    ingestion,
    permissions,
    rag,
    repository,
    templates,
    validation,
    vector_store,
    versioning,
)

__all__ = [
    "repository",
    "templates",
    "ingestion",
    "chunking",
    "embeddings",
    "vector_store",
    "rag",
    "versioning",
    "validation",
    "attribution",
    "permissions",
]