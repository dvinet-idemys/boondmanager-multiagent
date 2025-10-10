"""Notification node - log workflow results."""

import logging
from src.models.state import InvoiceWorkflowState

logger = logging.getLogger(__name__)


def send_notifications(state: InvoiceWorkflowState) -> InvoiceWorkflowState:
    """Log workflow results (no email sending for now).

    Args:
        state: Workflow state with invoice generation results

    Returns:
        Updated state marked as completed
    """
    logger.info("Notification node - logging workflow results")

    # Log summary
    if state.get("has_discrepancies"):
        logger.warning("Workflow completed with discrepancies")
    elif state.get("validation_passed"):
        logger.info("Workflow completed successfully")
    else:
        logger.error("Workflow completed with errors")

    state["current_step"] = "completed"
    return state
