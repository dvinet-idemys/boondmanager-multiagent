"""BoondManager API client for invoice workflow automation."""

import logging
from typing import Any, Optional
from urllib.parse import urljoin

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import config
from src.integrations.auth import new_token

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

        Used for verification to compare declared days vs actual CRA entries.

        Args:
            timesreport_id: Timesheet report ID

        Returns:
            Timesheet data with worked days breakdown
        """
        return await self._make_request(f"times-reports/{timesreport_id}")

    async def validate_timesheet(
        self, timesheet_id: int, expected_validator_id: int
    ) -> dict[str, Any]:
        """Validate a timesheet for a specific resource.

        This endpoint validates a pending timesheet, marking it as approved
        by the expected validator (manager/supervisor).

        Args:
            timesheet_id: Unique timesheet identifier to validate
            expected_validator_id: Resource ID of the validator (manager who approves)

        Returns:
            Validated timesheet data with warnings and validation metadata:
            {
                "meta": {
                    "version": "...",
                    "warnings": [
                        {
                            "code": "moreThanNumberOfWorkingDays",
                            "detail": "Warning message",
                            "project": {"id": "123", "reference": "PRJ-ABC"},
                            "delivery": {"id": "456", ...}
                        }
                    ],
                    "expectedValidatorsAllowedForValidate": [...],
                    "expectedValidatorsAllowedForUnvalidate": [...],
                    "expectedValidatorsAllowedForReject": [...]
                },
                "data": {
                    "id": "5",
                    "type": "timesreport",
                    "attributes": {
                        "term": "2025-09",
                        "state": "validated",
                        "closed": false
                    }
                }
            }

        Warning codes include:
            - moreThanNumberOfWorkingDays: Over expected work days
            - workplaceTimesMoreThanNumberOfWorkingDays: Workplace hours exceeded
            - noDeliveryOnProject: Missing delivery assignment
            - outsideContractDates: Work outside contract period
            - noSignedTimesheet: Timesheet not signed by worker
        """
        uri = f"times-reports/{timesheet_id}/validate?expectedValidator={expected_validator_id}"
        return await self._make_request(uri, method="POST")

    async def unvalidate_timesheet(
        self, timesheet_id: int, expected_validator_id: int
    ) -> dict[str, Any]:
        """Unvalidate (revoke approval of) a previously validated timesheet.

        This endpoint unvalidates a timesheet, reverting it from "validated" state
        back to "pending" state. Useful for corrections or when validation was done in error.

        Args:
            timesheet_id: Unique timesheet identifier to unvalidate
            expected_validator_id: Resource ID of the validator (manager who revokes)

        Returns:
            Unvalidated timesheet data with warnings and validation metadata:
            {
                "meta": {
                    "version": "...",
                    "warnings": [...],
                    "expectedValidatorsAllowedForValidate": [...],
                    "expectedValidatorsAllowedForUnvalidate": [...],
                    "expectedValidatorsAllowedForReject": [...]
                },
                "data": {
                    "id": "5",
                    "type": "timesreport",
                    "attributes": {
                        "term": "2025-09",
                        "state": "pending",  # State changed back to pending
                        "closed": false
                    }
                }
            }

        Note: Unvalidating a timesheet may block invoicing workflows that depend
        on validated timesheets. Use when corrections are needed before billing.
        """
        uri = f"times-reports/{timesheet_id}/unvalidate?expectedValidator={expected_validator_id}"
        return await self._make_request(uri, method="POST")

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

    async def generate_invoice(
        self,
        month: str,
        project_id: int,
        delivery_id: Optional[int] = None,
        resource_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        company_id: Optional[int] = None,
        opportunity_id: Optional[int] = None,
        product_id: Optional[int] = None,
        contract_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Generate invoice using PostProduction with advanced filtering.

        This endpoint generates invoices for post-production projects with multiple
        filtering options. Each keyword parameter corresponds to a specific entity
        type that can filter the results.

        Args:
            month: Target month in format "YYYY-MM" (required)
            project_id: Project unique identifier (required)
            delivery_id: Filter by delivery unique identifier (optional)
            resource_id: Filter by resource unique identifier (optional)
            contact_id: Filter by contact unique identifier (optional)
            company_id: Filter by company unique identifier (optional)
            opportunity_id: Filter by opportunity unique identifier (optional)
            product_id: Filter by product unique identifier (optional)
            contract_id: Filter by contract unique identifier (optional)

        Returns:
            Invoice generation response with invoice ID

        Example:
            >>> client = BoondManagerClient()
            >>> # Generate invoice for specific project
            >>> result = await client.generate_invoice("2025-10", 123)
            >>>
            >>> # Generate invoice with additional filters
            >>> result = await client.generate_invoice(
            ...     month="2025-10", project_id=123, company_id=456, contact_id=789
            ... )
        """
        # Build keywords parameter from all ID filters
        keywords_parts = [f"PRJ{project_id}"]  # project_id is mandatory

        if delivery_id:
            keywords_parts.append(f"MIS{delivery_id}")
        if resource_id:
            keywords_parts.append(f"COMP{resource_id}")
        if contact_id:
            keywords_parts.append(f"CCON{contact_id}")
        if company_id:
            keywords_parts.append(f"CSOC{company_id}")
        if opportunity_id:
            keywords_parts.append(f"AO{opportunity_id}")
        if product_id:
            keywords_parts.append(f"PROD{product_id}")
        if contract_id:
            keywords_parts.append(f"CTR{contract_id}")

        # Build query parameters
        keywords = " ".join(keywords_parts)
        uri = (
            f"apps/post-production/projects?month={month}&keywords={keywords}&generateInvoices=true"
        )

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

    # ========================================================================
    # Invoice Management
    # ========================================================================

    async def search_invoices(
        self,
        invoice_id: Optional[int] = None,
        order_id: Optional[int] = None,
        project_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        company_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Search invoices by ID filters.

        Args:
            invoice_id: Filter by specific invoice ID
            order_id: Filter by order ID
            project_id: Filter by project ID
            contact_id: Filter by contact ID
            company_id: Filter by company ID

        Returns:
            Invoice search results

        Example:
            >>> # Search all invoices for a project
            >>> result = await client.search_invoices(project_id=123)
            >>>
            >>> # Search invoices for a company
            >>> result = await client.search_invoices(company_id=456)
        """
        params = {}

        # Build keywords parameter from ID filters
        keywords_parts = []
        if invoice_id:
            keywords_parts.append(f"FACT{invoice_id}")
        if order_id:
            keywords_parts.append(f"BDC{order_id}")
        if project_id:
            keywords_parts.append(f"PRJ{project_id}")
        if contact_id:
            keywords_parts.append(f"CCON{contact_id}")
        if company_id:
            keywords_parts.append(f"CSOC{company_id}")

        if keywords_parts:
            params["keywords"] = " ".join(keywords_parts)

        return await self._make_request("invoices", params=params)

    async def get_invoice(self, invoice_id: int) -> dict[str, Any]:
        """Get basic invoice data by ID.

        Args:
            invoice_id: Invoice unique identifier

        Returns:
            Invoice basic data including reference, dates, amounts, and relationships
        """
        return await self._make_request(f"invoices/{invoice_id}")

    async def get_invoice_information(self, invoice_id: int) -> dict[str, Any]:
        """Get detailed invoice information (much more detailed than basic).

        Args:
            invoice_id: Invoice unique identifier

        Returns:
            Detailed invoice data with line items, payments, documents, and full details
        """
        return await self._make_request(f"invoices/{invoice_id}/information")
