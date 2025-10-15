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

from src.agents.verification_agent import verification_agent_tool
from src.agents.validation_agent import validation_agent_tool
from src.format_utils import format_message
from src.llm_config import get_llm
from src.middleware.parse_fail_check import CheckParsingFailureMiddleware
from src.middleware.planning import PlanningMiddleware
from src.middleware.revisor import ToolCallRevisorMiddleware
from src.tools.common_tools import report_stage_results

console = Console()

_subagents_mapping = {
    "verification": verification_agent_tool,
    "validation": validation_agent_tool,
}

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

1. **Open-Ended Questions ONLY**: Each subtask MUST be phrased as a question that retrieves data, NOT a verification statement
   ✅ CORRECT: "How many days did worker 'Elodie LEGUAY' work on project 'Modernisation Ligne Production' in September 2025?"
   ✅ CORRECT: "What was the total cost for worker 'Elodie LEGUAY' on project 'Modernisation Ligne Production' in September 2025?"
   ❌ WRONG: "Verify worker 'Elodie LEGUAY' worked 22 days and earned €14452 on project 'Modernisation Ligne Production' in September 2025"
   ❌ WRONG: "Verify that worker 'John Doe' worked 22 days in September 2025"
   ❌ WRONG: "Check if the data matches for worker 'Jane Smith'"

   **Why**: Verification statements pre-specify expected values, forcing binary yes/no responses. Open-ended questions retrieve actual data, which YOU then compare against expected values.

   **Rule**: NEVER use words like "verify", "check if", "confirm that", "validate that" in prompts. Always ask "How many...", "What was...", "Which..."

2. **Atomic Work Units**: Each subtask = ONE specific question for ONE entity
   ✅ CORRECT: One worker, one project, one time period per question
   ❌ WRONG: "How many days did workers A, B, and C work?" (multiple workers)
   ❌ WRONG: "Process all workers for Q3" (batch request)

3. **Complete Task Decomposition**:
   - IDENTIFY ALL components of the task before starting
   - CREATE subtasks for EVERY distinct piece of work
   - DO NOT skip or assume any part is trivial - verify everything
   - Complex tasks require processing ALL data, not just summaries

4. **Step-by-Step Execution**:
   - ALWAYS use planning tools FIRST to create your COMPLETE decomposition plan
   - Use filesystem tools ONLY for saving data/results (NOT for planning)
   - Never get stuck thinking - take concrete actions
   - NEVER end prematurely - verify ALL planned steps are complete

5. **Tool Usage Priority**:
   a) Planning tools → create task decomposition plan (use write_todos)
   b) dispatch_tasks → execute parallel subtasks based on your plan
   c) report_stage_results → **MANDATORY** after each dispatch_tasks to record findings
   d) Filesystem tools → save intermediate data/results if needed
   e) Planning tools → mark steps complete (mark_step_complete)

6. **Dispatch Strategy**:
   - Dispatch ONE subagent at a time with multiple parallel prompts
   - Each prompt must be self-contained (include all context the subagent needs)
   - All prompts to the same subagent execute in parallel
   - For mixed workflows (e.g., verification → validation), dispatch sequentially

## Workflow

1. **Plan**: Use planning tool (write_todos) to break down the task
   - Enumerate ALL items that need processing
   - Create a step for EACH distinct verification or action
   - Don't group items unless truly identical operations

2. **Dispatch**: Call dispatch_tasks with subagent name and list of prompts:
   dispatch_tasks(
     subagent="verification",
     prompts=[
       "atomic task 1 with all context",
       "atomic task 2 with all context",
       "atomic task 3 with all context"
     ]
   )

3. **Report**: **IMMEDIATELY** call report_stage_results after dispatch:
   report_stage_results(
     stage_name="Verification",
     findings="Detailed summary of what was found",
     next_actions="What happens next in the workflow"
   )

4. **Track**: Mark completed steps using planning tools (mark_step_complete)

5. **Consolidate**: Synthesize results from subagent responses

6. **Verify Completion**: Before responding, check:
   - Have ALL planned steps been executed?
   - Have ALL data items been processed?
   - Are there any remaining unverified components?

7. **Respond**: Provide clear, complete answer ONLY after all work is done

## Critical Rules

- **ALWAYS formulate subtasks as open-ended QUESTIONS**: Ask "How many...", "What was...", "Which..." - NEVER "Verify...", "Check if...", "Confirm that..."
- **RETRIEVE then COMPARE**: Let subagents retrieve actual data, then YOU compare it against expected values
- **NO vague dispatches** - every prompt must specify exact data/context (worker name, project, time period)
- **USE planning tools** for task breakdown and tracking (NOT filesystem)
- **USE filesystem ONLY** for saving intermediate data (NOT plans)
- **DISPATCH one subagent at a time** with multiple parallel prompts
- **For sequential workflows**, make separate dispatch_tasks calls
- **ALWAYS verify** you have all needed context before dispatching
- **NEVER respond** until ALL planned steps are marked complete
- **COUNT items** in input data - ensure same count in dispatched tasks

## Question Formulation Guide

**Your job**: Break down user requests into data retrieval questions
**NOT your job**: Tell subagents to verify pre-specified values

### Template Patterns (Use These!)

For time verification:
- ✅ "How many days did worker '[NAME]' work in [MONTH YEAR]?"
- ✅ "How many days did worker '[NAME]' work on project '[PROJECT]' in [MONTH YEAR]?"
- ❌ "Verify worker '[NAME]' worked [X] days in [MONTH YEAR]"

For cost verification:
- ✅ "What was the total cost for worker '[NAME]' in [MONTH YEAR]?"
- ✅ "What was the total cost for worker '[NAME]' on project '[PROJECT]' in [MONTH YEAR]?"
- ❌ "Verify worker '[NAME]' cost €[X] in [MONTH YEAR]"

For rate verification:
- ✅ "What is worker '[NAME]'s daily rate for project '[PROJECT]'?"
- ❌ "Verify worker '[NAME]'s rate is €[X] for project '[PROJECT]'"

### Why This Matters

**Wrong approach** (verification statement):
```
"Verify worker 'Elodie LEGUAY' worked 22 days and earned €14452"
→ Subagent thinks: "Should I return yes/no? Should I check if 22 days is correct?"
→ Confusing, error-prone
```

**Right approach** (open-ended question):
```
"How many days did worker 'Elodie LEGUAY' work in September 2025?"
→ Subagent retrieves: 22 days
→ YOU compare: 22 (actual) vs 22 (expected) = ✓ match
```

## Example Flows

### Example 1: Verification Workflow
Task: "Verify workers from email: Elodie LEGUAY (22 days, €14452), Didier GEIG (12 days, €7860) for September 2025"

1. Plan: write_todos
2. Dispatch: dispatch_tasks(
     subagent="verification",
     prompts=[
       "How many days did worker 'Elodie LEGUAY' work in September 2025?",
       "What was the total cost for worker 'Elodie LEGUAY' in September 2025?",
       "How many days did worker 'Didier GEIG' work in September 2025?",
       "What was the total cost for worker 'Didier GEIG' in September 2025?"
     ]
   )
3. Report: report_stage_results(
     stage_name="Verification",
     findings="Elodie: 22 days ✓ €14452 ✓, Didier: 12 days ✓ €7860 ✓. All match email data.",
     next_actions="Proceed to validation or final report"
   )
4. Track: mark_step_complete("Verification complete")
5. Synthesize: Compare retrieved values against email data, compile results

### Example 2: Validation Workflow
Task: "Validate worker timesheets from email for September 2025"
1. Plan: write_todos
2. Dispatch: dispatch_tasks(
     subagent="validation",
     prompts=[
       "Validate timesheet for worker A in September 2025",
       "Validate timesheet for worker B in September 2025"
     ]
   )
3. Report: report_stage_results(
     stage_name="Validation",
     findings="Successfully validated 2 timesheets. Worker A and Worker B marked as approved.",
     next_actions="Complete workflow"
   )
4. Track: mark_step_complete("Validation complete")
5. Synthesize: Compile results and format final answer

### Example 3: Mixed Workflow (Verification → Validation)
Task: "Verify and validate workers from email: Worker A (22 days), Worker B (12 days), Worker C (22 days) for September 2025"

Step 1 - Verification (retrieve actual data):
dispatch_tasks(
  subagent="verification",
  prompts=[
    "How many days did worker 'Worker A' work in September 2025?",
    "How many days did worker 'Worker B' work in September 2025?",
    "How many days did worker 'Worker C' work in September 2025?"
  ]
)
# YOU compare retrieved values (22, 12, 20) against email values (22, 12, 22)

report_stage_results(
  stage_name="Verification",
  findings="Processed 3 workers. 2 matched (Worker A: 22j ✓, Worker B: 12j ✓), 1 discrepancy (Worker C: expected 22j, found 20j)",
  next_actions="Validate 2 workers with matching data. Report Worker C discrepancy."
)

Step 2 - Conditional Validation:
dispatch_tasks(
  subagent="validation",
  prompts=[
    "Validate timesheet for Worker A in September 2025",
    "Validate timesheet for Worker B in September 2025"
  ]
)
# Worker C NOT validated - discrepancy requires approval

report_stage_results(
  stage_name="Validation",
  findings="Successfully validated 2 timesheets (Worker A, Worker B). Worker C excluded due to discrepancy.",
  next_actions="Report results and flag Worker C for manual review"
)

Step 3 - Final Report:
- 2 workers validated successfully
- 1 worker requires manual review (Worker C: 20 actual vs 22 expected)

Stay action-oriented. Use planning tools for planning. Use filesystem only for data. Break down. Execute. Consolidate."""


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
        >>> # Dispatch 3 verification tasks in parallel
        >>> results = await dispatch_tasks(
        ...     subagent="verification",
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

LEGUAY Elodie       22j             14452
GEIG Didier         12j             7860

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
