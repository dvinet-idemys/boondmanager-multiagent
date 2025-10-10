"""Invoice generation node - create invoices in BoondManager."""

import logging
from src.models.state import InvoiceWorkflowState

logger = logging.getLogger(__name__)


def generate_invoices(state: InvoiceWorkflowState) -> InvoiceWorkflowState:
    """Generate invoices in BoondManager for validated activities.

    Args:
        state: Workflow state with reconciled consultant activities

    Returns:
        Updated state with invoice data
    """
    logger.info("Invoice generation node - TODO: implement invoice creation")

    # TODO: If validation_passed:
    # 1. Group activities by client_id and billing_month
    # 2. Call BoondManager API to generate invoices
    # 3. Store invoice IDs in invoice_data
    # 4. Update state with results

    state["current_step"] = "notification"
    state["validation_passed"] = True  # TODO: actual validation
    return state
