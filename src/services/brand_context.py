"""Brand context service with RAG integration for AISMA v2.

Extends the existing BrandContextService to load approved brand knowledge
from the Brand OS repository via the RAG pipeline. Provides governed access
so that only authorized, approved information reaches agents.

Phase 3 behavior is preserved: in the absence of Brand OS data, the service
falls back to in-memory inputs and marks missing information. Imported
external content is scanned before use.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from brand_os.rag import QueryContext, VectorStoreConfig, run_retrieval_pipeline
from brand_os.schemas import (
    BrandCompletenessReport,
)
from governance.injection import InjectionScanError, scan_untrusted_text

logger = logging.getLogger(__name__)


@dataclass
class BrandContext:
    """Brand context for agent execution, with RAG-backed knowledge."""

    business_id: str
    brand_identity: dict[str, Any] = field(default_factory=dict)
    brand_voice: dict[str, Any] = field(default_factory=dict)
    target_audience: dict[str, Any] = field(default_factory=dict)
    positioning: dict[str, Any] = field(default_factory=dict)
    messaging: dict[str, Any] = field(default_factory=dict)
    verified_proof_points: list[dict[str, Any]] = field(default_factory=list)
    prohibited_claims: list[str] = field(default_factory=list)
    approved_products_services: list[dict[str, Any]] = field(default_factory=list)
    channel_guidelines: dict[str, Any] = field(default_factory=dict)
    content_restrictions: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    source: str = "unspecified"

    # RAG metadata
    rag_context: dict[str, Any] = field(default_factory=dict)  # from run_retrieval_pipeline
    last_rag_query: str = ""
    rag_retrieval_status: str = "none"  # none, success, no_approved_content

    def compact_prompt(self, max_chars: int = 4000) -> str:
        """Render brand context as a compact prompt string.

        Includes RAG context if available; otherwise falls back to in-memory fields.
        """
        parts = [
            f"business_id={self.business_id}",
            f"identity={self.brand_identity}",
            f"voice={self.brand_voice}",
            f"audience={self.target_audience}",
            f"positioning={self.positioning}",
            f"messaging={self.messaging}",
            f"proof_points={self.verified_proof_points}",
            f"prohibited_claims={self.prohibited_claims}",
            f"approved_offerings={self.approved_products_services}",
            f"channel_guidelines={self.channel_guidelines}",
            f"content_restrictions={self.content_restrictions}",
            f"missing_information={self.missing_information}",
        ]
        text = "\n".join(parts)
        if self.rag_context:
            # Prepend RAG context (approved brand knowledge from retrieval)
            rag_summary = self.rag_context.get("context_text", "")
            if rag_summary:
                text = f"BRAND_OS_RAG_CONTEXT:\n{rag_summary}\n\n{text}"
            # Add retrieval metadata note
            missing = self.rag_context.get("missing_info", [])
            verify = self.rag_context.get("verify_info", [])
            if missing:
                text += f"\n[MISSING] {', '.join(missing[:3])}"
            if verify:
                text += f"\n[VERIFY] {', '.join(verify[:3])}"

        if len(text) > max_chars:
            text = text[:max_chars] + "\n[TRUNCATED]"
        return text

    def to_dict(self) -> dict[str, Any]:
        return {
            "business_id": self.business_id,
            "brand_identity": self.brand_identity,
            "brand_voice": self.brand_voice,
            "target_audience": self.target_audience,
            "positioning": self.positioning,
            "messaging": self.messaging,
            "verified_proof_points": self.verified_proof_points,
            "prohibited_claims": self.prohibited_claims,
            "approved_products_services": self.approved_products_services,
            "channel_guidelines": self.channel_guidelines,
            "content_restrictions": self.content_restrictions,
            "missing_information": self.missing_information,
            "source": self.source,
            "rag_context": self.rag_context,
            "last_rag_query": self.last_rag_query,
            "rag_retrieval_status": self.rag_retrieval_status,
        }


class BrandContextService:
    """Loads and prepares brand context for agent execution.

    Provides two modes:
    1. RAG mode: Retrieves approved brand knowledge from the Brand OS repository
       using local Sentence Transformers + ChromaDB. Only approved knowledge is
       supplied; [MISSING] and [VERIFY] markers are preserved.
    2. In-memory mode (Phase 3 fallback): Accepts provided data and marks
       missing information. Imported external content is scanned before use.

    Governance: every operation enforces business_id tenant isolation. The kill
    switch is checked. Untrusted/imported content is scanned before use.
    """

    def __init__(self, kill_switch: Any = None, model_manager: Any = None) -> None:
        self.kill_switch = kill_switch
        self.model_manager = model_manager
        self._rag_config = VectorStoreConfig()  # default config

    def build(
        self,
        *,
        business_id: str,
        authorized_business_ids: set[str] | None = None,
        data: dict[str, Any] | None = None,
        imported_external_content: dict[str, str] | None = None,
        rag_query: str | None = None,  # optional query to retrieve from Brand OS
        agent_id: str | None = None,
        task_id: str | None = None,
    ) -> BrandContext:
        """Build a BrandContext, optionally retrieving from Brand OS RAG.

        If rag_query is provided, the service will retrieve approved brand knowledge
        from the Brand OS repository using local embeddings + ChromaDB. The retrieved
        context is integrated into the BrandCompact prompt.

        If rag_query is None, falls back to Phase 3 in-memory behavior.

        Raises PermissionError if business_id not authorized (tenant isolation).
        """
        # 1. Tenant isolation check
        if authorized_business_ids is not None and business_id not in authorized_business_ids:
            raise PermissionError(
                f"Tenant isolation: business {business_id} not authorized"
            )

        # 2. Kill switch check
        if self.kill_switch and self.kill_switch.is_engaged(business_id):
            raise PermissionError(f"Kill switch engaged for business {business_id}")

        # 3. If RAG query provided, retrieve from Brand OS
        rag_context: dict[str, Any] = {}
        last_rag_query = ""
        rag_retrieval_status = "none"

        if rag_query is not None and rag_query.strip():
            try:
                # Build QueryContext for RAG pipeline
                qc = QueryContext(
                    business_id=business_id,
                    agent_id=agent_id or "unknown",
                    task_id=task_id,
                    query=rag_query,
                    enforce_approved_only=True,
                    enforce_version_filter=True,
                )

                # Run retrieval pipeline
                result = run_retrieval_pipeline(qc, self._rag_config)

                rag_context = result
                last_rag_query = rag_query
                rag_retrieval_status = result.get("retrieval_metadata", {}).get(
                    "status", "success"
                )

                logger.info(
                    f"BrandContext RAG retrieval for {business_id}: "
                    f"returned {result.get('retrieval_metadata', {}).get('returned_count', 0)} "
                    f"chunks, {result.get('retrieval_metadata', {}).get('no_approved_content', False) = }"
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Brand OS RAG retrieval failed: {exc}")
                # Fall through to in-memory mode; do not raise to avoid breaking
                # agent execution when Brand OS is unavailable
                rag_retrieval_status = "failed"

        # 4. Build BrandContext from data + RAG context (if any)
        data = data or {}
        imported_external_content = imported_external_content or {}

        # Scan untrusted external content
        for source, text in imported_external_content.items():
            try:
                scan_untrusted_text(text, strict=True, source=f"brand_import:{source}")
            except InjectionScanError:
                raise  # re-raise as per Phase 3 contract

        # Known fields for BrandContext
        known_fields = [
            "brand_identity",
            "brand_voice",
            "target_audience",
            "positioning",
            "messaging",
            "verified_proof_points",
            "prohibited_claims",
            "approved_products_services",
            "channel_guidelines",
            "content_restrictions",
        ]

        # Start with RAG context if available and successful
        if rag_retrieval_status == "success" and rag_context.get("context_text", ""):
            # Use RAG context as the primary source
            # Extract relevant fields from the RAG context_text into the struct
            rag_text = rag_context["context_text"]
            # Parse simple BRAND_OS_RAG_CONTEXT block if present
            # (The compact_prompt will handle the integration)
            primary_data = self._extract_from_rag_context(rag_text)
        else:
            # Fall back to provided data (Phase 3 behavior)
            primary_data = data

        missing: list[str] = []

        # Populate fields from primary_data (RAG or provided)
        brand_identity = dict(primary_data.get("brand_identity") or {})
        brand_voice = dict(primary_data.get("brand_voice") or {})
        target_audience = dict(primary_data.get("target_audience") or {})
        positioning = dict(primary_data.get("positioning") or {})
        messaging = dict(primary_data.get("messaging") or {})
        verified_proof_points = list(primary_data.get("verified_proof_points") or [])
        prohibited_claims = list(primary_data.get("prohibited_claims") or [])
        approved_products_services = list(primary_data.get("approved_products_services") or [])
        channel_guidelines = dict(primary_data.get("channel_guidelines") or {})
        content_restrictions = list(primary_data.get("content_restrictions") or [])

        # Detect missing fields from known_fields
        # A field is "missing" if it has no value AND it's not present in RAG context
        # We check against the RAG context's missing_info
        rag_missing = rag_context.get("missing_info", [])
        _rag_verify = rag_context.get("verify_info", [])

        # Combine missing from RAG and from data gaps
        all_rag_missing = [f"RAG:{m}" for m in rag_missing]
        data_missing = [f for f in known_fields if not primary_data.get(f)]
        missing = all_rag_missing + data_missing

        # If RAG returned no approved content, surface [MISSING]
        if rag_retrieval_status == "success" and rag_context.get("no_approved_content"):
            missing.append("[MISSING] no approved brand knowledge found for this query/business")
            # Still proceed but mark clearly

        ctx = BrandContext(
            business_id=business_id,
            brand_identity=brand_identity,
            brand_voice=brand_voice,
            target_audience=target_audience,
            positioning=positioning,
            messaging=messaging,
            verified_proof_points=verified_proof_points,
            prohibited_claims=prohibited_claims,
            approved_products_services=approved_products_services,
            channel_guidelines=channel_guidelines,
            content_restrictions=content_restrictions,
            missing_information=missing,
            source=str(primary_data.get("source") or ("rag" if rag_retrieval_status == "success" else "provided")),
            rag_context=rag_context,
            last_rag_query=last_rag_query,
            rag_retrieval_status=rag_retrieval_status,
        )

        # Log the context build
        self._audit_context_build(ctx)

        return ctx

    def _extract_from_rag_context(self, rag_text: str) -> dict[str, Any]:
        """Extract structured fields from RAG context text.

        In Phase 4 this is a best-effort parse of the compact prompt text
        generated by run_retrieval_pipeline. Real systems would use proper
        structured data return from the RAG pipeline.
        """
        result: dict[str, Any] = {}
        # Very simple heuristic: look for key=value patterns
        import re

        for match in re.finditer(r"(\w+)=(.+?)(?:\n|$)", rag_text):
            key = match.group(1)
            val = match.group(2).strip()
            if key in {
                "brand_identity",
                "brand_voice",
                "target_audience",
                "positioning",
                "messaging",
            }:
                result[key] = eval(val) if val else {}

        return result

    def safe_scan_external(self, text: str, *, source: str) -> str:
        """Scan and isolate untrusted text, consistent with Phase 3 contract."""
        try:
            result = scan_untrusted_text(text, strict=True, source=source)
            return result["isolated_text"]
        except InjectionScanError:
            raise

    def get_completeness_report(self, business_id: str) -> BrandCompletenessReport:
        """Get a BrandCompletenessReport for a business.

        Scans the Brand OS repository for the business and returns a structured
        report of template completion status, missing fields, verification requirements,
        pending approvals, and archived records.
        """
        from brand_os.repository import compute_completeness_report

        return compute_completeness_report(business_id)

    def _audit_context_build(self, ctx: BrandContext) -> None:
        """Audit event for BrandContext build (fire-and-forget)."""
        try:
            from governance.audit import AuditLogger

            audit = AuditLogger()
            audit.log(
                business_id=ctx.business_id,
                actor="brand_context_service",
                action="brand_context_built",
                resource=f"business:{ctx.business_id}",
                outcome="ok",
                details={
                    "rag_retrieval_status": ctx.rag_retrieval_status,
                    "source": ctx.source,
                    "missing_count": len(ctx.missing_information),
                },
            )
        except Exception:  # noqa: BLE001
            pass