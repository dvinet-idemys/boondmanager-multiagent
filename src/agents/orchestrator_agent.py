"""Orchestrator Agent. Gets a complex task, splits it, and dispatches the
appropriate agents for each subtask.
"""

import asyncio
from typing import Any

from langchain.agents import AgentState, create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel

from src.agents.emailing_agent import emailing_agent_tool
from src.agents.invoice_agent import invoice_agent_tool
from src.agents.query_agent import query_agent_tool
from src.agents.validation_agent import validation_agent_tool
from src.format_utils import format_message
from src.llm_config import get_llm
from src.middleware.parse_fail_check import CheckParsingFailureMiddleware
from src.middleware.planning import PlanningMiddleware
from src.middleware.revisor import ToolCallRevisorMiddleware
from src.tools.common_tools import report_stage_results
from src.utils import invoke_and_print_agent

console = Console()

_subagents_mapping = {
    "query": query_agent_tool,
    "validation": validation_agent_tool,
    "invoice": invoice_agent_tool,
    "emailing": emailing_agent_tool,
}

subagent_descriptions = [
    f"""
{name}:
{subagent_tool.description}
"""
    for name, subagent_tool in _subagents_mapping.items()
]


ORCHESTRATOR_AGENT_PROMPT = f"""You are the Main Orchestrator - a task decomposition and parallel execution engine with expert prompt engineering capabilities.

## ⚠️ SYSTEM CONSTRAINTS

You cannot directly interact with the outside world. You cannot:
- Send emails directly to workers, clients, or managers
- Access external systems like email servers or databases
- Perform operations outside this orchestration environment

For any external interactions (emails, notifications, etc.), you MUST route through specialized subagents that interface with external systems. These subagents manage the actual external operations and handle things like draft creation for human review.

## Your Role
Break complex tasks into batches of parallel subtasks and dispatch them to specialized subagents.

## 🎯 CRITICAL: You are an Expert Prompt Engineer

**Important**: All subagents you dispatch to are ChatGPT-based language models (OpenAI API). Your success depends on crafting effective prompts that follow ChatGPT prompting best practices.

### ChatGPT Prompting Guidelines:

1. **Be Explicit and Detailed**: ChatGPT models need clear, comprehensive instructions
   - Include ALL relevant context in every prompt
   - Don't assume the model will infer missing information
   - Specify expected output format when needed

2. **Provide Complete Information**: Don't rely on brevity
   - Multi-line prompts with full details are BETTER than short vague ones
   - Include all data, constraints, and requirements upfront
   - For tasks (emails, reports), provide complete instructions

3. **Use Structured Instructions**: When tasks are complex
   - Break down what you need the subagent to do
   - Specify tone, format, required elements
   - Give examples when helpful

4. **Context is King**: ChatGPT performs better with more context
   - Full names, dates, project details, specific values
   - Background information that aids understanding
   - Relevant data from previous steps

### Prompt Quality Examples:

❌ **BAD** (too vague): "Email worker about issue"
✅ **GOOD** (detailed): "Draft an email to Elodie LEGUAY (elodie.leguay@example.com) regarding her timesheet discrepancy for project 'Modernisation Ligne Production - Multi commande' in September 2025. Our records show she worked 15 days, but the client email reported 12 days. Ask her to review her timesheet and provide clarification. Use a professional but friendly tone. Include the project name and time period in the email for clarity."

❌ **BAD** (missing context): "Check days for worker"
✅ **GOOD** (complete context): "How many days did Elodie LEGUAY work on project 'Modernisation Ligne Production - Multi commande' in September 2025 according to BoondManager CRA records?"

## Available Subagents
{chr(10).join(subagent_descriptions)}

## 🔴 CRITICAL RULES

1. **ALWAYS ask open-ended questions** - NEVER "verify", "check if", "confirm that"
   ✅ CORRECT: "How many days did worker X work in Sep 2025?"
   ❌ WRONG: "Verify worker X worked 22 days"

2. **PURELY PARALLEL batching** - Group by operation type, NOT by entity
   ✅ CORRECT: Get ALL days → Get ALL costs → Validate ALL workers
   ❌ WRONG: Get days for A → Get cost for A → Validate A → Get days for B...

3. **DO NOT include expected values in queries** - Ask open-ended questions only
   ✅ CORRECT: "What was total cost for worker X on project Y in September 2025?"
   ❌ WRONG: "What was total cost for worker X who worked 22 days on project Y?"

4. **MANDATORY after EVERY dispatch_tasks**: Call report_stage_results immediately

5. **🔴 DATA DEPENDENCIES** - Query data BEFORE using it:
   - ❌ NEVER fabricate/assume data (email addresses, costs, dates)
   - ✅ ALWAYS query unknown data first, THEN use results in next step
   - Example: Query email → THEN draft email with actual address

6. **PER-ENTITY TASKS** - "workers with X" means ONE task per worker:
   - ✅ CORRECT: ["Email worker A about X", "Email worker B about Y"]
   - ❌ WRONG: ["Email workers A and B about X and Y"]

7. **⚠️ MAXIMIZE CONTEXT IN PROMPTS** - Include ALL available details in every prompt:
   ✅ ALWAYS INCLUDE when available:
   - Full worker names (First + Last)
   - Project names/references (CRITICAL - include exact project name from email/context)
   - Time periods (month + year: "September 2025")
   - Client/company names when relevant

   ✅ CORRECT: "How many days did Elodie LEGUAY work on project 'Modernisation Ligne Production - Multi commande' in September 2025?"
   ❌ WRONG: "How many days did Elodie work in Sep 2025?" (missing last name and project name)

   **Why this matters**: Subagents need full context to query correctly, especially project names for accurate data retrieval and validation

## Workflow Pattern

1. **PLAN**: write_todos (identify ALL subtasks, check for data dependencies)
2. **DISPATCH**: dispatch_tasks (parallel batches by operation type)
3. **REPORT**: report_stage_results (MANDATORY after each dispatch)

Repeat steps 2-3 for each todo. Query dependencies FIRST, then use results.

Generate invoices ONLY when explicitly requested.
Stay action-oriented. Batch by operation type. Execute in parallel."""


@tool(parse_docstring=True)
async def dispatch_tasks(subagent: str, prompts: list[str]) -> list[tuple[str, str]]:
    """
    Dispatch multiple prompts to the same subagent in parallel.

    This tool enables parallel execution of independent tasks to the same specialized
    subagent. Use this to maximize efficiency when multiple similar operations can
    be performed concurrently.

    Args:
        subagent (str): Name of the subagent to dispatch tasks to.
            Must be one of the available subagents (e.g., "verification", "validation").
        prompts (list[str]): List of independent prompts to send to the subagent.
            Each prompt should be self-contained with all necessary context.
            All prompts will be executed in parallel.

    Returns:
        list[tuple[str, str]]: List of (prompt, result) tuples, where each tuple
            contains the original prompt and the subagent's response.

    Example:
        >>> # Dispatch 3 query tasks in parallel
        >>> results = await dispatch_tasks(
        ...     subagent="query",
        ...     prompts=[
        ...         "How many days did Worker A work in September 2025?",
        ...         "How many days did Worker B work in September 2025?",
        ...         "How many days did Worker C work in September 2025?"
        ...     ]
        ... )
    """
    if subagent not in _subagents_mapping:
        raise ValueError(
            f"Unknown subagent '{subagent}'. Available: {list(_subagents_mapping.keys())}"
        )

    subagent_tool = _subagents_mapping[subagent]
    results = []

    # Execute prompts sequentially for proper console output timing
    for i, prompt in enumerate(prompts, 1):
        console.print(
            Padding(
                Panel(
                    prompt,
                    title=f"📝 Prompt {i}/{len(prompts)} → {subagent}",
                    border_style="purple",
                ),
                pad=(0, 0, 0, 0),
            )
        )

        ret = await subagent_tool.ainvoke({"prompt": prompt})
        results.append((prompt, ret))

    return (
        "\n".join(f"{p}: {r}" for p, r in results)
        + "\n\n"
        + "Call report_stage_results to report your findings."
    )
    # return results


def create_orchestrator_agent(
    model: BaseChatModel | None = None,
    checkpointer=None,
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
        tools=[dispatch_tasks, report_stage_results],
        middleware=[
            PlanningMiddleware(),
            ToolCallRevisorMiddleware("dispatch_tasks"),
            CheckParsingFailureMiddleware(),
        ],
        system_prompt=ORCHESTRATOR_AGENT_PROMPT,
        checkpointer=checkpointer,
    )

    return agent


EMAIL = """
Hi Dimitri,

Here is the breakdown for the projects at Roche, Veolia and SAUR for September 2025.

- Project

LAST First Name     days worked     total cost

- Modernisation Ligne Production - Multi commande

LEGUAY Elodie       12j             7860
GEIG Didier         22j             14432
"""


async def demo_orchestrator_agent():
    """Demo function to test the project agent with example queries."""
    print("=== BoondManager Orchestrator Agent Demo ===\n")

    agent = create_orchestrator_agent(checkpointer=InMemorySaver())

    # Example queries
    queries = [
        #         f"""
        # Verify days worked and totals for each worker in this email.
        # {EMAIL}
        # """,
        #         f"""
        # Validate timesheets when days worked and totals match.
        # Query results:
        # LEGUAY Elodie       12j             7860
        # GEIG Didier         22j             14432
        # Original Email:
        # {EMAIL}
        # """,
        #         f"""
        # Validate timesheets when days worked and totals match.
        # Query results:
        # LEGUAY Elodie       15j             7860
        # GEIG Didier         22j             14432
        # Original Email:
        # {EMAIL}
        # """,
        # f"""
        # Generate invoices for projects in this email. Check that each worker's timesheet
        # were validated. Only generate invoices for projects where all timesheets were
        # validated.
        # Original Email:
        # {EMAIL}
        # """,
        f"""
Draft and send end an email to the workers with mismatches to ask for clarification. Ensure
correct email address.

# Query results:
# LEGUAY Elodie       15j             7860
# GEIG Didier         22j             14432

Original Email:
{EMAIL}
""",
    ]

    query_responses = []

    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}: {query} ---")
        await invoke_and_print_agent(agent, query)
        print("hi, i fixed my timsheet. can you recheck please ?")
        await invoke_and_print_agent(agent, "hi, i fixed my timsheet. can you recheck please ?")
        # try:
            # async for message in agent.astream(
            #     {"messages": [("user", query)]}, {"recursion_limit": 100}
            # ):
            #     # # Print the agent's response
            #     response = message.get("tools", {}) or message.get("model", {})
            #     for msg in response.get("messages", []):
            #         format_message(msg)
            #         # if hasattr(msg, "content") and msg.content:
            #         #     print(f"Agent: {msg.content}")
        # except Exception as e:
        #     print(f"Error: {e}")

        print("-" * 50)

    from pprint import pprint

    pprint(query_responses)


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_orchestrator_agent())
