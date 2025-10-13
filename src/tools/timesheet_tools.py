"""Timesheet-related tools for LangChain agents to interact with BoondManager API.

This module provides 2 essential tools for querying BoondManager timesheet data:
- get_resource_timesheets: Get all timesheets for a specific worker
- get_timesheet_by_id: Get detailed timesheet with daily entries
"""

import logging
from typing import Any, Dict

from langchain_core.tools import tool

from src.integrations.boond_client import BoondManagerClient

logger = logging.getLogger(__name__)


@tool(parse_docstring=True)
async def get_resource_timesheets(resource_id: int) -> Dict[str, Any]:
    """Get all timesheets for a specific worker/resource.

    Use when you need to find timesheets for a worker by their ID.

    Args:
        resource_id: Worker/resource identifier (e.g., from productivity endpoint)

    Returns:
        {
            "data": [{
                "id": "5",                                    # Timesheet ID
                "type": "timesreport",
                "attributes": {
                    "term": "2025-09",                        # Period (YYYY-MM)
                    "state": "validated",                     # State (validated/pending/rejected)
                    "closed": false,                          # Is timesheet closed?
                    "creationDate": "2025-09-24T15:33:48+0200",
                    "updateDate": "2025-09-24T15:34:46+0200"
                },
                "relationships": {
                    "resource": {"data": {"id": "28"}},       # Worker ID
                    "projects": {"data": [{"id": "8"}]}       # Projects worked on
                }
            }]
        }

    Example:
        get_resource_timesheets(resource_id=28) → Get all timesheets for worker 28
    """
    client = BoondManagerClient()
    logger.info(f"Fetching timesheets for resource {resource_id}")

    try:
        result = await client._make_request(f"resources/{resource_id}/timesreports")
        logger.info(
            f"Successfully fetched {len(result.get('data', []))} timesheets for resource {resource_id}"
        )
        return result

    except Exception as e:
        logger.error(f"Error fetching timesheets for resource {resource_id}: {e}")
        return {
            "error": str(e),
            "data": [],
            "message": f"Failed to fetch timesheets for resource {resource_id}.",
        }


@tool(parse_docstring=True)
async def get_timesheet_by_id(timesheet_id: int) -> Dict[str, Any]:
    """Get detailed timesheet with daily time entries.

    ⚠️ CRITICAL: Daily entries are in attributes.regularTimes[], NOT in data[]!
    Each entry contains project, delivery, date, and duration information.

    Args:
        timesheet_id: Unique timesheet identifier

    Returns:
        {
            "data": {                                        # Single object, not array
                "id": "5",
                "attributes": {
                    "term": "2025-09",                       # Period (YYYY-MM)
                    "state": "validated",                    # Validation state
                    "closed": false,                         # Is timesheet locked?
                    "regularTimes": [{                       # ⚠️ Daily entries HERE!
                        "id": "75",
                        "startDate": "2025-09-15",           # Work date
                        "duration": 1,                       # Days worked (1 = 1 day)
                        "workUnitType": {
                            "activityType": "production",    # Type: production/internal/absence
                            "name": "Normale"
                        },
                        "project": {
                            "id": "8",                       # Project ID
                            "reference": "Project Name"      # Project name
                        },
                        "delivery": {
                            "id": "18",                      # Delivery/assignment ID
                            "startDate": "2025-09-15",
                            "endDate": "2025-12-31"
                        }
                    }],
                    "exceptionalTimes": [],                  # Overtime entries
                    "absencesTimes": []                      # Absence entries
                },
                "relationships": {
                    "resource": {"data": {"id": "28"}},      # Worker ID
                    "projects": {"data": [{"id": "8"}]},     # All projects in timesheet
                    "orders": {"data": [{"id": "11"}]}       # Related orders
                }
            },
            "included": [{                                   # Related entities
                "id": "28",
                "type": "resource",
                "attributes": {
                    "firstName": "Elodie",
                    "lastName": "Leguay"
                }
            }]
        }

    Note: Daily entries show individual work days for the month/period.

    Parsing:
        1. Get worker ID from data.relationships.resource.data.id
        2. Iterate through data.attributes.regularTimes[]
        3. Each entry has: startDate (work day), duration (days), project info
        4. Filter by activityType: "production" = client work, "internal" = non-billable

    Example:
        get_timesheet_by_id(timesheet_id=5) → Get detailed timesheet 5 with daily entries
    """
    client = BoondManagerClient()
    logger.info(f"Fetching timesheet {timesheet_id}")

    try:
        result = await client._make_request(f"timesreports/{timesheet_id}")
        logger.info(f"Successfully fetched timesheet {timesheet_id}")
        return result

    except Exception as e:
        logger.error(f"Error fetching timesheet {timesheet_id}: {e}")
        return {
            "error": str(e),
            "data": None,
            "message": f"Failed to fetch timesheet {timesheet_id}.",
        }
