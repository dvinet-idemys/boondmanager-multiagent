"""Reconciliation node - compare declared days vs BoondManager CRA."""

import logging
from src.models.state import InvoiceWorkflowState

logger = logging.getLogger(__name__)


def reconcile_activities(state: InvoiceWorkflowState) -> InvoiceWorkflowState:
    """Compare declared days against BoondManager CRA data.

    Args:
        state: Workflow state with resolved project/resource IDs

    Returns:
        Updated state with discrepancy information
    """
    logger.info("Reconciliation node - TODO: implement CRA comparison")

    # TODO: For each consultant_activity:
    # 1. Fetch CRA data from BoondManager using timesheet_id
    # 2. Compare days_declared vs days_in_boond
    # 3. Calculate discrepancy_amount
    # 4. Set severity (ok/warning/critical)
    # 5. Update has_discrepancies flag

    state["current_step"] = "invoice_generation"
    state["has_discrepancies"] = False  # TODO: actual check
    return state
