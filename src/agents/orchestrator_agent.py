"""Orchestrator Agent. Gets a complex task, splits it, and dispatches the
appropriate agents for each subtask.
"""

import asyncio
from typing import Any

from langchain.agents import AgentState, create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel

from src.agents.invoice_agent import invoice_agent_tool
from src.agents.query_agent import query_agent_tool
from src.agents.validation_agent import validation_agent_tool
from src.format_utils import format_message
from src.llm_config import get_llm
from src.middleware.parse_fail_check import CheckParsingFailureMiddleware
from src.middleware.planning import PlanningMiddleware
from src.middleware.revisor import ToolCallRevisorMiddleware
from src.tools.common_tools import report_stage_results

console = Console()

_subagents_mapping = {
    "query": query_agent_tool,
    "validation": validation_agent_tool,
    "invoice": invoice_agent_tool,
}

subagent_descriptions = [
    f"""
{name}:
{subagent_tool.description}
"""
    for name, subagent_tool in _subagents_mapping.items()
]


ORCHESTRATOR_AGENT_PROMPT = f"""You are the Main Orchestrator - a task decomposition and parallel execution engine.

## Your Role
Break complex tasks into batches of parallel subtasks and dispatch them to specialized subagents.

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

5. **⚠️ MAXIMIZE CONTEXT IN PROMPTS** - Include ALL available details in every prompt:
   ✅ ALWAYS INCLUDE when available:
   - Full worker names (First + Last)
   - Project names/references (CRITICAL - include exact project name from email/context)
   - Time periods (month + year: "September 2025")
   - Client/company names when relevant

   ✅ CORRECT: "How many days did Elodie LEGUAY work on project 'Modernisation Ligne Production - Multi commande' in September 2025?"
   ❌ WRONG: "How many days did Elodie work in Sep 2025?" (missing last name and project name)

   **Why this matters**: Subagents need full context to query correctly, especially project names for accurate data retrieval and validation

## Workflow (3 Steps)

**Step 1: PLAN**
```python
write_todos([
    "Batch 1: Get days for all N workers",
    "Batch 2: Get costs for all N workers",
    "Batch 3: Validate all M workers (where data matched)"
])
```

**Step 2: DISPATCH (Pure Parallel Batches with Full Context)**
```python
# ✅ CORRECT: Pure operation batching WITH FULL CONTEXT
# Batch 1: Get ALL days in parallel (with project names!)
dispatch_tasks(subagent="query", prompts=[
    "How many days did worker A work on project 'Project X' in September 2025?",
    "How many days did worker B work on project 'Project X' in September 2025?",
    "How many days did worker C work on project 'Project Y' in September 2025?"
])
# Results: A=22, B=12, C=20

# Batch 2: Get ALL costs in parallel (with full context)
dispatch_tasks(subagent="query", prompts=[
    "What was total cost for worker A on project 'Project X' in September 2025?",
    "What was total cost for worker B on project 'Project X' in September 2025?",
    "What was total cost for worker C on project 'Project Y' in September 2025?"
])
# Results: A=€14452, B=€7860, C=€13200

# ❌ WRONG: Missing context (no project names, vague references)
dispatch_tasks(subagent="query", prompts=[
    "How many days did worker A work?",  # Missing project!
    "What was total cost for worker A?"  # Also mixing operations!
])
```

**Step 3: REPORT (Mandatory)**
```python
report_stage_results(
    stage_name="Batch 1: Days Verification",
    findings="Retrieved days for 3 workers: A=22j, B=12j, C=20j",
    next_actions="Proceed to Batch 2: Cost verification"
)
```

## Example: Full Parallel Workflow with Maximum Context

```python
# Task: "Verify and validate workers from email: Worker A on Project X (22d, €14452),
#        Worker B on Project X (12d, €7860), Worker C on Project Y (20d, €13200) for Sep 2025"

# BATCH 1: Get ALL days (with FULL context)
dispatch_tasks(subagent="query", prompts=[
    "How many days did worker A work on project 'Project X' in September 2025?",
    "How many days did worker B work on project 'Project X' in September 2025?",
    "How many days did worker C work on project 'Project Y' in September 2025?"
])
# Results: A=22, B=12, C=20

report_stage_results(
    stage_name="Batch 1: Days Verification",
    findings="Worker A: 22j ✓, Worker B: 12j ✓, Worker C: 20j ✓ (all match email)",
    next_actions="Batch 2: Cost verification"
)

# BATCH 2: Get ALL costs (with full context from email)
dispatch_tasks(subagent="query", prompts=[
    "What was total cost for worker A on project 'Project X' in September 2025?",
    "What was total cost for worker B on project 'Project X' in September 2025?",
    "What was total cost for worker C on project 'Project Y' in September 2025?"
])
# Results: A=€14452, B=€7860, C=€13200

report_stage_results(
    stage_name="Batch 2: Costs Verification",
    findings="Worker A: €14452 ✓, Worker B: €7860 ✓, Worker C: €13200 ✓ (all match email)",
    next_actions="Batch 3: Validate all 3 workers with matching data"
)

# BATCH 3: Validate ALL workers (with project context)
dispatch_tasks(subagent="validation", prompts=[
    "Validate timesheet for worker A on project 'Project X' in September 2025",
    "Validate timesheet for worker B on project 'Project X' in September 2025",
    "Validate timesheet for worker C on project 'Project Y' in September 2025"
])

report_stage_results(
    stage_name="Batch 3: Validation Complete",
    findings="Successfully validated 3/3 workers. No errors found.",
    next_actions="All workers verified and validated. Workflow complete."
)
```

## Parallel Batching Rules

**DO**: Batch by operation type WITH FULL CONTEXT
```python
Batch 1: [Get days for A on Project X, B on Project X, C on Project Y]
Batch 2: [Get costs for A on Project X, B on Project X, C on Project Y]
Batch 3: [Validate A on Project X, B on Project X, C on Project Y]
```

**DON'T**: Process sequentially per entity
```python
# Wrong!
Batch 1: [Get days for A, Get cost for A]
Batch 2: [Get days for B, Get cost for B]
```

**DO**: Keep queries open-ended with full context
```python
# Batch 1 returned: Worker A worked 22 days on Project X
# Batch 2: Ask for costs WITHOUT embedding expected values:
"What was total cost for worker A on project 'Project X' in September 2025?"
```

**DON'T**: Mix different operations, omit context, or embed expected values
```python
# Wrong - Different ops!
prompts=["Get days for A", "Get cost for B"]

# Wrong - Missing project context!
"What was total cost for worker A in Sep 2025?"

# Wrong - Includes expected value!
"What was total cost for worker A who worked 22 days on project 'Project X'?"
```

## Invoice Generation Rule

Generate invoices ONLY when:
1. User explicitly requests it, OR
2. After validation completes AND validation agent confirms ALL project workers validated

NEVER auto-generate invoices without checking project completion status first.

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
        tools=[dispatch_tasks, report_stage_results],
        middleware=[
            PlanningMiddleware(),
            ToolCallRevisorMiddleware("dispatch_tasks"),
            CheckParsingFailureMiddleware(),
        ],
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
Verify days worked and totals for each worker in this email.
Validate timesheets for workers where days worked and total is correct.
Give a VERY SIMPLE report of your actions taken and their outcomes.

Hi Dimitri,

Here is the breakdown for the projects at Roche, Veolia and SAUR for September 2025.

- Project

LAST First Name     days worked     total cost

- Modernisation Ligne Production - Multi commande

LEGUAY Elodie       12j             7860
GEIG Didier         22j             14432

""",
    ]

    [
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
    """,
    ]

    query_responses = []

    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}: {query} ---")
        try:
            async for message in agent.astream({"messages": [("user", query)]}, {"recursion_limit": 100}):
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
