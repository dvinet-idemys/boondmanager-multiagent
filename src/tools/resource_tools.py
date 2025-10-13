"""Resource-related tools for LangChain agents to interact with BoondManager API.

This module provides tools for querying BoondManager resource (worker) data:
- search_resources: Find resources by name or filters
- get_resource_by_id: Get resource details (placeholder for future)
"""

import logging
from typing import Any, Dict, Optional

from langchain_core.tools import tool

from src.integrations.boond_client import BoondManagerClient

logger = logging.getLogger(__name__)


@tool(parse_docstring=True)
async def search_resources(
    keywords: Optional[str] = None,
) -> Dict[str, Any]:
    """Search for resources (workers/consultants).
    Can specify search by name or keywords.

    Primary tool for finding resource IDs. Returns all resources if no arguments provided.

    Args:
        keywords: Search term (e.g., "elodie", "leguay")

    Returns:
        {
            "data": [{
                "id": "28",                                  # ⚠️ STRING, not int
                "type": "resource",
                "attributes": {
                    "firstName": "Elodie",                   # First name
                    "lastName": "Leguay",                    # Last name
                    "email": "elodie@example.com",           # Email
                    "isActive": true,                        # Active status
                    "startDate": "2020-01-15",               # Employment start
                    "phone": "+33123456789"                  # Phone
                },
                "relationships": {
                    "agency": {"data": {"id": "1"}},         # Agency assignment
                    "manager": {"data": {"id": "2"}}         # Direct manager
                }
            }]
        }

    Example:
        search_resources(keywords="elodie") → Find resource by name
        search_resources() → Find all resources
    """
    client = BoondManagerClient()
    logger.info(f"Searching resources with keywords={keywords}")

    try:
        result = await client.get_resources(keywords=keywords)
        logger.info(f"Found {len(result.get('data', []))} resources")
        return result

    except Exception as e:
        logger.error(f"Error searching resources: {e}")
        return {
            "error": str(e),
            "data": [],
            "message": "Failed to search resources.",
        }


@tool(parse_docstring=True)
async def get_resource_by_id(resource_id: int) -> Dict[str, Any]:
    """Get detailed information for a specific resource.

    Use when you have a resource ID and need detailed profile information.

    Args:
        resource_id: Unique resource identifier

    Returns:
        {
            "data": {                                        # ⚠️ OBJECT, not array
                "id": "28",
                "type": "resource",
                "attributes": {
                    "firstName": "Elodie",
                    "lastName": "Leguay",
                    "email": "elodie@example.com",
                    "isActive": true,
                    "startDate": "2020-01-15",
                    "phone": "+33123456789",
                    "skillLevel": 3                          # Skill/seniority level
                },
                "relationships": {
                    "agency": {"data": {"id": "1"}},
                    "manager": {"data": {"id": "2"}},
                    "team": {"data": {"id": "5"}}
                }
            }
        }

    Example:
        get_resource_by_id(resource_id=28) → Get resource 28 details
    """
    client = BoondManagerClient()
    logger.info(f"Fetching resource {resource_id}")

    try:
        result = await client._make_request(f"resources/{resource_id}")
        logger.info(f"Successfully fetched resource {resource_id}")
        return result

    except Exception as e:
        logger.error(f"Error fetching resource {resource_id}: {e}")
        return {
            "error": str(e),
            "data": None,
            "message": f"Failed to fetch resource {resource_id}.",
        }
