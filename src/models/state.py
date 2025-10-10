"""State models for the BoondManager invoice workflow."""

from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict

from langgraph.graph import add_messages


class EmailData(TypedDict):
    """Parsed email content."""
    sender: str
    subject: str
    body_text: str
    billing_month: str  # "YYYY-MM"


class ConsultantActivity(TypedDict):
    """Consultant activity with discrepancy tracking and entity IDs."""
    # Consultant data
    consultant_name: str
    days_declared: float
    days_in_boond: Optional[float]

    # BoondManager entity IDs
    client_id: Optional[str]
    client_name: Optional[str]
    project_id: Optional[str]
    project_name: Optional[str]
    resource_id: Optional[str]
    resource_name: Optional[str]
    timesheet_id: Optional[str]

    # Discrepancy tracking
    discrepancy_amount: Optional[float]
    severity: Optional[Literal["ok", "warning", "critical"]]


class InvoiceData(TypedDict):
    """Invoice data for BoondManager API."""
    client_id: str
    billing_period: str
    total_amount: float
    boond_invoice_id: Optional[str]


class InvoiceWorkflowState(TypedDict):
    """Main workflow state container."""
    current_step: Literal[
        "email_parsing",
        "project_resolution",
        "reconciliation",
        "invoice_generation",
        "notification",
        "completed"
    ]

    email_data: Optional[EmailData]
    consultant_activities: list[ConsultantActivity]
    invoice_data: Optional[InvoiceData]

    has_discrepancies: bool
    validation_passed: bool

    errors: Annotated[list[str], add_messages]
    warnings: Annotated[list[str], add_messages]
