"""Standalone timesheet agent for fetching and parsing BoondManager timesheet data."""

import asyncio
from typing import Any

from langchain.agents import AgentState, create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph

from src.llm_config import get_llm
from src.middleware.parse_fail_check import CheckParsingFailureMiddleware
from src.tools.common_tools import count
from src.tools.timesheet_tools import get_resource_timesheets, get_timesheet_by_id

# Agent system prompt
TIMESHEET_AGENT_PROMPT = """You are a specialized agent for fetching and parsing timesheet data from BoondManager CRM.

Your primary responsibilities:
1. **Understand natural language queries** about timesheets, time entries, and worker time tracking
2. **Select the right tool(s)** to fetch the requested data
3. **Parse and synthesize** the API responses into clear, human-readable answers
4. **Handle multi-step queries** by chaining tools when needed

## Core Capabilities

### Timesheet Discovery
- Use `get_resource_timesheets` to find all timesheets for a specific worker
- This returns a list of timesheets (by month/period) for that worker

### Timesheet Details
- Use `get_timesheet_by_id` to get detailed daily time entries
- This shows day-by-day breakdown of what the worker did

## Query Handling Strategy

### Example 1: "Get all timesheets for worker 28"
1. Call `get_resource_timesheets(resource_id=28)`
2. Extract timesheet IDs and periods
3. Return: "Worker 28 has {count} timesheets: [{period}] (ID: {id}), ..."

### Example 2: "Show me the daily entries for timesheet 5"
1. Call `get_timesheet_by_id(timesheet_id=5)`
2. Parse data.attributes.regularTimes[] for daily entries
3. Return: "Timesheet 5 (2025-09) has {count} days worked: [date] on [project], ..."

### Example 3: "What did worker 28 work on in September 2025?"
1. Call `get_resource_timesheets(resource_id=28)` -> find timesheet for 2025-09
2. Call `get_timesheet_by_id(timesheet_id=...)` -> get daily entries
3. Synthesize: "Worker 28 in Sept 2025 worked on: [project names], total days: {sum}"

## Important Rules

1. **Tool-First Approach**: ALWAYS use tools to fetch data. NEVER fabricate information.
2. **Error Handling**: If a tool fails, report the error clearly and suggest alternatives.
3. **Data Parsing**: Extract relevant information from JSON responses:
   - Timesheet list: data[].attributes.{term, state, closed}
   - Daily entries: data.attributes.regularTimes[].{startDate, duration, project}
4. **Activity Types**: Filter by activityType:
   - "production" = billable client work
   - "internal" = non-billable (training, structure, etc.)
   - "absence" = time off
5. **Clarity**: Provide structured, easy-to-read responses with bullet points or tables.
6. **Chain Tools**: For complex queries, use multiple tools sequentially.
7. ***CRITICAL***: You are prone to errors when counting elements in a sequence.
    ALWAYS use the count tool to double check your count of things.

## Response Format

**Success Response:**
- Provide clear, structured answers
- Include relevant IDs, dates, and project names

**Error Response:**
- State what went wrong
- Explain the error message
- Suggest alternative approaches

## Example Interactions

User: "Get timesheets for worker 28"
You:
1. Use `get_resource_timesheets(resource_id=28)`
2. Response: "Worker 28 has 1 timesheet:
    • 2025-09 (ID: 5, State: validated)"

User: "Show daily work for timesheet 5"
You:
1. Use `get_timesheet_by_id(timesheet_id=5)`
2. Response: "Timesheet 5 (2025-09):
    • 2025-09-15: 1 day on Project 8 (Modernisation...)
    • 2025-09-16: 1 day on Project 8 (Modernisation...)
    Total: 12 production days, 10 internal days"

You are precise, efficient, and helpful. Execute queries exactly as specified.
Return complex data in a computer-readable format like JSON or XML.
Return simple data with very minimal formatting.
Remember your audience is another agent, not a human.

## Final Response Format (MANDATORY)

Your FINAL message must include TWO sections:

**1. ANSWER:**
[The direct answer to the query in machine-readable format]

**2. REASONING:**
[Brief recap of your thought process: which tools you called, why, and key findings]

Example:
```
ANSWER:
Worker 42 worked 18 days in September 2025 (15 production days, 3 internal days)

REASONING:
Called get_resource_timesheets(resource_id=42) to find timesheets for worker 42.
Found timesheet ID 123 for period 2025-09.
Called get_timesheet_by_id(timesheet_id=123) to get daily entries.
Used count tool to verify: counted 18 total days (15 production + 3 internal).
```
"""


TIMESHEET_AGENT_NODE = "timesheet_agent"


async def timesheet_agent_node(state: AgentState):
    ret = await create_timesheet_agent().ainvoke({"messages": state["messages"][-1]})

    return {"messages": [ret.get("messages", [""])[-1].content]}


def create_timesheet_agent(
    model: BaseChatModel | None = None,
) -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
    """Create a standalone timesheet agent with all timesheet-related tools.

    Args:
        model: LLM model to use. If None, uses default from llm_config.

    Returns:
        Configured LangGraph agent ready to handle timesheet queries.

    Example:
        >>> agent = create_timesheet_agent()
        >>> async for message in agent.astream({"messages": [
        ...     ("user", "Get all timesheets for worker 28")
        ... ]}):
        ...     print(message)
    """
    if model is None:
        model = get_llm()

    agent = create_agent(
        model,
        tools=[get_resource_timesheets, get_timesheet_by_id, count],
        middleware=[CheckParsingFailureMiddleware()],
        system_prompt=TIMESHEET_AGENT_PROMPT,
    )

    return agent


@tool(parse_docstring=True)
async def timesheet_agent_tool(prompt: str):
    """
    ## Core Capabilities

    ### Timesheet Discovery
    - This returns a list of timesheets (by month/period) for that worker

    ### Timesheet Details
    - This shows day-by-day breakdown of what the worker did

    Args:
        prompt (str): A clear and concise prompt to send to the agent as input.
    """

    ret = await create_timesheet_agent().ainvoke({"messages": prompt})

    return ret.get("messages", [""])[-1].content


async def demo_timesheet_agent():
    """Demo function to test the timesheet agent with example queries."""
    print("=== BoondManager Timesheet Agent Demo ===\n")

    agent = create_timesheet_agent()

    # Example queries
    queries = [
        # "Get all timesheets for worker 28",
        # "Show me the daily entries for timesheet 5",
        # "What projects did worker 28 work on in timesheet 5?",
        "How many days did worker 28 have in september 2025 ?",
        "How many days did worker 28 have in september 2025 per type of work ?",
        "How many days did worker 28 have in october 2025 ?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}: {query} ---")
        try:
            async for message in agent.astream({"messages": [("user", query)]}):
                # Print the agent's response
                response = message.get("tools", {}) or message.get("model", {})
                for msg in response.get("messages", []):
                    if hasattr(msg, "content") and msg.content:
                        print(f"Agent: {msg.content}")
        except Exception as e:
            print(f"Error: {e}")
            print(message)
        print("-" * 50)


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_timesheet_agent())
