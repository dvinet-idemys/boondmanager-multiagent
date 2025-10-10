"""Main LangGraph workflow for invoice generation."""

import logging
from langgraph.graph import StateGraph, END
from src.models.state import InvoiceWorkflowState
from src.nodes.email_parser import parse_email
from src.nodes.project_resolution import resolve_projects
from src.nodes.reconciliation import reconcile_activities
from src.nodes.validation import validate_data
from src.nodes.invoice_generation import generate_invoices
from src.nodes.notification import send_notifications

logger = logging.getLogger(__name__)


def should_continue_to_validation(state: InvoiceWorkflowState) -> str:
    """Conditional routing after reconciliation.

    Args:
        state: Current workflow state

    Returns:
        "validate" if all activities matched, "notify" if discrepancies found
    """
    if state.get("has_discrepancies"):
        logger.warning("Discrepancies found, routing to notification")
        return "notify"
    else:
        logger.info("All activities matched, continuing to validation")
        return "validate"


def create_workflow() -> StateGraph:
    """Create the invoice workflow graph with conditional branching.

    Workflow:
    1. parse_email → extract consultant activities
    2. resolve_projects → match project names to IDs
    3. reconcile → compare declared vs CRA days (FAN-OUT per consultant)
    4. IF discrepancies → notify (END)
    5. IF all match → validate → generate_invoices → notify (END)

    Returns:
        Compiled LangGraph workflow
    """
    # Create workflow graph
    workflow = StateGraph(InvoiceWorkflowState)

    # Add nodes
    workflow.add_node("parse_email", parse_email)
    workflow.add_node("resolve_projects", resolve_projects)
    workflow.add_node("reconcile", reconcile_activities)
    workflow.add_node("validate", validate_data)
    workflow.add_node("generate_invoices", generate_invoices)
    workflow.add_node("notify", send_notifications)

    # Define edges (workflow flow)
    workflow.set_entry_point("parse_email")

    # Linear flow: parse → resolve → reconcile
    workflow.add_edge("parse_email", "resolve_projects")
    workflow.add_edge("resolve_projects", "reconcile")

    # Conditional branching after reconciliation
    workflow.add_conditional_edges(
        "reconcile",
        should_continue_to_validation,
        {
            "validate": "validate",
            "notify": "notify"
        }
    )

    # Success path: validate → invoice → notify → END
    workflow.add_edge("validate", "generate_invoices")
    workflow.add_edge("generate_invoices", "notify")

    # Both paths end at notify
    workflow.add_edge("notify", END)

    return workflow.compile()


def run_invoice_workflow(raw_email_content: str) -> InvoiceWorkflowState:
    """Run the complete invoice workflow.

    Args:
        raw_email_content: Raw email text to process

    Returns:
        Final workflow state with results
    """
    # Initialize state
    initial_state: InvoiceWorkflowState = {
        "current_step": "email_parsing",
        "raw_email_content": raw_email_content,
        "email_data": None,
        "consultant_activities": [],
        "invoice_data": None,
        "has_discrepancies": False,
        "validation_passed": False,
        "errors": [],
        "warnings": []
    }

    # Create and run workflow
    workflow = create_workflow()
    final_state = workflow.invoke(initial_state)

    logger.info(f"Workflow completed with status: {final_state['current_step']}")
    return final_state


# NOTE: Fan-out for reconciliation
# ===================================
# Current skeleton: reconcile_activities processes ALL consultants sequentially
#
# For fan-out (parallel processing per consultant):
# Option 1: Use Send() API in reconcile node to spawn parallel tasks
# Option 2: Create sub-graph with map-reduce pattern
#
# Implementation approach (when ready):
# 1. In reconcile node, use Send() to dispatch each consultant to parallel workers
# 2. Workers fetch CRA data and compare independently
# 3. Collect results back into main state
#
# Example skeleton for fan-out:
# ```python
# from langgraph.types import Send
#
# def reconcile_fanout(state: InvoiceWorkflowState):
#     return [
#         Send("reconcile_worker", {"consultant": activity})
#         for activity in state["consultant_activities"]
#     ]
#
# workflow.add_conditional_edges("reconcile", reconcile_fanout)
# workflow.add_node("reconcile_worker", reconcile_single_consultant)
# ```
