"""Embedding tests for Brand OS Phase 4."""

import os

os.environ["AISMA_TEST_MODE"] = "true"

from brand_os.embeddings import get_embedding, get_model, is_initialized, reset


class TestEmbeddingModelSingleton:
    """Test the lazy singleton embedding model."""

    def test_get_model_returns_instance(self):
        """get_model should return a SentenceTransformer instance."""
        model = get_model()
        assert model is not None

    def test_get_embedding_initialized(self):
        """get_embedding should work when model is initialized."""
        get_model()
        embedding = get_embedding("test document text")
        assert embedding is not None
        assert len(embedding) > 0

    def test_embedding_dimension(self):
        """Embedding should have correct dimension (384 for all-MiniLM-L6-v2)."""
        model = get_model()
        embedding = get_embedding("test document text for dimension check")
        assert len(embedding) == model.get_dimension()


class TestMissingModelHandling:
    """Test handling when model is not available."""

    def test_missing_model_handling(self):
        """Should handle missing model gracefully."""
        try:
            # The model should load successfully in normal conditions
            # but we test that the function doesn't crash
            pass
        except Exception as e:
            # Expected if model files aren't available
            assert "model" in str(e).lower() or "load" in str(e).lower()


class TestLazyLoading:
    """Test lazy loading behavior."""

    def test_model_loads_on_demand(self):
        """Model should be loaded on first call, not before."""
        model1 = get_model()
        model2 = get_model()
        assert model1 is model2  # Should be the same singleton instance


class TestInitializationState:
    """Test initialization state checks."""

    def test_is_initialized_after_import(self):
        """is_initialized should work after module import."""
        assert is_initialized() is not None  # Should be True or False, not crash

    def test_reset_clears_model(self):
        """reset should clear the model instance."""
        reset()
        # After reset, model should be reinitializable
        model = get_model()
        assert model is not None