"""Unit tests for project resolution node."""

import pytest
from unittest.mock import AsyncMock, patch
from src.nodes.project_resolution import resolve_projects, get_boondmanager_projects
from src.models.state import InvoiceWorkflowState


@pytest.fixture
def state_with_activities():
    """State with consultant activities needing project resolution."""
    return {
        "current_step": "project_resolution",
        "email_data": {
            "sender": "test@test.com",
            "subject": "Test",
            "body_text": "",
            "billing_month": "2025-10",
        },
        "consultant_activities": [
            {
                "consultant_name": "Elodie LEGUAY",
                "days_declared": 22.0,
                "project_name": "Modernisation Ligne Production",
                "project_id": None,
                "client_id": None,
                "days_in_boond": None,
                "resource_id": None,
                "resource_name": None,
                "timesheet_id": None,
                "discrepancy_amount": None,
                "severity": None,
                "client_name": None,
            }
        ],
        "invoice_data": None,
        "has_discrepancies": False,
        "validation_passed": False,
        "errors": [],
        "warnings": [],
    }


@pytest.fixture
def mock_boond_projects():
    """Mock BoondManager projects response."""
    return {
        "data": [
            {
                "id": "proj-123",
                "attributes": {"name": "Modernisation Ligne Production - Multi commande"},
                "relationships": {"company": {"data": {"id": "client-456"}}},
            },
            {
                "id": "proj-789",
                "attributes": {"name": "Migration Cloud AWS - Temps partiel"},
                "relationships": {"company": {"data": {"id": "client-999"}}},
            },
        ]
    }


@pytest.mark.asyncio
async def test_get_boondmanager_projects_tool(mock_boond_projects):
    """Test the BoondManager projects fetching tool."""
    with patch("src.nodes.project_resolution.BoondManagerClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_projects = AsyncMock(return_value=mock_boond_projects)

        # Invoke tool with empty input (tool doesn't need parameters)
        result = await get_boondmanager_projects.ainvoke({})

        print("\n" + "=" * 80)
        print("TOOL OUTPUT - get_boondmanager_projects:")
        print("=" * 80)
        print(result)
        print("=" * 80 + "\n")

        # Verify tool returns JSON with project data
        assert "proj-123" in result
        assert "Modernisation Ligne Production" in result
        assert "client-456" in result


@pytest.mark.asyncio
async def test_resolve_projects_with_react_agent(state_with_activities, mock_boond_projects):
    """Test project resolution with actual ReAct agent execution."""
    with patch("src.nodes.project_resolution.BoondManagerClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_projects = AsyncMock(return_value=mock_boond_projects)

        # Run resolution - agent will use the real LLM
        result = await resolve_projects(state_with_activities)

        print("\n" + "=" * 80)
        print("REACT AGENT EXECUTION RESULT:")
        print("=" * 80)
        print(
            "\nInput project name:",
            state_with_activities["consultant_activities"][0]["project_name"],
        )
        print("\nResolved activity:")
        activity = result["consultant_activities"][0]
        print(f"  - Project ID: {activity['project_id']}")
        print(f"  - Client ID: {activity['client_id']}")
        print(f"  - Matched Name: {activity['project_name']}")
        print("\nWorkflow progression:", result["current_step"])
        print("Errors:", result["errors"])
        print("=" * 80 + "\n")

        # Verify the agent successfully resolved the project
        assert activity["project_id"] is not None
        assert activity["client_id"] is not None

        # Verify workflow progression
        assert result["current_step"] == "verification"
        assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_resolve_projects_handles_api_errors(state_with_activities):
    """Test error handling when BoondManager API fails."""
    # Patch at a higher level to ensure error is caught
    with patch("src.nodes.project_resolution.get_llm") as mock_get_llm:
        mock_get_llm.side_effect = Exception("LLM Error")

        result = await resolve_projects(state_with_activities)

        print("\n" + "=" * 80)
        print("ERROR HANDLING TEST:")
        print("=" * 80)
        print("Errors:", result["errors"])
        print("Current step:", result["current_step"])
        print("=" * 80 + "\n")

        # Verify error handling
        assert len(result["errors"]) >= 1
        assert "Project resolution error" in result["errors"][0]
        assert result["current_step"] == "completed"
