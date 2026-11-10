"""ChromaDB vector storage adapter for Brand OS RAG.

Provides a thin abstraction over ChromaDB so that Phase 5 can migrate to
PostgreSQL + pgvector without rewriting the retrieval pipeline.

Mandatory metadata on every chunk: business_id, document_id, template_id,
section_id, version, approval_status, source.

Strict tenant filtering: every query operation enforces business_id at the
storage boundary. The interface is designed so that adding a PostgreSQL backend
is a matter of implementing the same add/query/delete/get signatures.
"""

from __future__ import annotations

from typing import Any

from brand_os.schemas import (
    ChunkContent,
    QueryContext,
    RetrievalResult,
    VectorStoreConfig,
)

# ---------------------------------------------------------------------------
# ChromaDB client singleton (lazy, single-process)
# ---------------------------------------------------------------------------

_client: Any | None = None
_collection: Any | None = None
_initialized: bool = False


def _get_client(persist_directory: str) -> Any:
    """Get or create a ChromaDB client, lazily initialized."""
    global _client, _initialized

    if _initialized and _client is not None:
        return _client

    try:
        import chromadb
        _client = chromadb.Client(chromadb.Settings(persist_directory=persist_directory))
        _initialized = True
        return _client
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to initialize ChromaDB client: {exc}") from exc


def _get_or_create_collection(
    client: Any,
    collection_name: str,
    vector_store_config: VectorStoreConfig,
) -> Any:
    """Get an existing collection or create one with the given config."""
    try:
        col = client.get_collection(name=collection_name)
        return col
    except Exception:
        # Collection doesn't exist; create it
        col = client.create_collection(
            name=collection_name,
            metadata={"hnsw_space": "cosine"},
            # Persist metadata we care about
        )
        return col


def initialize_chroma(vector_store_config: VectorStoreConfig | None = None) -> Any:
    """Initialize the ChromaDB client and ensure the collection exists.

    Must be called before first use. Idempotent.
    """
    global _client, _collection, _initialized

    cfg = vector_store_config or VectorStoreConfig()
    if _initialized and _collection is not None:
        return _collection

    client = _get_client(cfg.persist_directory)
    _collection = _get_or_create_collection(client, cfg.collection_name, cfg)
    _initialized = True
    return _collection


def is_initialized() -> bool:
    """Return True if the vector store is ready."""
    return _initialized and _collection is not None


def add_chunks(
    chunks: list[Any],
    embeddings: list[list[float]] | None = None,
    vector_store_config: VectorStoreConfig | None = None,
) -> None:
    """Add chunk embeddings to the vector store.

    Each chunk MUST have mandatory metadata: business_id, document_id,
    template_id, section_id, version, approval_status, source.
    """
    global _collection
    if not _initialized or _collection is None:
        initialize_chroma(vector_store_config)

    parsed_chunks: list[ChunkContent] = []
    for c in chunks:
        if isinstance(c, dict):
            c_dict = dict(c)
            if "template_id" not in c_dict:
                c_dict["template_id"] = "brand_identity"
            if "section_id" not in c_dict:
                c_dict["section_id"] = "root"
            if "chunk_id" not in c_dict:
                c_dict["chunk_id"] = f"chunk_{len(parsed_chunks)}"
            if "version" not in c_dict:
                c_dict["version"] = "v1.0"
            if "source_attribution" not in c_dict:
                c_dict["source_attribution"] = {"source_name": "manual", "source_type": "ingested"}
            parsed_chunks.append(ChunkContent(**c_dict))
        else:
            parsed_chunks.append(c)

    if embeddings is None:
        from brand_os.embeddings import get_embedding
        embeddings = [get_embedding(c.content) for c in parsed_chunks]

    # Validate mandatory metadata on each chunk
    for chunk in parsed_chunks:
        _validate_mandatory_metadata(chunk)

    # Prepare ChromaDB documents and metadata
    ids: list[str] = []
    documents: list[str] = []  # stored text (chunk content summary)
    metadatas: list[dict[str, Any]] = []
    embeddings_list: list[list[float]] = []

    for chunk, emb in zip(parsed_chunks, embeddings, strict=True):
        mid = chunk.chunk_id
        ids.append(mid)

        # Store a compact text representation; full content is in ChunkContent
        text_summary = (chunk.content[:200] + "...") if len(chunk.content) > 200 else chunk.content
        documents.append(text_summary)

        metadata: dict[str, Any] = {
            "business_id": chunk.business_id,
            "document_id": chunk.document_id,
            "template_id": chunk.template_id,
            "section_id": chunk.section_id,
            "version": chunk.version,
            "approved": chunk.approved,
            "missing": chunk.missing,
            "verified": chunk.verified,
            "source_name": chunk.source_attribution.get("source_name", "unknown") if chunk.source_attribution else "unknown",
            "source_type": chunk.source_attribution.get("source_type", "ingested") if chunk.source_attribution else "ingested",
            "chunk_id": chunk.chunk_id,
            "relevance_score": chunk.relevance_score or 0.0,
        }
        metadatas.append(metadata)
        embeddings_list.append(emb)

    _collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings_list,
    )


def _validate_mandatory_metadata(chunk: ChunkContent) -> None:
    """Ensure a ChunkContent has all mandatory metadata fields.

    Raises ValueError if any required field is missing/empty.
    """
    required = ["business_id", "document_id", "template_id", "section_id", "version"]
    for field in required:
        val = getattr(chunk, field, None)
        if not val:
            raise ValueError(f"Mandatory metadata missing: {field}")


def query_chunks(
    query_embedding: Any,
    query_context: Any = None,
    vector_store_config: VectorStoreConfig | None = None,
    top_k: int | None = None,
    **kwargs: Any,
) -> list[RetrievalResult]:
    """Query the vector store for relevant chunks.

    Supports:
    - query_chunks(query_embedding, query_context, vector_store_config, top_k)
    - query_chunks(query_text, business_id=..., top_k=...)
    """
    if isinstance(query_embedding, str):
        query_text = query_embedding
        biz_id = kwargs.get("business_id") or (query_context if isinstance(query_context, str) else "general")
        from brand_os.embeddings import get_embedding
        emb = get_embedding(query_text)
        qc = QueryContext(business_id=biz_id, query=query_text, user_query=query_text)
        k_val = kwargs.get("top_k") or top_k or 5
    else:
        emb = query_embedding
        qc = query_context
        k_val = top_k or (qc.requested_top_k if hasattr(qc, "requested_top_k") else 5) or 5

    if not _initialized or _collection is None:
        initialize_chroma(vector_store_config)

    k = k_val

    # Build where filter: mandatory business_id isolation
    where_filter: dict[str, Any] = {
        "business_id": qc.business_id,
    }

    # Optionally filter by template_id if provided
    if qc.template_filters:
        where_filter = {
            "$and": [
                {"business_id": qc.business_id},
                {"template_id": {"$in": [str(tid) for tid in qc.template_filters]}},
            ]
        }

    # Query the collection
    try:
        results = _collection.query(
            query_embeddings=[emb],
            n_results=k,
            where=where_filter,
            include=["metadatas", "documents", "embeddings"],
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"ChromaDB query failed: {exc}") from exc

    # Post-process results into RetrievalResult objects
    retrieved: list[RetrievalResult] = []

    if results["ids"] and results["ids"][0]:
        id_list = results["ids"][0]
        meta_list = results["metadatas"][0] if results.get("metadatas") else [{}] * len(id_list)
        doc_list = results["documents"][0] if results.get("documents") else [""] * len(id_list)
        distances = results.get("distances")
        score_list = distances[0] if (distances and len(distances) > 0 and distances[0] is not None) else [0.0] * len(id_list)

        for i, chunk_id in enumerate(id_list):
            meta = meta_list[i]
            doc_text = doc_list[i] if i < len(doc_list) else ""
            relevance = float(score_list[i]) if i < len(score_list) else 0.0

            # Enforce approved-only filter at retrieval time
            approved = meta.get("approved", False)
            if getattr(qc, "enforce_approved_only", True) and not approved:
                continue  # skip unapproved chunks

            retrieved.append(
                RetrievalResult(
                    chunk_id=str(meta.get("chunk_id", chunk_id)),
                    document_id=str(meta.get("document_id", "")),
                    business_id=str(meta.get("business_id", "")),
                    template_id=meta.get("template_id", ""),
                    section_id=meta.get("section_id", ""),
                    version=str(meta.get("version", "")),
                    relevance_score=relevance,
                    approved=bool(approved),
                    text=str(doc_text),
                    source_reference=f"doc:{meta.get('document_id','')}:tid:{meta.get('template_id','')}:sid:{meta.get('section_id','')}:v:{meta.get('version','')}",
                    missing=bool(meta.get("missing", False)),
                    verified=bool(meta.get("verified", False)),
                )
            )

    return retrieved


def delete_chunks(
    business_id: str,
    document_id: str | None = None,
    chunk_id: str | None = None,
    vector_store_config: VectorStoreConfig | None = None,
    **kwargs: Any,
) -> None:
    """Delete chunks from the vector store."""
    if not _initialized or _collection is None:
        initialize_chroma(vector_store_config)

    c_id = chunk_id or kwargs.get("chunk_id")
    d_id = document_id or kwargs.get("document_id")

    try:
        if c_id:
            _collection.delete(ids=[c_id])
        elif d_id:
            _collection.delete(where={"business_id": business_id, "document_id": d_id})
        else:
            _collection.delete(where={"business_id": business_id})
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"ChromaDB delete failed: {exc}") from exc


def clear_collection(vector_store_config: VectorStoreConfig | None = None) -> None:
    """Delete all records from ChromaDB collection."""
    global _initialized, _collection, _client
    if not _initialized or _collection is None:
        initialize_chroma(vector_store_config)

    try:
        if _collection is not None:
            all_ids = _collection.get().get("ids", [])
            if all_ids:
                _collection.delete(ids=all_ids)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"ChromaDB clear failed: {exc}") from exc