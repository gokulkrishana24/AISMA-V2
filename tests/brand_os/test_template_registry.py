"""Template registry tests for Brand OS Phase 4."""

from brand_os.templates import (
    TemplateID,
    get_all_template_ids,
    get_template,
    get_template_completeness,
    list_templates,
)


class TestTemplateIDEnum:
    """Test that all 27 template IDs are defined."""

    def test_all_27_template_ids_exist(self):
        ids = get_all_template_ids()
        assert len(ids) == 27


class TestTemplateRegistry:
    """Test the 27-template registry."""

    def test_all_templates_available(self):
        templates = list_templates()
        assert len(templates) == 27

    def test_template_have_unique_ids(self):
        templates = list_templates()
        ids = [t.get("name", "") for t in templates]
        assert len(ids) == len(set(ids))

    def test_template_has_required_fields(self):
        # Test that BRAND_IDENTITY has brandName and mission as required
        template = get_template(TemplateID.BRAND_IDENTITY)
        fields = template.get("fields", {})
        assert "brandName" in fields
        assert fields["brandName"]["type"] == "required"
        assert "mission" in fields
        assert fields["mission"]["type"] == "required"


class TestTemplateCompleteness:
    """Test completeness report generation."""

    def test_completeness_report_structure(self):
        report = get_template_completeness("biz_test", {})
        assert report.total_templates == 27
        assert hasattr(report, "completed_templates")
        assert hasattr(report, "incomplete_templates")
        assert hasattr(report, "missing_fields")
        assert hasattr(report, "verification_required")
        assert hasattr(report, "pending_approvals")
        assert hasattr(report, "archived_records")