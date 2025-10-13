"""Orchestrator Agent. Gets a complex task, splits it, and dispatches the
appropriate agents for each subtask.
"""

import asyncio
from typing import Any

from deepagents.middleware import FilesystemMiddleware, PlanningMiddleware
from langchain.agents import AgentState, create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph

from src.agents.reconciliation_agent import reconciliation_agent_tool
from src.format_utils import format_message
from src.llm_config import get_llm
from src.middleware.revisor import ToolCallRevisorMiddleware

_subagents_mapping = {"reconciliation": reconciliation_agent_tool}

subagent_descriptions = [
    f"""
{name}:
{subagent_tool.description}
"""
    for name, subagent_tool in _subagents_mapping.items()
]


ORCHESTRATOR_AGENT_PROMPT = f"""You are the Main Orchestrator - a mission-critical task decomposition and dispatch agent.

## Your Role
Break complex tasks into atomic subtasks and dispatch them to specialized subagents.

## Available Subagents
{chr(10).join(subagent_descriptions)}

## Core Principles

1. **Atomic Work Units**: Each subtask = ONE specific open-ended question for ONE subagent
   Example: "reconciliation: How many days did worker 'John Doe' work in September 2025?"
   NOT: "reconciliation: verify worker 'John Doe' worked 22 days in September 2025"
   NOT: "reconciliation: process all workers for Q3"

2. **CRITICAL - Time Period Inclusion**: EVERY dispatch task MUST include the complete time period
   - ALWAYS include month AND year (e.g., "September 2025", "October 2024")
   - Extract time period from user input or context
   - NEVER omit time period from dispatch tasks
   - Example: "How many days did Elodie LEGUAY work in September 2025?" ✅
   - WRONG: "How many days did Elodie LEGUAY work?" ❌ (missing time period)

3. **Complete Task Decomposition**:
   - IDENTIFY ALL components of the task before starting
   - CREATE subtasks for EVERY distinct piece of work
   - DO NOT skip or assume any part is trivial - verify everything
   - Complex tasks require processing ALL data, not just summaries

3. **Step-by-Step Execution**:
   - ALWAYS use planning tools FIRST to create your COMPLETE decomposition plan
   - Use filesystem tools ONLY for saving data/results (NOT for planning)
   - Never get stuck thinking - take concrete actions
   - NEVER end prematurely - verify ALL planned steps are complete

4. **Tool Usage Priority**:
   a) Planning tools → create task decomposition plan (use create_plan, add_step)
   b) dispatch_tasks → execute parallel subtasks based on your plan
   c) Filesystem tools → save intermediate data/results if needed
   d) Planning tools → mark steps complete (mark_step_complete)

5. **Dispatch Strategy**:
   - Group independent subtasks for parallel execution
   - Each prompt must be self-contained (include all context needed)
   - MANDATORY: Include full worker name + time period (month + year) in EVERY task
   - Format: list of tuples: [("subagent_name", "precise instruction with time period"), ...]

## Workflow

1. **Plan**: Use planning tools (create_plan, add_step) to break down the task
   - Enumerate ALL items that need processing
   - Create a step for EACH distinct verification or action
   - Don't group items unless truly identical operations

2. **Dispatch**: Call dispatch_tasks with list of (subagent, prompt) tuples:
   calls=[
     ("reconciliation", "atomic task 1 with all context"),
     ("reconciliation", "atomic task 2 with all context"),
   ]

3. **Track**: Mark completed steps using planning tools (mark_step_complete)

4. **Consolidate**: Synthesize results from subagent responses

5. **Verify Completion**: Before responding, check:
   - Have ALL planned steps been executed?
   - Have ALL data items been processed?
   - Are there any remaining unverified components?

6. **Respond**: Provide clear, complete answer ONLY after all work is done

## Critical Rules

- ALWAYS formulate subtasks as open-ended QUESTIONS, not verification statements
- ASK "How many days did worker X work in [MONTH YEAR]?" NOT "Verify worker X worked Y days"
- **MANDATORY TIME PERIOD**: EVERY dispatch task MUST include month + year (e.g., "September 2025")
- NO vague dispatches - every prompt must specify exact data/context + time period
- USE planning tools for task breakdown and tracking (NOT filesystem)
- USE filesystem ONLY for saving intermediate data (NOT plans)
- PARALLELIZE independent subtasks in single dispatch_tasks call
- ALWAYS verify you have all needed info (including time period) before dispatching
- NEVER respond until ALL planned steps are marked complete
- COUNT items in input data - ensure same count in dispatched tasks

## Example Flow

Task: "Check worker hours from email for September"
1. Plan: create_plan("Check worker hours")
        add_step("Extract worker data from input")
        add_step("Dispatch open-ended reconciliation queries")
        add_step("Synthesize results")
2. Dispatch: dispatch_tasks(calls=[
     ("reconciliation", "How many days did worker A work on project Y in September 2025?"),
     ("reconciliation", "How many days did worker B work on project Y in September 2025?"),
     ("reconciliation", "How many days did worker C work on project Y in September 2025?")
   ])
3. Track: mark_step_complete("Dispatch reconciliation tasks")
4. Synthesize: Compile results and format final answer

Stay action-oriented. Use planning tools for planning. Use filesystem only for data. Break down. Execute. Consolidate."""


@tool(parse_docstring=True)
async def dispatch_tasks(calls: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    Call subagents in parallel.

    Args:
        calls (list[tuple[str, str]]): list of tuples of (subagent_name, prompt).
            This is the list of subagents to call, associated with their prompts.
            Invokes subagent calls[0][0] with prompt calls[0][1], then
            calls[1][0] with prompt calls[1][1], etc...

    Raises:
        ValueError: List of subagents and prompts must be of same length to be
            zipped together.

    Returns:
        list[tuple[str, str]]: list of (prompt, result)
    """

    results = []
    for subagent, prompt in calls:
        ret = await _subagents_mapping.get(subagent).ainvoke({"prompt": prompt})
        results.append((prompt, ret))

    return results


def create_orchestrator_agent(
    model: BaseChatModel | None = None,
) -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
    """Create an orchestrator agent with all available subagents.

    Args:
        model: LLM model to use. If None, uses default from llm_config.

    Returns:
        Configured LangGraph agent ready to handle user queries.
    """
    if model is None:
        model = get_llm()

    agent = create_agent(
        model,
        tools=[dispatch_tasks],
        middleware=[PlanningMiddleware(), FilesystemMiddleware(), ToolCallRevisorMiddleware("dispatch_tasks")],
        system_prompt=ORCHESTRATOR_AGENT_PROMPT,
    )

    return agent


async def demo_orchestrator_agent():
    """Demo function to test the project agent with example queries."""
    print("=== BoondManager Orchestrator Agent Demo ===\n")

    agent = create_orchestrator_agent()

    # Example queries
    queries = [
        """
Verify days worked and totals for each worker in this email:

Hi Dimitri,

Here is the breakdown for the projects at Roche, Veolia and SAUR.

- Project

LAST First Name     days worked     total cost

- Modernisation Ligne Production - Multi commande

LEGUAY Elodie       22j             14452
GEIG Didier         12j             7860

"""
"""

- Migration Cloud AWS - Tps partiel

LEVIN Jon           7j              4606


- Application Mobile Interne - Basic

RENEE ZHAO Ruike    21j             15400
LEVIN Jon           15j             11370
DENECE Philippe     22j             14454
FINN Chelsea        17j             11917
LEVY Daniel         22j             15400


Total:                              95459

Feel free to reach out.

Best,

Alexis.
""",]

    query_responses = []

    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}: {query} ---")
        try:
            async for message in agent.astream({"messages": [("user", query)]}):
                # # Print the agent's response
                response = message.get("tools", {}) or message.get("model", {})
                for msg in response.get("messages", []):
                    format_message(msg)
                    # if hasattr(msg, "content") and msg.content:
                    #     print(f"Agent: {msg.content}")
        except Exception as e:
            print(f"Error: {e}")
            print(message)

        query_responses.append((query, msg.content))

        print("-" * 50)

    from pprint import pprint

    pprint(query_responses)


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_orchestrator_agent())
