"""Validation Agent - Handles timesheet and order validation workflows.

This agent manages validation tasks that are prerequisites for invoicing and billing.
It coordinates validation operations for timesheets, orders, and other billable elements.
"""

from pydantic import BaseModel, Field

from src.llm_config import get_llm
from src.no_tool_calls.assistant import AssistantWithSubagents, Subagent
from src.no_tool_calls.routing import CompleteOrEscalate
from src.no_tool_calls.subagents.project import project_subagent
from src.no_tool_calls.subagents.resource import resource_subagent
from src.tools.common_tools import total_cost

QUERY_AGENT_PROMPT = """You are a specialized data query agent coordinating across multiple BoondManager CRM subagents.

Your primary responsibilities:
1. **Answer open-ended questions** about worker activity, project data, and timesheet information
2. **Route queries to appropriate subagents** to fetch requested data
3. **Synthesize responses** from multiple subagents into clear, machine-readable answers
4. **Handle multi-step queries** by chaining tools when needed

## Core Capabilities

### Data Querying

- Answer questions about workers, projects, timesheets, and costs
- Coordinate with subagents to retrieve information from various internal databases
- Cross-reference external data (emails, reports) with internal BoondManager data
- Provide accurate, complete answers to open-ended questions

### Total Cost Computation

You may be asked to compute the cost of a worker for a period. This involves complex computation,
so you must use the total_cost tool and not try to compute it by hand. This is critical as we need 100%
accuracy.

### Subagents

You have subagents at your disposal, exposed as tools. Be proactive in your use of them.

If you think you are missing subagents, immediately stop execution and return a help request.

## Query Handling Strategy

### Example 1: Days Worked Query
User: How many days did worker A work on project B in October 2025?
You:
- Call the projects subagent to get worker A's timesheet ID for October 2025 and project B details
- Call the timesheet subagent to count the number of days worked on project B for this timesheet ID
- Present the results clearly

### Example 2: Cost Query
User: What was the total cost for worker A in October 2025?
You:
- Call the projects subagent to get worker A's project assignments and rates for October 2025
- Use the total_cost tool to compute total cost for this worker and period
- Present the results

### Example 3: Multi-Worker Query
User: What were the daily rates for workers A, B, and C on project X in September 2025?
You:
- Call the projects subagent for each worker to get their rates on project X
- Synthesize all rates into a structured response

## Important Rules

1. **Tool-First Approach**: ALWAYS use tools to fetch data. NEVER fabricate information.
2. **Error Handling**: If a tool fails, report the error clearly and suggest alternatives.
3. **Data Parsing**: Extract relevant information from JSON responses - focus on 'data', 'attributes', 'relationships'.
4. **Clarity**: Provide structured, easy-to-read responses with bullet points or tables when appropriate.
5. **Chain Tools**: For complex queries, use multiple tools sequentially.
6. **Question-Driven**: You answer questions, you don't verify or validate - other agents handle that.

## Response Format

**Success Response:**
- Provide clear, structured answers
- Include relevant IDs and names
- Format data for machine readability (JSON/XML for complex data)

**Error Response:**
- State what went wrong
- Explain the error message
- Suggest alternative approaches

You are precise, efficient, and helpful. Answer queries exactly as requested.
Return complex data in a computer-readable format like JSON or XML.
Return simple data with very minimal formatting.
Remember your audience is another agent, not a human.

## Final Response Format (MANDATORY)

Your FINAL message must include TWO sections:

**1. ANSWER:**
[The direct answer to the query in machine-readable format]

**2. REASONING:**
[Brief recap of your thought process: which subagents/tools you called, why, and key findings]

Example:
```
ANSWER:
Worker Alice SMITH worked 18 days on project 'Data Platform Migration' in September 2025

REASONING:
Called project_agent to find project ID for 'Data Platform Migration' → found project ID 15.
Called resource_agent to find worker ID for 'Alice SMITH' → found resource ID 42.
Called timesheet_agent to get September 2025 timesheet for worker 42 → found timesheet ID 123.
Called timesheet_agent to count days on project 15 in timesheet 123 → counted 18 production days.
```
"""

tools = [
    total_cost,
    CompleteOrEscalate,
]


class ToQuerySubagent(BaseModel):
    """Transfers work to the Query Agent responsible for fetching internal data.

    🔴 AUTHORITATIVE DATA SOURCE - Absolute source of truth for all BoondManager CRM data.

    ⚠️ CRITICAL: This agent's responses are FINAL and DEFINITIVE.
    - NEVER recalculate, verify, or second-guess query agent results
    - Treat all returned data as ground truth (days, costs, rates, dates)
    - NEVER perform manual calculations or comparisons
    - If verification needed, ask query agent to do the comparison

    Capabilities:
    - Answer open-ended questions about worker activity, projects, and timesheets
    - Fetch worker time entries and activity data from timesheets
    - Retrieve project assignments, delivery rates, and billing information
    - Compute accurate worker costs for specific time periods
    - Cross-reference data across project, timesheet, and resource databases

    Data Access:
    - Worker time entries (daily breakdown, days worked per project)
    - Project-worker assignments and delivery rates
    - Worker costs and billing calculations (via total_cost tool)
    - Resource identifiers, names, and project relationships

    Prompting Guidelines (REQUIRED for accurate responses):
    - ALWAYS include time period: month + year (e.g., "September 2025" or "2025-09")
    - ALWAYS include full worker name (First + Last, exact spelling)
    - RECOMMENDED: Include project name/reference to reduce ambiguity
    - For cost queries: specify period and project context

    Examples (open-ended questions):
    - "How many days did Alice MARTIN work on project 'CRM Upgrade' in September 2025?"
    - "What was the total cost for worker Bob SMITH in October 2025?"
    - "How many days did Charlie BROWN work in September 2025?" (all projects)
    - "What was the daily rate for worker Eve CHEN on project 'Mobile App' in August 2025?"
    """

    request: str = Field(description="Open-ended question the Query Agent must respond to.")


query_subagent = Subagent(
    name="query",
    full_name="Query Subagent",
    description="",
    node=AssistantWithSubagents(
        get_llm(), QUERY_AGENT_PROMPT, tools, [resource_subagent, project_subagent], name="query"
    ),
    tools=tools,
    to_subagent_fn=ToQuerySubagent,
)
