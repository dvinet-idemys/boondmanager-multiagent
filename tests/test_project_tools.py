"""Unit tests for project tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.project_tools import (
    get_project_by_id,
    get_project_information,
    get_project_orders,
    get_project_productivity,
    get_project_rights,
    get_project_tasks,
    search_projects,
)

# ============================================================================
# Mock Data
# ============================================================================

MOCK_PROJECT_SEARCH_RESPONSE = {
    "data": [
        {
            "id": "12345",
            "type": "projects",
            "attributes": {
                "reference": "PRJ12345",
                "title": "Project Alpha",
                "state": {"id": 1, "value": "Active"},
            },
            "relationships": {"company": {"data": {"id": "123", "type": "companies"}}},
        }
    ]
}

MOCK_PROJECT_BY_ID_RESPONSE = {
    "data": {
        "id": "12345",
        "type": "projects",
        "attributes": {
            "reference": "PRJ12345",
            "title": "Project Alpha",
            "state": {"id": 1, "value": "Active"},
        },
    }
}

MOCK_PRODUCTIVITY_RESPONSE = {
    "data": [
        {
            "id": "prod-1",
            "type": "productivity",
            "attributes": {
                "resource": {"id": 234, "firstName": "Elodie", "lastName": "LEGUAY"},
                "workedDays": 12,
                "timesReport": {"id": "timesheet-1"},
            },
        },
        {
            "id": "prod-2",
            "type": "productivity",
            "attributes": {
                "resource": {"id": 567, "firstName": "Didier", "lastName": "GEIG"},
                "workedDays": 22,
                "timesReport": {"id": "timesheet-2"},
            },
        },
    ]
}


# ============================================================================
# Test search_projects
# ============================================================================


@pytest.mark.asyncio
async def test_search_projects_by_keywords():
    """Test searching projects by keywords."""
    with patch("src.tools.project_tools.BoondManagerClient") as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.get_projects.return_value = MOCK_PROJECT_SEARCH_RESPONSE
        mock_client_class.return_value = mock_client

        # Execute tool
        result = await search_projects.ainvoke({"keywords": "alpha"})

        # Assertions
        assert "data" in result
        assert len(result["data"]) == 1
        assert result["data"][0]["attributes"]["title"] == "Project Alpha"
        mock_client.get_projects.assert_called_once()


@pytest.mark.asyncio
async def test_search_projects_by_company():
    """Test searching projects by company ID."""
    with patch("src.tools.project_tools.BoondManagerClient") as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.get_projects.return_value = MOCK_PROJECT_SEARCH_RESPONSE
        mock_client_class.return_value = mock_client

        # Execute tool
        result = await search_projects.ainvoke({"companies": [123]})

        # Assertions
        assert "data" in result
        mock_client.get_projects.assert_called_once_with(company_id=123)


@pytest.mark.asyncio
async def test_search_projects_error_handling():
    """Test error handling in search_projects."""
    with patch("src.tools.project_tools.BoondManagerClient") as mock_client_class:
        # Setup mock to raise exception
        mock_client = AsyncMock()
        mock_client.get_projects.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client

        # Execute tool
        result = await search_projects.ainvoke({"keywords": "test"})

        # Assertions
        assert "error" in result
        assert result["error"] == "API Error"
        assert result["data"] == []


# ============================================================================
# Test get_project_by_id
# ============================================================================


@pytest.mark.asyncio
async def test_get_project_by_id_success():
    """Test fetching project by ID."""
    with patch("src.tools.project_tools.BoondManagerClient") as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client._make_request.return_value = MOCK_PROJECT_BY_ID_RESPONSE
        mock_client_class.return_value = mock_client

        # Execute tool
        result = await get_project_by_id.ainvoke({"project_id": 12345})

        # Assertions
        assert "data" in result
        assert result["data"]["attributes"]["title"] == "Project Alpha"
        mock_client._make_request.assert_called_once_with("projects/12345")


@pytest.mark.asyncio
async def test_get_project_by_id_not_found():
    """Test fetching non-existent project."""
    with patch("src.tools.project_tools.BoondManagerClient") as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client._make_request.side_effect = Exception("Project not found")
        mock_client_class.return_value = mock_client

        # Execute tool
        result = await get_project_by_id.ainvoke({"project_id": 999999})

        # Assertions
        assert "error" in result
        assert "not found" in result["error"].lower()


# ============================================================================
# Test get_project_productivity
# ============================================================================


@pytest.mark.asyncio
async def test_get_project_productivity_success():
    """Test fetching project productivity data."""
    with patch("src.tools.project_tools.BoondManagerClient") as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.get_project_productivity.return_value = MOCK_PRODUCTIVITY_RESPONSE
        mock_client_class.return_value = mock_client

        # Execute tool
        result = await get_project_productivity.ainvoke({"project_id": 4})

        # Assertions
        assert "data" in result
        assert len(result["data"]) == 2
        assert result["data"][0]["attributes"]["resource"]["firstName"] == "Elodie"
        assert result["data"][1]["attributes"]["resource"]["firstName"] == "Didier"
        mock_client.get_project_productivity.assert_called_once_with(4)


# ============================================================================
# Test Extended Tools
# ============================================================================


@pytest.mark.asyncio
async def test_get_project_information():
    """Test fetching detailed project information."""
    with patch("src.tools.project_tools.BoondManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client._make_request.return_value = {"data": {"info": "detailed"}}
        mock_client_class.return_value = mock_client

        result = await get_project_information.ainvoke({"project_id": 1})

        assert "data" in result
        mock_client._make_request.assert_called_once_with("projects/1/information")


@pytest.mark.asyncio
async def test_get_project_orders():
    """Test fetching project orders."""
    with patch("src.tools.project_tools.BoondManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get_project_orders.return_value = {"data": []}
        mock_client_class.return_value = mock_client

        result = await get_project_orders.ainvoke({"project_id": 1})

        assert "data" in result
        mock_client.get_project_orders.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_project_tasks():
    """Test fetching project tasks."""
    with patch("src.tools.project_tools.BoondManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client._make_request.return_value = {"data": []}
        mock_client_class.return_value = mock_client

        result = await get_project_tasks.ainvoke({"project_id": 1})

        assert "data" in result
        mock_client._make_request.assert_called_once_with("projects/1/tasks")


@pytest.mark.asyncio
async def test_get_project_rights():
    """Test fetching project rights."""
    with patch("src.tools.project_tools.BoondManagerClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client._make_request.return_value = {"data": {}}
        mock_client_class.return_value = mock_client

        result = await get_project_rights.ainvoke({"project_id": 1})

        assert "data" in result
        mock_client._make_request.assert_called_once_with("projects/1/rights")


# ============================================================================
# Integration-Style Tests
# ============================================================================


@pytest.mark.asyncio
async def test_workflow_find_project_and_workers():
    """Test typical workflow: find project by name, then get workers."""
    with patch("src.tools.project_tools.BoondManagerClient") as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.get_projects.return_value = MOCK_PROJECT_SEARCH_RESPONSE
        mock_client.get_project_productivity.return_value = MOCK_PRODUCTIVITY_RESPONSE
        mock_client_class.return_value = mock_client

        # Step 1: Search for project
        search_result = await search_projects.ainvoke({"keywords": "alpha"})
        project_id = int(search_result["data"][0]["id"])

        # Step 2: Get workers
        workers_result = await get_project_productivity.ainvoke({"project_id": project_id})

        # Assertions
        assert len(workers_result["data"]) == 2
        assert workers_result["data"][0]["attributes"]["resource"]["lastName"] == "LEGUAY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
