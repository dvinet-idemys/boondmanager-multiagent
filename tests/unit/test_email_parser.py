"""Unit tests for email parsing node."""

import pytest
from src.nodes.email_parser import parse_email
from src.models.state import InvoiceWorkflowState


@pytest.fixture
def simple_email_content():
    """Simple email with single project."""
    with open("tests/fixtures/sample_email_simple.txt", "r") as f:
        return f.read()


@pytest.fixture
def multi_project_email_content():
    """Multi-project email with consultants appearing in multiple projects."""
    with open("tests/fixtures/sample_email.txt", "r") as f:
        return f.read()


def test_parse_simple_email(simple_email_content):
    """Test parsing email with single project."""
    state: InvoiceWorkflowState = {
        "current_step": "email_parsing",
        "raw_email_content": simple_email_content,
        "email_data": None,
        "consultant_activities": [],
        "invoice_data": None,
        "has_discrepancies": False,
        "validation_passed": False,
        "errors": [],
        "warnings": []
    }

    result = parse_email(state)

    # Check email metadata
    assert result["email_data"] is not None
    assert result["email_data"]["sender"] == "alexis@conseil-tech.fr"
    assert result["email_data"]["billing_month"] == "2025-10"

    # Check consultant activities
    assert len(result["consultant_activities"]) == 2

    # Check first consultant
    elodie = next((c for c in result["consultant_activities"] if "Elodie" in c["consultant_name"]), None)
    assert elodie is not None
    assert elodie["days_declared"] == 22
    assert elodie["project_name"] == "Modernisation Ligne Production - Multi commande"

    # Check second consultant
    didier = next((c for c in result["consultant_activities"] if "Didier" in c["consultant_name"]), None)
    assert didier is not None
    assert didier["days_declared"] == 12
    assert didier["project_name"] == "Modernisation Ligne Production - Multi commande"

    # Check workflow progression
    assert result["current_step"] == "project_resolution"
    assert len(result["errors"]) == 0


def test_parse_multi_project_email(multi_project_email_content):
    """Test parsing email with multiple projects."""
    state: InvoiceWorkflowState = {
        "current_step": "email_parsing",
        "raw_email_content": multi_project_email_content,
        "email_data": None,
        "consultant_activities": [],
        "invoice_data": None,
        "has_discrepancies": False,
        "validation_passed": False,
        "errors": [],
        "warnings": []
    }

    result = parse_email(state)

    # Check email metadata
    assert result["email_data"] is not None
    assert result["email_data"]["sender"] == "alexis@conseil-tech.fr"
    assert result["email_data"]["billing_month"] == "2025-10"

    # Should have 8 consultant activities (Jon LEVIN appears twice in different projects)
    assert len(result["consultant_activities"]) == 8

    # Check Jon LEVIN appears in two different projects
    jon_activities = [c for c in result["consultant_activities"] if "Jon" in c["consultant_name"] and "LEVIN" in c["consultant_name"]]
    assert len(jon_activities) == 2

    # Verify projects are different for Jon
    jon_projects = {activity["project_name"] for activity in jon_activities}
    assert len(jon_projects) == 2
    assert "Migration Cloud AWS" in str(jon_projects)
    assert "Application Mobile Interne" in str(jon_projects)

    # Verify days for each Jon activity
    jon_days = sorted([activity["days_declared"] for activity in jon_activities])
    assert jon_days == [7, 15]

    # Check workflow progression
    assert result["current_step"] == "project_resolution"
    assert len(result["errors"]) == 0


def test_parse_email_with_no_content():
    """Test error handling when no email content provided."""
    state: InvoiceWorkflowState = {
        "current_step": "email_parsing",
        "raw_email_content": "",
        "email_data": None,
        "consultant_activities": [],
        "invoice_data": None,
        "has_discrepancies": False,
        "validation_passed": False,
        "errors": [],
        "warnings": []
    }

    result = parse_email(state)

    # Should have error and move to completed state
    assert len(result["errors"]) == 1
    assert "No email content" in result["errors"][0]
    assert result["current_step"] == "completed"


def test_consultant_activity_structure():
    """Test that consultant activities have correct structure with project references."""
    state: InvoiceWorkflowState = {
        "current_step": "email_parsing",
        "raw_email_content": open("tests/fixtures/sample_email_simple.txt").read(),
        "email_data": None,
        "consultant_activities": [],
        "invoice_data": None,
        "has_discrepancies": False,
        "validation_passed": False,
        "errors": [],
        "warnings": []
    }

    result = parse_email(state)

    # Check structure of consultant activity
    for activity in result["consultant_activities"]:
        assert "consultant_name" in activity
        assert "days_declared" in activity
        assert "project_name" in activity
        assert activity["project_name"] is not None
        assert isinstance(activity["days_declared"], float)

        # Initially unresolved fields should be None
        assert activity["days_in_boond"] is None
        assert activity["project_id"] is None
        assert activity["client_id"] is None
