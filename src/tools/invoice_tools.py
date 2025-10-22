"""Invoice-related tools for LangChain agents to interact with BoondManager API.

This module provides 3 essential tools for querying BoondManager invoice data:
- search_invoices: Find invoices by project, order, company, or contact
- get_invoice_by_id: Get basic invoice data
- get_invoice_information: Get detailed invoice information with line items
"""

import logging
from typing import Any, Dict, Optional

from langchain_core.tools import tool

from src.integrations.boond_client import BoondManagerClient

logger = logging.getLogger(__name__)


@tool(parse_docstring=True)
async def search_invoices(
    invoice_id: Optional[int] = None,
    order_id: Optional[int] = None,
    project_id: Optional[int] = None,
    contact_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Search for invoices by ID filters.

    Primary tool for finding invoices. All parameters are optional.
    Use this when you need to find invoices related to projects, orders, or companies.

    Args:
        invoice_id (optional): Specific invoice ID to search for
        order_id (optional): Find invoices related to a specific order
        project_id (optional): Find invoices for a specific project
        contact_id (optional): Find invoices for a specific contact
        company_id (optional): Find invoices for a specific company

    Returns:
        {
            "data": [{
                "id": "123",                                    # ⚠️ STRING, not int
                "type": "invoice",
                "attributes": {
                    "reference": "FACT-2025-001",              # Invoice reference number
                    "date": "2025-10-14",                      # Invoice date
                    "state": {...},                            # Invoice state (draft/validated/etc)
                    "closed": false,                           # Is invoice closed?
                    "totalExcludingTax": 5000.00,             # Amount excl. tax
                    "totalIncludingTax": 6000.00,             # Amount incl. tax
                    "totalPayableIncludingTax": 6000.00,      # Total to pay
                    "expectedPaymentDate": "2025-11-14",      # Expected payment date
                    "performedPaymentDate": null,             # Actual payment date (if paid)
                    "startDate": "2025-09-01",                # Billing period start
                    "endDate": "2025-09-30"                   # Billing period end
                },
                "relationships": {
                    "project": {"data": {"id": "8"}},         # Related project
                    "order": {"data": {"id": "11"}},          # Related order
                    "company": {"data": {"id": "5"}}          # Client company
                }
            }],
            "meta": {
                "pagination": {
                    "page": 1,
                    "totalPages": 5,
                    "totalResults": 142
                }
            }
        }

    Note: Amounts are in currency units (5000.00 = 5 000€).

    Example:
        search_invoices(project_id=8) → Find all invoices for project 8
        search_invoices(company_id=5) → Find all invoices for company 5
        search_invoices(order_id=11) → Find invoices for order 11
        search_invoices() → Find all invoices
    """
    client = BoondManagerClient()
    logger.info(
        f"Searching invoices with filters: invoice={invoice_id}, order={order_id}, "
        f"project={project_id}, contact={contact_id}, company={company_id}"
    )

    try:
        result = await client.search_invoices(
            invoice_id=invoice_id,
            order_id=order_id,
            project_id=project_id,
            contact_id=contact_id,
            company_id=company_id,
        )
        logger.info(f"Found {len(result.get('data', []))} invoices")
        return result

    except Exception as e:
        logger.error(f"Error searching invoices: {e}")
        return {
            "error": str(e),
            "data": [],
            "message": "Failed to search invoices.",
        }


@tool(parse_docstring=True)
async def get_invoice_by_id(invoice_id: int) -> Dict[str, Any]:
    """Get basic invoice data by ID.

    Use when you have an invoice ID and need its basic information.
    For detailed information including line items, use get_invoice_information instead.

    Args:
        invoice_id: Unique invoice identifier

    Returns:
        {
            "data": {                                        # ⚠️ OBJECT, not array
                "id": "123",
                "type": "invoice",
                "attributes": {
                    "reference": "FACT-2025-001",           # Invoice reference
                    "date": "2025-10-14",                   # Invoice date
                    "state": {...},                         # Invoice state
                    "closed": false,                        # Is closed?
                    "totalExcludingTax": 5000.00,          # Amount excl. tax
                    "totalIncludingTax": 6000.00,          # Amount incl. tax
                    "totalPayableIncludingTax": 6000.00,   # Total to pay
                    "expectedPaymentDate": "2025-11-14",
                    "performedPaymentDate": null,
                    "startDate": "2025-09-01",             # Billing period start
                    "endDate": "2025-09-30"                # Billing period end
                },
                "relationships": {
                    "project": {"data": {"id": "8"}},
                    "order": {"data": {"id": "11"}},
                    "company": {"data": {"id": "5"}},
                    "mainManager": {"data": {"id": "2"}}   # Invoice manager
                }
            }
        }

    Example:
        get_invoice_by_id(invoice_id=123) → Get basic data for invoice 123
    """
    client = BoondManagerClient()
    logger.info(f"Fetching invoice {invoice_id}")

    try:
        result = await client.get_invoice(invoice_id)
        logger.info(f"Successfully fetched invoice {invoice_id}")
        return result

    except Exception as e:
        logger.error(f"Error fetching invoice {invoice_id}: {e}")
        return {
            "error": str(e),
            "data": None,
            "message": f"Failed to fetch invoice {invoice_id}.",
        }


@tool(parse_docstring=True)
async def get_invoice_information(invoice_id: int) -> Dict[str, Any]:
    """Get detailed invoice information including line items, payments, and documents.

    ⚠️ CRITICAL: This provides MUCH MORE detail than get_invoice_by_id!
    Use this when you need:
    - Line items with quantities and prices
    - Payment information and history
    - Attached documents
    - Tax breakdown
    - Custom fields

    Args:
        invoice_id: Unique invoice identifier

    Returns:
        {
            "data": {
                "id": "123",
                "type": "invoice",
                "attributes": {
                    "reference": "FACT-2025-001",
                    "date": "2025-10-14",
                    "state": {...},
                    "closed": false,
                    "totalExcludingTax": 5000.00,
                    "totalIncludingTax": 6000.00,
                    "lines": [{                             # ⚠️ Line items HERE!
                        "id": "456",
                        "label": "Development services",    # Line item description
                        "quantity": 10,                     # Quantity
                        "unitPrice": 500.00,               # Unit price excl. tax
                        "totalExcludingTax": 5000.00,      # Line total excl. tax
                        "vatRate": 20                       # VAT rate %
                    }],
                    "payments": [{                          # Payment history
                        "date": "2025-11-15",
                        "amount": 6000.00,
                        "method": "Bank transfer"
                    }],
                    "documents": [{                         # Attached documents
                        "id": "789",
                        "name": "invoice.pdf",
                        "url": "https://..."
                    }]
                },
                "relationships": {
                    "project": {"data": {"id": "8"}},
                    "order": {"data": {"id": "11"}},
                    "company": {"data": {"id": "5"}},
                    "timesReports": {                       # Related timesheets
                        "data": [{"id": "5", "type": "timesreport"}]
                    }
                }
            },
            "included": [{                                  # Related entities
                "id": "5",
                "type": "company",
                "attributes": {
                    "name": "Client Corp",
                    "address": "123 Main St"
                }
            }]
        }

    Note: Line items show individual billing lines with quantities and prices.
          Use this endpoint for detailed invoice analysis and reconciliation.

    Example:
        get_invoice_information(invoice_id=123) → Get full details for invoice 123
    """
    client = BoondManagerClient()
    logger.info(f"Fetching detailed information for invoice {invoice_id}")

    try:
        result = await client.get_invoice_information(invoice_id)
        logger.info(f"Successfully fetched detailed information for invoice {invoice_id}")
        return result

    except Exception as e:
        logger.error(f"Error fetching detailed invoice information for {invoice_id}: {e}")
        return {
            "error": str(e),
            "data": None,
            "message": f"Failed to fetch detailed information for invoice {invoice_id}.",
        }


@tool(parse_docstring=True)
async def generate_invoice(
    month: str,
    project_id: int,
    delivery_id: Optional[int] = None,
    resource_id: Optional[int] = None,
    contact_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Generate invoices for a project in a specific month using PostProduction.

    ⚠️ CRITICAL: This creates new invoices in BoondManager!
    Use this tool to generate invoices after validating:
    - Timesheet data is validated
    - Business rules are satisfied
    - All required entities exist

    CRITICAL: Always check the generated invoices after calling this tool. Give
    a recap of the generated invoices, don't just return "Success".

    This endpoint triggers invoice generation and returns project data with updated
    production and invoicing information.

    Args:
        month: Target month in format "YYYY-MM" (required, e.g., "2025-10")
        project_id: Project unique identifier (required)
        delivery_id: Filter by delivery unique identifier (optional)
        resource_id: Filter by resource/consultant unique identifier (optional)
        contact_id: Filter by contact unique identifier (optional)
        company_id: Filter by company unique identifier (optional)

    Returns:
        {
            "meta": {
                "version": "4.0.0",
                "isLogged": true,
                "language": "en",
                "totals": {"rows": 1}                      # Number of projects
            },
            "data": [{
                "id": "8",                                 # Project ID (string)
                "type": "apppostproductionproject",
                "attributes": {
                    "reference": "Project Alpha",          # Project name
                    "turnoverProductionExcludingTax": 12000.00,  # Production amount
                    "turnoverInvoicedExcludingTax": 12000.00,    # Invoiced amount
                    "productionTerm": "2025-10",           # Billing month
                    "numberOfOrders": 1,                   # Related orders count
                    "canGenerateInvoices": true,           # Invoice generation allowed (false if not all necessary info present)
                    "productionComments": "..."            # Generation notes
                },
                "relationships": {
                    "company": {
                        "data": {"id": "5", "type": "company"}  # Client company
                    },
                    "deliveries": {
                        "data": [{                         # Related deliveries
                            "id": "1",
                            "type": "apppostproductiondelivery"
                        }]
                    }
                }
            }],
            "included": [{                                 # Related entities
                "id": "5",
                "type": "company",
                "attributes": {"name": "Client Corp"}
            }]
        }

    Note: Amounts are in currency units (12000.00 = 12 000€).
          The actual invoice IDs must be retrieved via search_invoices after generation.
          This endpoint returns project post-production data, not invoice objects directly.

    Example:
        generate_invoice(month="2025-10", project_id=8)
        → Generate invoices for project 8 in October 2025

        generate_invoice(month="2025-10", project_id=8, resource_id=28)
        → Generate invoices for specific consultant on project 8
    """
    client = BoondManagerClient()

    try:
        result = await client.generate_invoice(
            month=month,
            project_id=project_id,
            delivery_id=delivery_id,
            resource_id=resource_id,
            contact_id=contact_id,
            company_id=company_id,
        )

        return result
    except Exception as e:
        logger.error(f"Error generating invoice: {e}")
        return {
            "error": str(e),
            "data": [],
            "message": f"Failed to generate invoice for project {project_id} in {month}.",
        }
