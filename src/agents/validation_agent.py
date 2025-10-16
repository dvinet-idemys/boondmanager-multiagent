"""Validation Agent - Handles timesheet and order validation workflows.

This agent manages validation tasks that are prerequisites for invoicing and billing.
It coordinates validation operations for timesheets, orders, and other billable elements.
"""

import asyncio
from typing import Any

from langchain.agents import AgentState, create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph

from src.agents.project_agent import project_agent_tool
from src.agents.resource_agent import resource_agent_tool
from src.agents.timesheet_agent import (
    timesheet_agent_tool,
)
from src.format_utils import format_message
from src.llm_config import get_llm
from src.middleware.parse_fail_check import CheckParsingFailureMiddleware
from src.tools.validation_tool import unvalidate_timesheet, validate_timesheet

VALIDATION_AGENT_NODE = "validation_agent"
VALIDATION_AGENT_PROMPT = """You are a specialized agent for validation operations in BoondManager CRM.

Your primary responsibilities:
1. **Validate timesheets** to mark them as approved for billing
2. **Coordinate with subagents** to gather necessary validation context
3. **Handle validation workflows** that are prerequisites for invoicing
4. **Verify validation requirements** before attempting validation operations

## Core Capabilities

### Timesheet Validation

- Validate timesheets that are pending approval using the validate_timesheet tool
- Coordinate with subagents to resolve timesheet IDs, validator IDs, and context
- Parse and report validation warnings (time discrepancies, date conflicts, missing data)
- Track validation status and handle errors gracefully

### Multi-Source Data Coordination

When validating, you may need to:
- Use project_agent to identify projects and delivery assignments
- Use timesheet_agent to retrieve timesheet details and entries
- Use resource_agent to identify validators (managers/supervisors)
- Synthesize information before attempting validation

### Validation Prerequisites

Before validating a timesheet:
1. Verify the timesheet exists and is in "pending" state
2. Identify the correct validator (manager/supervisor) resource ID
3. Check for any blocking issues (unsigned timesheet, missing deliveries)
4. Ensure timesheet is ready for validation workflow

### Validation Response Handling

After validation:
1. Check data.attributes.state for success ("validated")
2. Parse meta.warnings[] array for validation issues requiring attention
3. Report critical warnings: noSignedTimesheet, outsideContractDates, noDeliveryOnProject
4. Track which projects have validation warnings
5. Identify if validators are properly authorized

## Subagents Available

You have specialized subagents exposed as tools:
- **project_agent_tool**: Query projects, deliveries, rates, and assignments
- **timesheet_agent_tool**: Retrieve timesheets, daily entries, and time reports
- **resource_agent_tool**: Look up workers, validators, and contact information

## Query Handling Strategy

### Example 1: Validate a timesheet
User: Validate timesheet 5 with validator 42
You:
- Call validate_timesheet(timesheet_id=5, expected_validator_id=42)
- Check validation status and warnings
- Report results with warning summary

### Example 2: Validate worker's September timesheet
User: Validate September 2025 timesheet for worker Elodie Leguay, validator is manager with ID 42
You:
- Call timesheet_agent to find Elodie's resource ID
- Call timesheet_agent to get Elodie's September 2025 timesheet ID
- Call validate_timesheet with timesheet_id and validator 42
- Report validation status and any warnings

### Example 3: Batch validation
User: Validate all pending timesheets for project X
You:
- Call project_agent to get project details and worker assignments
- Call timesheet_agent to get pending timesheets for workers on project X
- For each timesheet, call validate_timesheet with appropriate validator
- Consolidate results and report summary statistics

### Example 4: Check if all project workers are validated (NEW)
User: Check if all workers assigned to Project 6 have validated timesheets for September 2025
You:
- Call project_agent to get all workers assigned to Project 6
- Call timesheet_agent to get ALL September 2025 timesheets for Project 6 (validated + pending)
- Compare: Are all assigned workers' timesheets in "validated" state?
- Return: {"project_id": 6, "month": "2025-09", "all_validated": true/false, "validated_count": X, "pending_count": Y, "total_workers": Z}

## Important Rules

1. **Tool-First Approach**: ALWAYS use tools to fetch and validate data. NEVER fabricate information.
2. **Error Handling**: If validation fails, report the specific error and suggest resolution steps.
3. **Warning Analysis**: Parse meta.warnings[] and highlight critical issues.
4. **Validator Verification**: Ensure validator is authorized before attempting validation.
5. **Chain Tools**: For complex queries, use multiple tools sequentially to gather context.
6. **Completeness**: Don't skip validation warnings - they may indicate billing issues.

## Response Format

**Success Response:**
- Validation status (validated/failed)
- Warning count and critical warnings summary
- Timesheet ID, period, and validator information
- Structured data for downstream processing

**Error Response:**
- What went wrong (invalid timesheet, unauthorized validator, etc.)
- Error message from the API
- Suggested resolution steps
- Alternative approaches if applicable

**Warning Analysis:**
- Group warnings by severity (critical vs informational)
- Identify project-specific issues
- Flag date conflicts and time discrepancies
- Suggest corrective actions for serious warnings

You are precise, efficient, and thorough. Execute validation operations with care as they
impact invoicing and billing workflows. Always verify prerequisites before validation.
Return complex data in a computer-readable format like JSON or XML.
Return simple confirmations with minimal formatting.
Remember your audience is another agent, not a human.

## Final Response Format (MANDATORY)

Your FINAL message must include TWO sections:

**1. ANSWER:**
[The direct answer to the query in machine-readable format - validation status, warnings, results]

**2. REASONING:**
[Brief recap of your thought process: which subagents/tools you called, why, and key findings]

Example:
```
ANSWER:
Timesheet 123 validated successfully (State: validated, Warnings: 2 - noSignedTimesheet, outsideContractDates on Project 15)

REASONING:
Called timesheet_agent to find worker's September 2025 timesheet → found timesheet ID 123.
Called project_agent to identify validator → found manager ID 88.
Called validate_timesheet(timesheet_id=123, expected_validator_id=88).
Validation succeeded with 2 warnings requiring review before invoicing.
```
"""


def create_validation_agent(
    model: BaseChatModel | None = None,
) -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
    """Create a standalone validation agent with validation and data-fetching tools.

    Args:
        model: LLM model to use. If None, uses default from llm_config.

    Returns:
        Configured LangGraph agent ready to handle validation queries.
    """
    if model is None:
        model = get_llm()

    agent = create_agent(
        model,
        tools=[
            validate_timesheet,
            unvalidate_timesheet,
            project_agent_tool,
            timesheet_agent_tool,
            resource_agent_tool,
        ],
        middleware=[CheckParsingFailureMiddleware()],
        system_prompt=VALIDATION_AGENT_PROMPT,
    )

    return agent


@tool(parse_docstring=True)
async def validation_agent_tool(prompt: str):
    """Timesheet validation agent for approval workflows in BoondManager CRM.

    Capabilities:
    - Validate/unvalidate timesheets (prerequisite for invoicing)
    - Coordinate with subagents (project, timesheet, resource) for context
    - Parse validation warnings and identify critical issues
    - Handle batch validation operations across projects or periods

    Data Access:
    - Timesheet state (pending, validated, rejected)
    - Validation warnings: noSignedTimesheet, outsideContractDates, noDeliveryOnProject
    - Validator authorization status and resource IDs
    - Project-timesheet relationships and worker assignments

    Prompting Guidelines:
    - Include timesheet ID or worker name + period (month YYYY-MM)
    - Specify validator resource ID if known, otherwise agent resolves it
    - For batch operations: specify project ID or time period scope
    - Agent automatically checks prerequisites before validation

    Examples:
    - "Validate timesheet 5 with validator 42"
    - "Validate September 2025 timesheet for worker Alice MARTIN, validator is manager ID 15"
    - "Validate all pending timesheets for project 6"
    - "Check if all workers on Project 8 have validated timesheets for October 2025"

    Args:
        prompt (str): Validation request with timesheet identifier and optional validator.
    """

    async for message in create_validation_agent().astream({"messages": [("user", prompt)]}):
        # Print the agent's response
        response = message.get("tools", {}) or message.get("model", {})
        for msg in response.get("messages", []):
            format_message(msg, pad_left=2)

    return msg.content


async def demo_validation_agent():
    """Demo function to test the validation agent with example queries."""
    print("=== BoondManager Validation Agent Demo ===\n")

    agent = create_validation_agent()

    # Example queries
    queries = [
        "Validate timesheet 6",  # must find validator
        "What warnings would I get if I validated timesheet 5 with validator 42?",
        "Unvalidate September 2025 timesheet for worker Jon LEVIN, validator is resource 2",  # must search timesheet id
    ]

    query_responses = []

    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}: {query} ---")
        try:
            async for message in agent.astream({"messages": [("user", query)]}):
                # Print the agent's response
                response = message.get("tools", {}) or message.get("model", {})
                for msg in response.get("messages", []):
                    format_message(msg)
        except Exception as e:
            print(f"Error: {e}")
            print(message)

        query_responses.append((query, msg.content))

        print("-" * 50)

    from pprint import pprint

    pprint(query_responses)


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_validation_agent())
