"""BoondManager API client for invoice workflow automation."""

import logging
from typing import Any, Optional
from urllib.parse import urljoin

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.integrations.auth import new_token
from src.config import config

logger = logging.getLogger(__name__)

# API Base URL
API_BASE = "https://ui.boondmanager.com/api/"


class BoondManagerClient:
    """Async HTTP client for BoondManager API with retry logic."""

    def __init__(self):
        self.base_url = API_BASE
        self.timeout = 30.0

    def _get_headers(self) -> dict[str, str]:
        """Generate authentication headers with JWT token."""
        return {
            "Accept": "application/json",
            "X-Jwt-Client-BoondManager": new_token(mode="god"),
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def _make_request(self, uri: str, method: str = "GET", **kwargs) -> dict[str, Any]:
        """Make authenticated request to BoondManager API with retry logic.

        Args:
            uri: API endpoint path
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional httpx request parameters

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPStatusError: On HTTP error responses
            httpx.TimeoutException: On request timeout (after retries)
        """
        headers = self._get_headers()
        url = urljoin(self.base_url, uri)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(f"BoondManager API: {method} {url}")
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()

    # ========================================================================
    # Project Management
    # ========================================================================

    async def get_projects(self, company_id: Optional[int] = None) -> dict[str, Any]:
        """Fetch projects, optionally filtered by company.

        Used for client_id resolution by matching project names from emails.

        Args:
            company_id: Optional company ID to filter projects

        Returns:
            Projects data with structure:
            {
                "data": [
                    {
                        "id": "project-123",
                        "attributes": {"name": "Project Alpha"},
                        "relationships": {
                            "company": {"data": {"id": "client-456"}}
                        }
                    }
                ]
            }
        """
        if company_id is None:
            uri = "projects"
        else:
            uri = f"projects?companies={company_id}"

        return await self._make_request(uri)

    async def get_project_productivity(self, project_id: int) -> dict[str, Any]:
        """Get productivity data for a project.

        Productivity = units of work within a project, includes resource assignments.

        Args:
            project_id: Project ID

        Returns:
            Productivity data including resource assignments and timesheet IDs
        """
        return await self._make_request(f"projects/{project_id}/productivity")

    async def get_project_deliveries(self, project_id: int) -> dict[str, Any]:
        """Get deliveries for a project.

        Deliveries = work done by individual workers on a project.
        Contains daily rates and worker assignments.

        Args:
            project_id: Project ID

        Returns:
            Deliveries data with worker info and daily rates
        """
        return await self._make_request(f"projects/{project_id}/deliveries-groupments")

    # ========================================================================
    # Timesheet / CRA Management
    # ========================================================================

    async def get_times_report(self, timesreport_id: int) -> dict[str, Any]:
        """Get timesheet/CRA data by ID.

        Used for reconciliation to compare declared days vs actual CRA entries.

        Args:
            timesreport_id: Timesheet report ID

        Returns:
            Timesheet data with worked days breakdown
        """
        return await self._make_request(f"times-reports/{timesreport_id}")

    # ========================================================================
    # Order Management
    # ========================================================================

    async def get_project_orders(self, project_id: int) -> dict[str, Any]:
        """Get orders for a project.

        Orders = client work orders for billing periods.

        Args:
            project_id: Project ID

        Returns:
            Order data for the project
        """
        return await self._make_request(f"projects/{project_id}/orders")

    async def get_order_info(self, order_id: int) -> dict[str, Any]:
        """Get detailed order information.

        Args:
            order_id: Order ID

        Returns:
            Detailed order data including worker assignments
        """
        return await self._make_request(f"orders/{order_id}/information")

    # ========================================================================
    # Invoice Generation
    # ========================================================================

    async def generate_invoice(self, month: str, project_id: int) -> dict[str, Any]:
        """Generate invoice using PostProduction.

        Args:
            month: Target month in format "YYYY-MM"
            project_id: Project ID

        Returns:
            Invoice generation response with invoice ID

        Example:
            >>> client = BoondManagerClient()
            >>> result = await client.generate_invoice("2025-10", 123)
        """
        uri = f"apps/post-production/projects?month={month}&keywords=PRJ{project_id}&generateInvoices=true"
        return await self._make_request(uri)

    # ========================================================================
    # Resource Management
    # ========================================================================

    async def get_resources(self, keywords: Optional[str] = None) -> dict[str, Any]:
        """Fetch resources (workers/consultants), optionally filtered by keywords.

        Resources = workers, consultants, or employees who can be assigned to projects.

        Args:
            keywords: Optional search term (name, email, etc.)

        Returns:
            Resources data with structure:
            {
                "data": [
                    {
                        "id": "28",
                        "attributes": {
                            "firstName": "Elodie",
                            "lastName": "Leguay",
                            "email": "elodie@example.com",
                            "isActive": true
                        }
                    }
                ]
            }
        """
        if keywords:
            uri = f"resources?keywords={keywords}"
        else:
            uri = "resources"
        return await self._make_request(uri)

    # ========================================================================
    # Contact Management
    # ========================================================================

    async def get_contacts(self) -> dict[str, Any]:
        """Fetch contacts.

        Contacts = human links to client companies (e.g., sales reps).

        Returns:
            Contact data with emails and company associations
        """
        return await self._make_request("contacts")
