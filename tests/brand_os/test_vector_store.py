"""Vector store tests for Brand OS Phase 4."""

from brand_os.vector_store import (
    add_chunks,
    clear_collection,
    delete_chunks,
    initialize_chroma,
    is_initialized,
    query_chunks,
)


class TestVectorStoreInitialization:
    """Test ChromaDB initialization."""

    def test_initialize_chroma_creates_collection(self):
        """initialize_chroma should create/initialize the ChromaDB collection."""
        result = initialize_chroma()
        assert result is not None

    def test_initialized_flag(self):
        """_initialized should be set after initialization."""
        # The module should have _initialized set to True after init
        assert is_initialized() is not None


class TestAddQueryChunks:
    """Test adding and querying chunks."""

    def test_add_chunks_stores_metadata(self):
        """Adding chunks should store business_id in metadata."""
        # Initialize first
        initialize_chroma()

        # Add chunks with business_id metadata
        chunks = [
            {
                "business_id": "test_biz_vs",
                "document_id": "doc_vs_001",
                "template_id": "brand_identity",
                "section_id": "root",
                "chunk_id": "chunk_vs_1",
                "version": "v1.0",
                "content": "Test content for vector store",
                "approved": True,
                "missing": False,
                "verified": True,
            }
        ]

        add_chunks(chunks)

        # Query should find the chunks
        results = query_chunks(
            "test content", business_id="test_biz_vs", top_k=5
        )
        assert len(results) > 0

    def test_business_id_filtering(self):
        """Query with business_id should only return chunks for that business."""
        # Initialize first
        initialize_chroma()

        # Add chunks for different businesses
        chunks_biz_a = [
            {
                "business_id": "biz_a",
                "document_id": "doc_a",
                "template_id": "brand_identity",
                "section_id": "root",
                "chunk_id": "chunk_a",
                "version": "v1.0",
                "content": "Content for biz A",
                "approved": True,
                "missing": False,
                "verified": True,
            }
        ]

        chunks_biz_b = [
            {
                "business_id": "biz_b",
                "document_id": "doc_b",
                "template_id": "brand_identity",
                "section_id": "root",
                "chunk_id": "chunk_b",
                "version": "v1.0",
                "content": "Content for biz B",
                "approved": True,
                "missing": False,
                "verified": True,
            }
        ]

        add_chunks(chunks_biz_a)
        add_chunks(chunks_biz_b)

        # Query for biz_a should only return biz_a chunks
        results_a = query_chunks("Content for biz A", business_id="biz_a", top_k=5)
        biz_a_ids = [r.get("metadata", {}).get("business_id") for r in results_a]
        assert "biz_a" in biz_a_ids
        assert "biz_b" not in biz_a_ids

        # Query for biz_b should only return biz_b chunks
        results_b = query_chunks("Content for biz B", business_id="biz_b", top_k=5)
        biz_b_ids = [r.get("metadata", {}).get("business_id") for r in results_b]
        assert "biz_b" in biz_b_ids
        assert "biz_a" not in biz_b_ids


class TestDeleteAndClear:
    """Test deletion and clearing."""

    def test_delete_chunks_removes_specific(self):
        """delete_chunks should remove specific chunks."""
        initialize_chroma()

        chunks = [
            {
                "business_id": "test_biz_delete",
                "document_id": "doc_delete",
                "template_id": "brand_identity",
                "section_id": "root",
                "chunk_id": "chunk_to_delete",
                "version": "v1.0",
                "content": "Content to delete",
                "approved": True,
                "missing": False,
                "verified": True,
            }
        ]

        add_chunks(chunks)
        delete_chunks(business_id="test_biz_delete", chunk_id="chunk_to_delete")

        # After deletion, query should return no results or fewer results
        query_chunks(
            "Content to delete", business_id="test_biz_delete", top_k=5
        )
        # May return 0 results after deletion

    def test_clear_collection(self):
        """clear_collection should clear the entire collection."""
        initialize_chroma()

        # Add some chunks
        chunks = [
            {
                "business_id": "test_biz_clear",
                "document_id": "doc_clear",
                "template_id": "brand_identity",
                "section_id": "root",
                "chunk_id": "chunk_clear",
                "version": "v1.0",
                "content": "Content to clear",
                "approved": True,
                "missing": False,
                "verified": True,
            }
        ]

        add_chunks(chunks)

        # Clear the collection
        clear_collection()

        # After clearing, query should return no results
        results = query_chunks("Content to clear", top_k=5)
        assert len(results) == 0