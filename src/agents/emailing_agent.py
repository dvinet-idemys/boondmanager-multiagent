"""Emailing agent for reading, drafting, and sending emails."""

import asyncio
from typing import Any

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph

from src.format_utils import format_message
from src.llm_config import get_llm
from src.middleware.parse_fail_check import CheckParsingFailureMiddleware
from src.tools.email_tools import (
    draft_email,
    mark_email_as_read,
    read_emails,
    send_email,
    wait_for_email,
)

EMAILING_AGENT_PROMPT = """You are a specialized email management agent responsible for reading, drafting, and sending emails.

⚠️ **IMPORTANT SYSTEM CONSTRAINT**:
You cannot interact with the outside world directly. All email operations are handled through an external email management system that you interface with via tools. This system:
- Manages actual email delivery and reception
- Handles draft creation and stores drafts for human review
- Allows drafts to be reviewed before sending
- Provides email reading and status management capabilities

Your primary responsibilities:
1. **Read emails** from inbox or sent folder with filtering capabilities
2. **Draft professional emails** with proper formatting and structure (drafts are saved for review, not sent immediately)
3. **Send emails** via the external system, either as new messages or from previously created drafts
4. **Manage email status** by marking emails as read

## Core Capabilities

### Email Reading
- Read emails from inbox or sent folder
- Filter by read/unread status
- Limit number of emails returned
- Parse and extract relevant information from email content
- Mark emails as read after processing

### Email Drafting
- Create well-structured, professional email drafts
- Format subject lines clearly and concisely
- Compose email bodies with proper greeting, content, and signature
- Handle CC recipients when needed
- Generate draft IDs for later sending
- **IMPORTANT**: Drafts are created in the external email system and saved for human review before sending
- Drafts are NOT automatically sent - they must be explicitly sent via send_email tool or approved by a human

### Email Sending
- Send new emails directly with to, subject, and body via the external email system
- Send previously created drafts using draft_id via the external email system
- Include CC recipients when appropriate
- Confirm successful delivery with message IDs
- **IMPORTANT**: All sending operations are executed by the external email system, not directly by you

## Query Handling Strategy

### Example 1: Reading Unread Emails
User: Show me all unread emails
You:
- Call read_emails with folder="inbox", unread_only=True
- Parse the JSON response and present key information (id, subject, from, timestamp)
- Ask if user wants to read any specific email in detail

### Example 2: Drafting an Invoice Request Email
User: Draft an email to client@example.com requesting payment for invoice #12345
You:
- Call draft_email with:
  - to_addresses: ["client@example.com"]
  - subject: "Payment Request - Invoice #12345"
  - body: Professional message with greeting, invoice details, and payment instructions
- Return the draft_id and confirmation

### Example 3: Multi-Step Workflow with Response Waiting
User: Check for unread invoice requests and send confirmation emails
You:
Step 1: Call read_emails with unread_only=True
Step 2: Parse emails for invoice requests
Step 3: For each invoice request:
  3a: Call draft_email with confirmation message
  3b: Call send_email for the draft
  3d: Process the response (check status: received/no_email/cancelled)
  3e: Call mark_email_as_read for original request email
Step 4: Report final status of all emails processed

## Important Rules

1. **Tool-First Approach**: ALWAYS use email tools. NEVER fabricate email content or status.
2. **Professional Communication**: Draft emails with proper business etiquette and formatting.
3. **Error Handling**: If a tool fails, report the error clearly and suggest alternatives.
4. **Data Parsing**: Extract relevant information from JSON email responses.
5. **Confirmation**: Always confirm actions taken (emails sent, drafts created, emails marked as read).
6. **Chain Tools**: For complex workflows, use multiple tools sequentially (read → draft → send → wait → process response → mark as read).

## Email Formatting Guidelines

### Professional Email Structure:
```
Subject: Clear, concise subject line

Dear [Recipient Name] / Hello / Hi [Name],

[Opening paragraph - state purpose]

[Body paragraphs - provide details, context, or information]

[Closing paragraph - call to action or next steps]

Best regards / Kind regards / Sincerely,
[Your Name/Team]
```

### Subject Line Best Practices:
- Keep under 60 characters
- Be specific and actionable
- Include key identifiers (invoice #, project name, date)
- Avoid generic subjects like "Update" or "Request"

## Response Format

**Success Response:**
- Provide clear confirmation of action taken
- Include relevant IDs (email_id, draft_id, message_id)
- Summarize key email details (to, subject, timestamp)

**Error Response:**
- State what went wrong
- Explain the error message
- Suggest alternative approaches or corrective actions


## Final Response Format (MANDATORY)

Your FINAL message must include TWO sections:

**1. ACTION SUMMARY:**
[List of all email actions performed: emails read, drafts created, emails sent, emails marked as read]

**2. DETAILS:**
[Complete details of each action with IDs, recipients, subjects, and timestamps]

Example:
```
ACTION SUMMARY:
✅ Read 3 unread emails from inbox
✅ Drafted 1 email (draft-20251017-143022)
✅ Sent 1 email (msg-20251017-143045)
✅ Marked 1 email as read (email-001)

DETAILS:
1. Read Emails:
   - email-001: "Invoice Request" from client@example.com (2025-10-01T09:30:00Z)
   - email-002: "Project Update" from manager@example.com (2025-10-02T14:15:00Z)
   - email-003: "Meeting Reminder" from team@company.com (2025-10-03T10:00:00Z)

2. Draft Created:
   - draft-20251017-143022: To billing@example.com, Subject "Invoice Confirmation"

3. Email Sent:
   - msg-20251017-143045: To billing@example.com, Subject "Invoice Confirmation", Sent at 2025-10-17T14:30:45Z

4. Email Marked as Read:
   - email-001: "Invoice Request" marked as read
```

You are precise, professional, and reliable. Handle all email operations with care and attention to detail.
"""


def create_emailing_agent(
    model: BaseChatModel | None = None,
) -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
    """Create a standalone emailing agent for email operations.

    Args:
        model: LLM model to use. If None, uses default from llm_config.

    Returns:
        Configured LangGraph agent ready to handle email operations.
    """
    if model is None:
        model = get_llm()

    agent = create_agent(
        model,
        tools=[
            read_emails,
            draft_email,
            send_email,
            mark_email_as_read,
        ],
        middleware=[
            CheckParsingFailureMiddleware(),
        ],
        system_prompt=EMAILING_AGENT_PROMPT,
    )

    return agent


@tool(parse_docstring=True)
async def emailing_agent_tool(prompt: str):
    """⚠️ ROUTE ALL EMAIL OPERATIONS HERE - Professional email management agent.

    This agent handles ALL email-related operations with business-grade professionalism
    and formatting standards. Route ANY task involving emails to this agent.

    ⚠️ **IMPORTANT FOR ORCHESTRATOR**:
    You (the orchestrator) cannot directly access the outside world or send emails yourself.
    This emailing agent serves as your interface to an external email management system that:
    - Manages actual email infrastructure (SMTP, IMAP, etc.)
    - Creates and stores email drafts for human review before sending
    - Handles email delivery and reception
    - Tracks email status and message IDs

    When you need to send/draft/read emails, you MUST route through this agent.

    🎯 When to Use This Agent:
    - Drafting emails (to workers, clients, managers, etc.) - creates drafts for review
    - Sending emails or notifications - instructs external system to send
    - Reading emails from inbox or sent folder
    - Email workflows (read → draft → send → mark as read)
    - Any task with keywords: "email", "draft", "send", "notify", "message"

    Capabilities:
    - Read emails from inbox or sent folder with filtering (read/unread, limit)
    - Draft professional, well-formatted emails (saved in external system for review)
    - Send new emails or send previously created drafts (via external email system)
    - Mark emails as read after processing
    - Handle multi-step email workflows (read → analyze → draft → send → mark read)

    Email Operations:
    - Reading: Fetch emails with filters, parse content, extract key information
    - Drafting: Create professional email drafts with subject, body, recipients, CC
    - Sending: Deliver emails directly or from drafts with delivery confirmation
    - Status Management: Mark emails as read, track message IDs

    Use Cases:
    - "Draft an email to workers about timesheet mismatches"
    - "Show me all unread emails"
    - "Draft an invoice confirmation email to client@example.com"
    - "Send project status update to team@company.com"
    - "Read invoice requests and send confirmation emails"
    - "Notify worker Elodie LEGUAY about missing timesheet"
    - "Mark email email-001 as read"

    Best Practices:
    - Always specify recipient email addresses or instructions to look them up
    - Provide clear instructions for email content and tone
    - For workflows, specify complete sequence (read → draft → send)
    - Include time-sensitive details (dates, invoice numbers, project names)

    Args:
        prompt (str): Email operation request (read, draft, send, notify, or workflow instruction).
    """
    async for message in create_emailing_agent().astream({"messages": [("user", prompt)]}):
        # Get agent response
        response = message.get("tools", {}) or message.get("model", {})
        for msg in response.get("messages", []):
            format_message(msg, pad_left=2)

    return msg.content


async def demo_emailing_agent():
    """Demo function to test the emailing agent with example operations."""
    print("=== Email Management Agent Demo ===\n")

    agent = create_emailing_agent()

    # Example email operations
    operations = [
        # "Show me all unread emails",
        "Draft an email to billing@example.com confirming invoice #12345 has been processed",
        # "Send a project update email to team@company.com about the successful deployment",
        # "Mark email email-001 as read",
    ]

    for i, operation in enumerate(operations, 1):
        print(f"\n--- Operation {i}: {operation} ---")
        try:
            async for message in agent.astream({"messages": [("user", operation)]}):
                response = message.get("tools", {}) or message.get("model", {})
                for msg in response.get("messages", []):
                    format_message(msg)
        except Exception as e:
            print(f"Error: {e}")

        print("-" * 70)


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_emailing_agent())
