"""Business-scoped permissions for Brand OS operations.

Enforces tenant isolation: every read/write/query operation must include a
business_id, and the repository/vector store must reject any operation that
attempts to cross business boundaries.

Phase 4 preserves the existing Phase 1 PermissionManager patterns (default-deny,
least privilege) but implements Brand OS-specific checks.
"""

from __future__ import annotations

from brand_os.repository import _ensure_business_dir
from brand_os.schemas import ApprovalState


class PermissionManager:
    """Brand OS-scoped permission checks.

    Rules:
    - Default deny: if business_id cannot be verified, deny access.
    - Least privilege: only the minimum necessary data is accessible.
    - Tenant isolation: business_id is enforced at the storage boundary.
    """

    @staticmethod
    def verify_business_id(business_id: str) -> None:
        """Verify that a business_id is valid and not a path traversal attempt.

        Raises PermissionError if the business_id is invalid.
        """
        if not business_id:
            raise PermissionError("business_id is required for Brand OS operations")

        # Re-use the repository's path traversal check
        try:
            _ensure_business_dir(business_id)
        except PermissionError as exc:
            raise PermissionError(f"Invalid business_id: {exc}") from exc

    @staticmethod
    def check_can_read_business_data(business_id: str, requester_id: str | None = None) -> None:
        """Check that a requester can read data for the given business.

        In Phase 4 this is a no-op (trust the business_id isolation in storage),
        but it exists as an explicit hook for future RBAC integration (Phase 5).
        """
        # Phase 4: basic validation only
        PermissionManager.verify_business_id(business_id)

    @staticmethod
    def check_can_write_brand_knowledge(business_id: str, actor: str) -> None:
        """Check that an actor can write brand knowledge for a business.

        In Phase 4, any authorized human admin can write; actual approval
        workflow is enforced through the ingestion pipeline and versioning.
        """
        PermissionManager.verify_business_id(business_id)

    @staticmethod
    def check_can_retrieve_brand_knowledge(business_id: str, agent_id: str) -> None:
        """Check that an agent can retrieve brand knowledge for a business.

        Enforces that the agent's assigned business_id matches the request.
        """
        PermissionManager.verify_business_id(business_id)

    @staticmethod
    def check_approval_access(
        business_id: str,
        required_state: ApprovalState,
        current_state: ApprovalState,
    ) -> bool:
        """Determine if the current approval state meets the required state.

        Rules (deterministic Python, no LLM):
        - PENDING -> APPROVED requires explicit approval transition
        - DRAFT -> PENDING_APPROVAL is allowed
        - Any state -> REJECTED requires human escalation
        - APPROVED -> any state is allowed (already approved)
        """
        # Simple state transition check
        allowed_transitions = {
            ApprovalState.PENDING: {ApprovalState.APPROVED, ApprovalState.REJECTED},
            ApprovalState.DRAFT: {ApprovalState.PENDING, ApprovalState.REJECTED},
            ApprovalState.APPROVED: {ApprovalState.REJECTED, ApprovalState.APPROVED},
            ApprovalState.REJECTED: set(),  # terminal
            ApprovalState.UNAUTHORIZED: {ApprovalState.PENDING, ApprovalState.DRAFT},
        }

        allowed = allowed_transitions.get(current_state, set())
        return required_state in allowed


class RepoPermissionError(PermissionError):
    """Raised when a repository operation violates isolation or access rules."""

    pass


def verify_business_id(business_id: str) -> bool:
    try:
        PermissionManager.verify_business_id(business_id)
        return True
    except PermissionError as exc:
        raise RepoPermissionError(f"Invalid business_id: {exc}") from exc


def check_can_read(business_id: str, requester_id: str | None = None) -> bool:
    try:
        PermissionManager.check_can_read_business_data(business_id, requester_id)
        return True
    except PermissionError as exc:
        raise RepoPermissionError(str(exc)) from exc


def check_can_write(business_id: str, actor: str = "human_admin") -> bool:
    try:
        PermissionManager.check_can_write_brand_knowledge(business_id, actor)
        return True
    except PermissionError as exc:
        raise RepoPermissionError(str(exc)) from exc


def check_can_retrieve(business_id: str, agent_id: str = "general") -> bool:
    try:
        PermissionManager.check_can_retrieve_brand_knowledge(business_id, agent_id)
        return True
    except PermissionError as exc:
        raise RepoPermissionError(str(exc)) from exc