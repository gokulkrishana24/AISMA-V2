"""Repository tests for Brand OS Phase 4."""

import os
import shutil

from brand_os.repository import (
    RepoPermissionError,
    _ensure_business_dir,
    archive_document,
    compute_completeness_report,
    load_chunks,
    load_document_meta,
    load_version_record,
    store_chunks,
    store_document_meta,
    store_version_record,
)


class TestRepositoryBasics:
    """Test basic repository operations."""

    def test_ensure_business_dir_valid(self):
        """Valid business ID should create directory."""
        biz_id = "test_biz_001"
        try:
            _ensure_business_dir(biz_id)
            assert os.path.isdir("state/brand_os/test_biz_001/documents")
        finally:
            if os.path.exists("state/brand_os/test_biz_001"):
                shutil.rmtree("state/brand_os/test_biz_001", ignore_errors=True)

    def test_ensure_business_dir_invalid(self):
        """Invalid business ID (path traversal) should raise PermissionError."""
        try:
            _ensure_business_dir("../etc")
            raise AssertionError("Should have raised PermissionError")
        except RepoPermissionError:
            pass  # Expected

    def test_business_id_cannot_start_with_slash(self):
        """Business ID starting with / should raise PermissionError."""
        try:
            _ensure_business_dir("/absolute/path")
            raise AssertionError("Should have raised PermissionError")
        except RepoPermissionError:
            pass  # Expected


class TestDocumentMeta:
    """Test DocumentMeta storage and loading."""

    def test_store_and_load_document_meta(self):
        """Store and retrieve DocumentMeta."""
        biz_id = "test_biz_meta"
        doc_id = "doc_001"
        meta = {
            "business_id": biz_id,
            "document_id": doc_id,
            "template_id": "brand_identity",
            "section_id": "root",
            "chunk_id": "root",
            "version": "v1.0",
            "source_name": "test",
            "source_path": None,
            "approval_state": "unauthorized",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "created_by": "test",
            "updated_by": "test",
        }

        # Ensure business dir exists
        from brand_os.repository import _ensure_business_dir
        _ensure_business_dir(biz_id)

        store_document_meta(biz_id, doc_id, meta)
        loaded = load_document_meta(biz_id, doc_id)
        assert loaded is not None
        assert loaded.business_id == biz_id
        assert loaded.document_id == doc_id
        assert loaded.template_id == "brand_identity"


class TestVersionRecord:
    """Test VersionRecord storage and loading."""

    def test_store_and_load_version_record(self):
        """Store and retrieve VersionRecord."""
        biz_id = "test_biz_version"
        doc_id = "doc_002"
        # Ensure business dir exists
        from brand_os.repository import _ensure_business_dir
        from brand_os.schemas import VersionRecord
        _ensure_business_dir(biz_id)

        version = VersionRecord(
            version="v1.0",
            previous_version=None,
            change_summary="Initial version",
            updated_by="test",
            updated_at="2024-01-01T00:00:00Z",
            approval_state="unauthorized",
            source="test",
        )

        store_version_record(biz_id, doc_id, version)
        loaded = load_version_record(biz_id, doc_id, "v1.0")
        assert loaded is not None
        assert loaded.version == "v1.0"
        assert loaded.change_summary == "Initial version"


class TestChunkOperations:
    """Test chunk storage and loading."""

    def test_store_and_load_chunks(self):
        """Store and retrieve ChunkContent."""
        biz_id = "test_biz_chunks"
        doc_id = "doc_003"
        version = "v1.0"

        # Ensure business dir exists
        from brand_os.repository import _ensure_business_dir
        _ensure_business_dir(biz_id)

        from brand_os.schemas import ChunkContent

        chunks = [
            ChunkContent(
                business_id=biz_id,
                document_id=doc_id,
                template_id="brand_identity",
                section_id="root",
                chunk_id="chunk_1",
                version=version,
                content="Test chunk content",
                approved=True,
                missing=False,
                verified=False,
                source_attribution={"source_name": "test", "source_type": "ingested"},
            )
        ]

        store_chunks(biz_id, doc_id, version, chunks)
        loaded = load_chunks(biz_id, doc_id, version)
        assert loaded is not None
        assert len(loaded) == 1
        assert loaded[0].content == "Test chunk content"
        assert loaded[0].approved


class TestArchiveDocument:
    """Test document archival."""

    def test_archive_document_moves_directory(self):
        """Archive document should move directory."""
        biz_id = "test_biz_archive"
        doc_id = "doc_004"

        # Ensure business dir exists
        from brand_os.repository import _ensure_business_dir
        _ensure_business_dir(biz_id)

        # Create a test document directory with a file
        doc_dir = os.path.join("state/brand_os", biz_id, "documents", doc_id)
        os.makedirs(doc_dir, exist_ok=True)
        with open(os.path.join(doc_dir, "test.txt"), "w") as f:
            f.write("test content")

        # Archive
        result = archive_document(biz_id, doc_id)
        assert result

        # Cleanup
        shutil.rmtree("state/brand_os/test_biz_archive", ignore_errors=True)


class TestCompletenessReport:
    """Test completeness report computation."""

    def test_compute_completeness_report(self):
        """Test that completeness report can be computed."""
        biz_id = "test_biz_completeness"

        # Ensure business dir exists
        from brand_os.repository import _ensure_business_dir
        _ensure_business_dir(biz_id)

        report = compute_completeness_report(biz_id)
        assert report is not None
        assert hasattr(report, "total_templates")
        assert hasattr(report, "completed_templates")
        assert hasattr(report, "incomplete_templates")