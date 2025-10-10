"""AI-powered email parsing node using LLM for extraction."""

import logging
from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage

from src.models.state import InvoiceWorkflowState, EmailData, ConsultantActivity
from src.llm_config import get_llm

logger = logging.getLogger(__name__)


def parse_email(state: InvoiceWorkflowState) -> InvoiceWorkflowState:
    """Parse email using LLM to extract billing data and consultant activities.

    Args:
        state: Workflow state (expects raw_email_content)

    Returns:
        Updated state with parsed email_data and consultant_activities
    """
    raw_email = state.get("raw_email_content", "")

    if not raw_email:
        state["errors"].append("No email content provided")
        state["current_step"] = "completed"
        return state

    try:
        # Initialize LLM
        llm = get_llm()

        # Extract email metadata
        email_data = _extract_metadata_with_llm(llm, raw_email)

        # Extract consultant activities
        consultant_activities = _extract_activities_with_llm(llm, raw_email)

        # Update state
        state["email_data"] = email_data
        state["consultant_activities"] = consultant_activities
        state["current_step"] = "project_resolution"

        logger.info(f"Parsed email: {len(consultant_activities)} consultants found")

    except Exception as e:
        logger.error(f"Email parsing failed: {e}")
        state["errors"].append(f"Email parsing error: {str(e)}")
        state["current_step"] = "completed"

    return state


def _extract_metadata_with_llm(llm, raw_email: str) -> EmailData:
    """Extract email metadata using LLM.

    Args:
        llm: LangChain LLM instance
        raw_email: Raw email content

    Returns:
        EmailData with sender, subject, billing_month
    """
    system_prompt = """You are an email metadata extractor. Extract the following information from the email:
1. Sender email address (from "From:" header)
2. Subject line (from "Subject:" header)
3. Billing month in YYYY-MM format (extract from subject, e.g., "Octobre 2025" -> "2025-10")

Return ONLY a JSON object with these exact keys: sender, subject, billing_month"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=raw_email)
    ]

    response = llm.invoke(messages)

    # Parse JSON response
    import json
    result = json.loads(response.content)

    return EmailData(
        sender=result["sender"],
        subject=result["subject"],
        body_text=raw_email,
        billing_month=result["billing_month"]
    )


def _extract_activities_with_llm(llm, raw_email: str) -> list[ConsultantActivity]:
    """Extract consultant activities using LLM, handling multiple projects.

    Args:
        llm: LangChain LLM instance
        raw_email: Raw email content

    Returns:
        List of ConsultantActivity with consultant names, days worked, and project names
    """
    system_prompt = """You are a consultant activity extractor. Extract ALL consultant activities from the email.

The email may contain MULTIPLE PROJECTS. Each project section is indicated by a line starting with "-" or a clear project title.
The same consultant may appear in MULTIPLE PROJECTS - create a separate entry for each.

For each consultant activity, extract:
- Full name (First Last format)
- Days worked (as a number, extract from "Xj" or "X jours")
- Project name (the project this consultant worked on)

Return ONLY a JSON array of objects with these exact keys: consultant_name, days_declared, project_name

Example for multi-project email:
[
  {"consultant_name": "Elodie LEGUAY", "days_declared": 22, "project_name": "Modernisation Ligne Production - Multi commande"},
  {"consultant_name": "Didier GEIG", "days_declared": 12, "project_name": "Modernisation Ligne Production - Multi commande"},
  {"consultant_name": "Jon LEVIN", "days_declared": 7, "project_name": "Migration Cloud AWS - Temps partiel"},
  {"consultant_name": "Jon LEVIN", "days_declared": 15, "project_name": "Application Mobile Interne - Basic"}
]

Important:
- Extract ALL consultants from ALL projects in the email
- If a consultant appears in multiple projects, create separate entries
- Convert "22j" to 22, "15.5 jours" to 15.5
- Use "First Last" name format
- Extract the full project name as it appears in the email
- Return empty array [] if no consultants found"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=raw_email)
    ]

    response = llm.invoke(messages)

    # Parse JSON response
    import json
    activities_data = json.loads(response.content)

    # Convert to ConsultantActivity objects
    consultants = []
    for data in activities_data:
        consultants.append(ConsultantActivity(
            consultant_name=data["consultant_name"],
            days_declared=float(data["days_declared"]),
            days_in_boond=None,
            client_id=None,
            client_name=None,
            project_id=None,
            project_name=data["project_name"],  # Store project name from email
            resource_id=None,
            resource_name=None,
            timesheet_id=None,
            discrepancy_amount=None,
            severity=None
        ))

    return consultants
