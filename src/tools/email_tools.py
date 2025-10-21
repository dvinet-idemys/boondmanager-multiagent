"""Email tools for reading, drafting, and sending emails."""

from datetime import datetime
from typing import List

from langchain_core.tools import tool
from langgraph.types import interrupt
from pydantic import BaseModel, Field


class EmailMessage(BaseModel):
    """Email message structure."""

    id: str = Field(description="Unique email identifier")
    subject: str = Field(description="Email subject line")
    from_address: str = Field(description="Sender email address")
    to_addresses: List[str] = Field(description="Recipient email addresses")
    cc_addresses: List[str] = Field(default_factory=list, description="CC email addresses")
    body: str = Field(description="Email body content")
    timestamp: str = Field(description="Email timestamp in ISO format")
    is_read: bool = Field(default=False, description="Whether email has been read")


# Mock email storage
MOCK_INBOX: List[EmailMessage] = [
    EmailMessage(
        id="email-001",
        subject="Invoice Request - Project Modernisation - September 2025",
        from_address="client@example.com",
        to_addresses=["billing@company.com"],
        body="""Hello,

We would like to request an invoice for the following consultants who worked on our Project Modernisation in September 2025:

- Elodie LEGUAY: 22 days
- Didier GEIG: 12 days

Please process this invoice at your earliest convenience.

Best regards,
Client Team""",
        timestamp="2025-10-01T09:30:00Z",
        is_read=False,
    ),
    EmailMessage(
        id="email-002",
        subject="RE: Monthly Report",
        from_address="manager@example.com",
        to_addresses=["team@company.com"],
        cc_addresses=["director@company.com"],
        body="Thanks for the update. Please proceed with the next phase.",
        timestamp="2025-10-02T14:15:00Z",
        is_read=True,
    ),
]

MOCK_SENT: List[EmailMessage] = []
MOCK_DRAFTS: dict[str, EmailMessage] = {}


@tool(parse_docstring=True)
def read_emails(folder: str = "inbox", unread_only: bool = False, limit: int = 10) -> str:
    """Read emails from the specified folder.

    This is a dummy implementation that returns mock email data for testing.
    In production, this would connect to a real email service (IMAP, Gmail API, etc.).

    Args:
        folder (str): Email folder to read from. Options: 'inbox', 'sent'. Default: 'inbox'
        unread_only (bool): If True, only return unread emails. Default: False
        limit (int): Maximum number of emails to return. Default: 10

    Returns:
        str: JSON-formatted list of emails with id, subject, from, to, cc, body, timestamp, is_read
    """
    # Select folder
    if folder.lower() == "sent":
        emails = MOCK_SENT
    else:
        emails = MOCK_INBOX

    # Filter unread if requested
    if unread_only:
        emails = [e for e in emails if not e.is_read]

    # Apply limit
    emails = emails[:limit]

    # Format response
    if not emails:
        return "No emails found."

    import json

    return json.dumps(
        [
            {
                "id": e.id,
                "subject": e.subject,
                "from": e.from_address,
                "to": e.to_addresses,
                "cc": e.cc_addresses,
                "body": e.body,
                "timestamp": e.timestamp,
                "is_read": e.is_read,
            }
            for e in emails
        ],
        indent=2,
    )


@tool(parse_docstring=True)
def draft_email(
    to_addresses: List[str],
    subject: str,
    body: str,
    cc_addresses: List[str] | None = None,
) -> str:
    """Draft an email with specified recipients, subject, and body.

    This is a dummy implementation that creates a draft email object.
    In production, this would save a draft in the email service.

    Args:
        to_addresses (List[str]): List of recipient email addresses
        subject (str): Email subject line
        body (str): Email body content (plain text or HTML)
        cc_addresses (List[str] | None): Optional list of CC email addresses

    Returns:
        str: Confirmation message with draft ID and email details
    """
    # Generate draft ID
    draft_id = f"draft-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Create draft
    draft = EmailMessage(
        id=draft_id,
        subject=subject,
        from_address="system@company.com",
        to_addresses=to_addresses,
        cc_addresses=cc_addresses or [],
        body=body,
        timestamp=datetime.now().isoformat(),
        is_read=False,
    )

    # Store draft
    MOCK_DRAFTS[draft_id] = draft

    # Format response
    return f"""Draft email created successfully!

Draft ID: {draft_id}
From: {draft.from_address}
To: {", ".join(draft.to_addresses)}
CC: {", ".join(draft.cc_addresses) if draft.cc_addresses else "None"}
Subject: {draft.subject}

Body Preview:
{draft.body[:200]}{"..." if len(draft.body) > 200 else ""}
"""


@tool(parse_docstring=True)
def send_email(
    to_addresses: List[str] | None = None,
    subject: str | None = None,
    body: str | None = None,
    cc_addresses: List[str] | None = None,
    draft_id: str | None = None,
) -> str:
    """Send an email either from scratch or from a draft.

    This is a dummy implementation that simulates sending an email.
    In production, this would use SMTP, Gmail API, or other email service.

    You can either:
    1. Send a new email by providing to_addresses, subject, and body
    2. Send an existing draft by providing draft_id

    Args:
        to_addresses (List[str] | None): Recipient email addresses (required if not using draft_id)
        subject (str | None): Email subject (required if not using draft_id)
        body (str | None): Email body content (required if not using draft_id)
        cc_addresses (List[str] | None): Optional CC addresses
        draft_id (str | None): Draft ID to send (alternative to providing email details)

    Returns:
        str: Confirmation message with sent email details and message ID
    """
    # Validate inputs
    if draft_id is None and (to_addresses is None or subject is None or body is None):
        return "Error: Either provide draft_id OR (to_addresses, subject, and body)"

    # Generate message ID
    message_id = f"msg-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Create email message
    if draft_id:
        # Retrieve draft
        if draft_id not in MOCK_DRAFTS:
            return (
                f"❌ Error: Draft '{draft_id}' not found. Please check the draft ID and try again."
            )

        draft = MOCK_DRAFTS[draft_id]
        email = EmailMessage(
            id=message_id,
            subject=draft.subject,
            from_address="system@company.com",
            to_addresses=draft.to_addresses,
            cc_addresses=draft.cc_addresses,
            body=draft.body,
            timestamp=datetime.now().isoformat(),
            is_read=False,
        )
    else:
        email = EmailMessage(
            id=message_id,
            subject=subject,
            from_address="system@company.com",
            to_addresses=to_addresses,
            cc_addresses=cc_addresses or [],
            body=body,
            timestamp=datetime.now().isoformat(),
            is_read=False,
        )

    # Add to sent folder
    MOCK_SENT.append(email)

    # Format response
    return f"""✅ Email sent successfully!

Message ID: {message_id}
From: {email.from_address}
To: {", ".join(email.to_addresses)}
CC: {", ".join(email.cc_addresses) if email.cc_addresses else "None"}
Subject: {email.subject}
Sent at: {email.timestamp}

The email has been delivered to {len(email.to_addresses)} recipient(s)."""


@tool(parse_docstring=True)
def mark_email_as_read(email_id: str) -> str:
    """Mark an email as read.

    Args:
        email_id (str): The ID of the email to mark as read

    Returns:
        str: Confirmation message
    """
    for email in MOCK_INBOX:
        if email.id == email_id:
            email.is_read = True
            return f"✅ Email '{email_id}' marked as read."

    return f"❌ Email '{email_id}' not found in inbox."


@tool(parse_docstring=True)
def wait_for_email(
    expected_subject: str | None = None,
    expected_from: str | None = None,
    reason: str | None = None,
) -> dict:
    """Wait for a new email to arrive (triggers human-in-the-loop interrupt).

    This tool pauses the workflow and waits for human input to simulate receiving
    an expected email. The workflow will interrupt here, allowing a human to either:
    1. Provide the email content that was received
    2. Indicate no email was received
    3. Cancel the workflow

    This is useful for workflows that depend on external responses, such as:
    - Waiting for client approval emails
    - Waiting for invoice confirmation responses
    - Waiting for timesheet submission notifications
    - Waiting for any external email response

    Args:
        expected_subject (str | None): Optional description of the expected email subject
        expected_from (str | None): Optional expected sender email address
        reason (str | None): Optional explanation of why we're waiting for this email

    Returns:
        dict: Human-provided email data with keys:
            - status: "received" | "no_email" | "cancelled"
            - email_data: dict with {subject, from, to, body, timestamp} if status="received"
            - message: optional message from human

    Example Usage:
        # Wait for client approval
        result = wait_for_email(
            expected_subject="Invoice Approval - September 2025",
            expected_from="client@example.com",
            reason="Waiting for client to approve invoice before sending"
        )

        # Generic wait for any response
        result = wait_for_email(
            reason="Waiting for email response from project manager..."
        )

        # Handle the result
        if result["status"] == "received":
            email_data = result["email_data"]
            # Process the received email
        elif result["status"] == "no_email":
            # Handle case where no email was received
        elif result["status"] == "cancelled":
            # Handle cancellation
    """
    # Build interrupt payload for human
    interrupt_payload = {
        "type": "wait_for_email",
        "message": "⏳ Workflow paused - Waiting for email to arrive",
    }

    if expected_subject:
        interrupt_payload["expected_subject"] = expected_subject

    if expected_from:
        interrupt_payload["expected_from"] = expected_from

    if reason:
        interrupt_payload["reason"] = reason

    interrupt_payload["instructions"] = {
        "received": "Provide email data as JSON: {subject, from, to, body, timestamp}",
        "no_email": "Respond with: NO_EMAIL",
        "cancel": "Respond with: CANCEL",
    }

    # Trigger interrupt - execution pauses here until human resumes with input
    human_response = interrupt(interrupt_payload)

    # Parse human response when execution resumes
    if isinstance(human_response, dict):
        # Human provided structured email data
        if "subject" in human_response and "from" in human_response:
            return {
                "status": "received",
                "email_data": {
                    "subject": human_response.get("subject", ""),
                    "from": human_response.get("from", ""),
                    "to": human_response.get("to", []),
                    "body": human_response.get("body", ""),
                    "timestamp": human_response.get("timestamp", datetime.now().isoformat()),
                },
            }
        else:
            return {
                "status": "error",
                "message": "Invalid email data format provided",
                "received_data": human_response,
            }
    elif isinstance(human_response, str):
        # Human provided simple string response
        response_upper = human_response.strip().upper()
        if response_upper == "NO_EMAIL":
            return {
                "status": "no_email",
                "message": "No email was received",
            }
        elif response_upper == "CANCEL":
            return {
                "status": "cancelled",
                "message": "Workflow cancelled by user",
            }
        else:
            # Treat as email body
            return {
                "status": "received",
                "email_data": {
                    "subject": expected_subject or "Unknown",
                    "from": expected_from or "unknown@example.com",
                    "to": ["system@company.com"],
                    "body": human_response,
                    "timestamp": datetime.now().isoformat(),
                },
            }
    else:
        # Unexpected response type
        return {
            "status": "error",
            "message": f"Unexpected response type: {type(human_response)}",
            "received_data": str(human_response),
        }
