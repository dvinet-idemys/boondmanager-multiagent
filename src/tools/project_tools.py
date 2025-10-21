"""Project-related tools for LangChain agents to interact with BoondManager API.

This module provides 4 essential tools for querying BoondManager project data:
- search_projects: Find projects by name or filters
- get_project_by_id: Get project details
- get_project_productivity: Get workers and timesheets (CRITICAL: uses included[] array)
- get_project_orders: Get billing and order information
"""

import logging
from typing import Any, Dict, Optional

from langchain_core.tools import tool

from src.integrations.boond_client import BoondManagerClient

logger = logging.getLogger(__name__)


@tool(parse_docstring=True)
async def search_projects(
    keywords: Optional[str] = None,
    company_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Search for projects.
    Can specify search by name, keywords, or company id.

    Primary tool for finding project IDs. Returns all projects if no arguments provided.

    Args:
        keywords: Search term (e.g., "alpha", "modernisation")
        company_id: company ID to filter by client

    Returns:
        {
            "data": [{
                "id": "8",                                    # ⚠️ STRING, not int
                "attributes": {
                    "reference": "Project Name",              # Project name here
                    "startDate": "2025-09-01",
                    "endDate": "2025-12-31"
                },
                "relationships": {
                    "company": {"data": {"id": "5"}},         # Client company
                    "mainManager": {"data": {"id": "2"}}      # Project manager
                }
            }]
        }

    Example:
        search_projects(keywords="alpha") → Find project by name
        search_projects(company_id=5) → Find all projects for company 5
    """
    client = BoondManagerClient()
    logger.info(f"Searching projects with keywords={keywords}, company={company_id}")

    try:
        if company_id:
            result = await client.get_projects(company_id=company_id)
        else:
            result = await client.get_projects()

        logger.info(f"Found {len(result.get('data', []))} projects")
        return result

    except Exception as e:
        logger.error(f"Error searching projects: {e}")
        return {
            "error": str(e),
            "data": [],
            "message": "Failed to search projects.",
        }


@tool(parse_docstring=True)
async def get_project_by_id(project_id: int) -> Dict[str, Any]:
    """Get detailed information for a specific project.

    Use when you have a project ID and need its details.

    Args:
        project_id: Unique project identifier

    Returns:
        {
            "data": {                                        # ⚠️ OBJECT, not array
                "id": "8",
                "attributes": {
                    "reference": "Project Name",
                    "startDate": "2025-09-01",
                    "typeOf": 1,                             # Project type
                    "mode": 1,                               # Project mode
                    "workUnitRate": 1,                       # Work unit conversion
                    "exchangeRate": 1
                },
                "relationships": {
                    "company": {"data": {"id": "5"}},
                    "mainManager": {"data": {"id": "2"}}
                }
            }
        }

    Example:
        get_project_by_id(project_id=8) → Get project 8 details
    """
    client = BoondManagerClient()
    logger.info(f"Fetching project {project_id}")

    try:
        result = await client._make_request(f"projects/{project_id}")
        logger.info(f"Successfully fetched project {project_id}")
        return result

    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {e}")
        return {
            "error": str(e),
            "data": None,
            "message": f"Failed to fetch project {project_id}.",
        }


@tool(parse_docstring=True)
async def get_project_productivity(project_id: int) -> Dict[str, Any]:
    """Get workers, timesheets, and work done on a project.

    ⚠️ CRITICAL: Worker names are in included[], NOT data[]!
    The data[] array contains delivery records with worker ID references.
    You must lookup worker details in included[] array.

    Args:
        project_id: Unique project identifier

    Returns:
        {
            "data": [{                                       # Delivery records
                "id": "18",
                "type": "delivery",
                "attributes": {
                    "regularTimesProduction": 12,            # Days worked (entire order period, all workers)
                    "costsProductionExcludingTax": 6660,     # Cost (entire period)
                    "turnoverProductionExcludingTax": 7860   # Revenue (entire period)
                },
                "relationships": {
                    "dependsOn": {
                        "data": {"id": "28", "type": "resource"}  # → Worker ID
                    },
                    "timesReports": {
                        "data": [{"id": "5", "type": "timesreport"}]  # → Timesheet ID
                    }
                }
            }],
            "included": [{                                   # ⚠️ Worker details HERE!
                "id": "28",
                "type": "resource",
                "attributes": {
                    "firstName": "Elodie",                   # Worker first name
                    "lastName": "Leguay"                     # Worker last name
                }
            }]
        }

    Note: Amounts are for the entire project period, not current month.

    Parsing:
        1. For each delivery in data[]
        2. Get worker_id from relationships.dependsOn.data.id
        3. Find worker in included[] where id=worker_id
        4. Extract worker.attributes.{firstName, lastName}

    Example:
        get_project_productivity(project_id=8) → Get workers on project 8
    """
    client = BoondManagerClient()
    logger.info(f"Fetching productivity for project {project_id}")

    try:
        result = await client.get_project_productivity(project_id)
        logger.info(f"Successfully fetched productivity for project {project_id}")
        return result

    except Exception as e:
        logger.error(f"Error fetching productivity for project {project_id}: {e}")
        return {
            "error": str(e),
            "data": None,
            "message": f"Failed to fetch productivity for project {project_id}.",
        }


@tool(parse_docstring=True)
async def get_project_orders(project_id: int) -> Dict[str, Any]:
    """Get orders and billing information for a project.

    Use to retrieve work orders, invoicing status, and financial tracking.

    Args:
        project_id: Unique project identifier

    Returns:
        {
            "data": [{
                "id": "11",
                "attributes": {
                    "number": "CMD2",                             # Order number
                    "reference": "BM1000000000011",               # BM reference
                    "date": "2025-09-24",
                    "startDate": "2025-09-15",
                    "endDate": "2025-12-31",
                    "turnoverOrderedExcludingTax": 49780,        # Total
                    "turnoverInvoicedExcludingTax": 7860,         # Invoiced
                    "deltaInvoicedExcludingTax": -41920,          # Remaining
                    "state": 1                                    # Order state
                }
            }]
        }

    Note: Amounts in units of currency (7860 = 7 860€). Negative delta = remaining to invoice.
    Note: Amounts are for the entire project period, not current month.

    Example:
        get_project_orders(project_id=8) → Get all orders for project 8
    """
    client = BoondManagerClient()
    logger.info(f"Fetching orders for project {project_id}")

    try:
        result = await client.get_project_orders(project_id)
        logger.info(f"Successfully fetched orders for project {project_id}")
        return result

    except Exception as e:
        logger.error(f"Error fetching orders for project {project_id}: {e}")
        return {
            "error": str(e),
            "data": None,
            "message": f"Failed to fetch orders for project {project_id}.",
        }


@tool(parse_docstring=True)
async def get_project_deliveries(project_id: int) -> dict[str, Any]:
    """
    Deliveries are units of work done by one worker on one project. Use this tool to list all deliveries for one project.

    Deliveries are stored in the "data" array. For each delivery, you can find the associated worker by their id in the
    "relationships.dependsOn.data" tag. The average daily price of the delivery can change per worker and is found in the
    "averageDailyPriceExcludingTax" tag. You can find which worker is referenced by the ids in the "included" tag.

    Args:
        project_id: int: id of the project, as specified by the get_projects tool
    """

    client = BoondManagerClient()
    logger.info(f"Fetching deliveries for project {project_id}")

    try:
        result = await client.get_project_deliveries(project_id)
        logger.info(f"Successfully fetched deliveries for project {project_id}")
        return result

    except Exception as e:
        logger.error(f"Error fetching deliveries for project {project_id}: {e}")
        return {
            "error": str(e),
            "data": None,
            "message": f"Failed to fetch deliveries for project {project_id}.",
        }
