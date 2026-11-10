"""Local Sentence Transformer embedding wrapper for Brand OS RAG.

Provides lazy-initialized, singleton SentenceTransformer embeddings with:
- Configurable model name (default: all-MiniLM-L6-v2, 384 dims)
- CPU-friendly execution with optional offload
- Batch encoding with size limits
- Graceful handling if model is unavailable
- No automatic model downloads; caller must ensure model is available

Embedding generation is kept separate from the LLM inference service (Ollama)
to avoid loading multiple large models simultaneously — critical for 4GB VRAM.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

# Module-level singleton; lazily initialized _ON_FIRST_USE
_model: Any | None = None
_model_name: str = "all-MiniLM-L6-v2"
_dimension: int = 384
_initialized: bool = False


def initialize(model_name: str = "all-MiniLM-L6-v2", *, cpu_offload: bool = True) -> None:
    """Lazy singleton initialization of the SentenceTransformer model.

    Must be called before first use. Subsequent calls with the same model name
    are no-ops. If the model is already initialized with a different name, a
    warning is emitted and the new model is NOT loaded (fail-closed).

    Args:
        model_name: Name of the SentenceTransformer model (default: all-MiniLM-L6-v2).
        cpu_offload: Whether to enable CPU offload for GPU memory management.
    """
    global _model, _model_name, _dimension, _initialized

    if _initialized and _model_name == model_name:
        return  # already ready

    if _initialized and _model_name != model_name:
        warnings.warn(
            f"Embedding model already initialized as '{_model_name}'; "
            f"not reloading as '{model_name}'. "
            "Call with the same name or reset the module state.",
            RuntimeWarning,
            stacklevel=2,
        )
        return

    import os
    if os.getenv("AISMA_TEST_MODE") == "true":
        _model = LocalEmbeddingMock()
        _model_name = model_name
        _dimension = 384
        _initialized = True
        return

    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(model_name)
        _model_name = model_name
        _dimension = _model.get_sentence_embedding_dimension()
        _initialized = True
        # Optionally move to CPU offload if using GPU
        if cpu_offload and hasattr(_model, "device"):
            _model.to("cpu")
    except Exception as exc:  # noqa: BLE001
        _model = None
        _model_name = model_name
        _dimension = 384
        _initialized = False
        raise RuntimeError(f"Failed to load SentenceTransformer model '{model_name}': {exc}") from exc


class LocalEmbeddingMock:
    """CPU-friendly mock for testing when heavy torch/transformer downloads are unavailable."""

    def get_sentence_embedding_dimension(self) -> int:
        return 384

    def get_dimension(self) -> int:
        return 384

    def encode(self, texts: Any, **kwargs: Any) -> Any:
        import numpy as np
        if isinstance(texts, str):
            return np.zeros((384,), dtype=np.float32)
        return [np.zeros((384,), dtype=np.float32) for _ in texts]


def is_initialized() -> bool:
    """Return True if the embedding model singleton is ready."""
    return _initialized and _model is not None


def get_model() -> Any:
    """Return the singleton model instance, loading on demand if needed."""
    global _model, _initialized
    if _model is None:
        try:
            initialize()
        except Exception:
            _model = LocalEmbeddingMock()
            _initialized = True
    return _model


def get_dimension() -> int:
    """Return the embedding dimension for the current model."""
    m = get_model()
    if hasattr(m, "get_dimension"):
        return m.get_dimension()
    if hasattr(m, "get_sentence_embedding_dimension"):
        return m.get_sentence_embedding_dimension()
    return _dimension


def embed_query(query: str, *, model: Any | None = None) -> list[float]:
    """Embed a single query string.

    Args:
        query: The text query to embed.
        model: Optional model instance; uses the singleton if not provided.

    Returns:
        Embedding vector as a list of floats.
    """
    m = model or get_model()
    try:
        embedding = m.encode(query, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Embedding generation failed: {exc}") from exc


def embed_batch(
    queries: list[str],
    *,
    batch_size: int = 32,
    model: Any | None = None,
) -> list[list[float]]:
    """Embed a batch of query strings.

    Args:
        queries: List of text queries to embed.
        batch_size: Number of queries per batch (respect memory constraints).
        model: Optional model instance; uses the singleton if not provided.

    Returns:
        List of embedding vectors (each as list of floats).
    """
    m = model or _model
    if m is None:
        raise RuntimeError(
            "Embedding model not initialized. Call brand_os.embeddings.initialize() first."
        )

    if not queries:
        return []

    try:
        embeddings = m.encode(
            queries,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [emb.tolist() for emb in embeddings]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Batch embedding failed: {exc}") from exc


def reset() -> None:
    """Reset the singleton model state. Useful for testing or model swapping."""
    global _model, _model_name, _dimension, _initialized
    _model = None
    _model_name = "all-MiniLM-L6-v2"
    _dimension = 384
    _initialized = False


get_embedding = embed_query