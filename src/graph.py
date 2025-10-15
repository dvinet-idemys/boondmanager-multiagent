"""Main LangGraph workflow: Planner and Orchestrator.

This module defines the primary workflow graph that combines planning and execution:
1. Planner Agent: Analyzes user query and creates structured task list
2. Orchestrator Agent: Executes the task list by dispatching to specialized subagents
"""

from typing import Any

from langchain.agents import AgentState
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.orchestrator_agent import create_orchestrator_agent
from src.agents.planner_agent import create_planner_graph
from src.middleware.planning import Todo

PLANNER = "planner"
ORCHESTRATOR = "orchestrator"


class WorkflowState(AgentState):
    """State for the main workflow combining planner and orchestrator.

    Attributes:
        prompt: Original user request
        plan: Generated task list from planner
        todos: Structured todos extracted from plan
        messages: Conversation history for orchestrator execution
    """

    prompt: str
    plan: str
    todos: list[Todo]


async def run_planner(state: WorkflowState) -> dict[str, Any]:
    """Execute the planner agent to create task list from user query.

    The planner uses a reflexion loop (planner � critic � refine) to generate
    a high-quality task list, then transforms it into structured todos.

    Args:
        state: Current workflow state with user prompt

    Returns:
        Updated state with plan and todos
    """
    planner_graph = create_planner_graph()

    # Run planner agent to completion
    result = await planner_graph.ainvoke({"prompt": state["prompt"]})

    plan = result.get("plan", "")
    if not plan:
        raise RuntimeError("No valid plan from planner.")

    todos = result.get("todos", [])
    if not todos:
        raise RuntimeError("No valid todos from planner.")

    return {
        "plan": plan,
        "todos": todos,
    }


async def run_orchestrator(state: WorkflowState) -> dict[str, Any]:
    """Execute the orchestrator agent to fulfill the planned tasks.

    The orchestrator receives the task list and dispatches work to specialized
    subagents (verification, validation, invoice) based on task requirements.

    Args:
        state: Current workflow state with plan and todos

    Returns:
        Updated state with orchestrator execution results
    """
    orchestrator_graph = create_orchestrator_agent()

    # Prepare orchestrator input with the plan
    orchestrator_prompt = f"""Execute the following task list:

{state['plan']}

Original request: {state['prompt']}
"""

    # Initialize messages for orchestrator if not present
    messages = state.get("messages", [])
    messages.append(HumanMessage(content=orchestrator_prompt))

    # Run orchestrator agent
    result = await orchestrator_graph.ainvoke(state)

    return {
        "messages": result.get("messages", []),
    }


def create_workflow_graph() -> CompiledStateGraph[WorkflowState, Any, WorkflowState, WorkflowState]:
    """Create the main workflow graph: Planner & Orchestrator.

    This creates a simple sequential workflow:
    1. START PLANNER: Analyze query and create task list
    2. PLANNER ORCHESTRATOR: Execute tasks via specialized subagents
    3. ORCHESTRATOR END: Complete workflow and return results

    Returns:
        Compiled LangGraph workflow ready to process user queries
    """
    builder = StateGraph(WorkflowState)

    # Add nodes
    builder.add_node(PLANNER, run_planner)
    builder.add_node(ORCHESTRATOR, run_orchestrator)

    # Build sequential flow: planner -> orchestrator
    builder.add_edge(START, PLANNER)
    builder.add_edge(PLANNER, ORCHESTRATOR)
    builder.add_edge(ORCHESTRATOR, END)

    graph = builder.compile()

    return graph


async def main():
    """Demo function to test the complete workflow."""
    print("=== BoondManager Workflow: Planner & Orchestrator ===\n")

    workflow = create_workflow_graph()

    # Example query
    query = """Verify and validate these workers from Alexis's email:

Hi Dimitri,

Here is the breakdown for the projects for September 2025.

- Project: Modernisation Ligne Production - Multi commande

LEGUAY Elodie       22j             14452
GEIG Didier         12j             7860

- Project: Migration Cloud AWS - Tps partiel

LEVIN Jon           7j              4606

Total:                              26918

Best,
Alexis.
"""

    print(f"Query:\n{query}\n")
    print("=" * 70)

    # Run workflow
    result = await workflow.ainvoke({"prompt": query}, {"recursion_limit": 100})

    print("\n" + "=" * 70)
    print("Workflow Complete!")
    print(f"\nPlan:\n{result.get('plan', 'N/A')}")
    print(f"\nTodos: {len(result.get('todos', []))} tasks")
    print(f"\nMessages: {len(result.get('messages', []))} exchanges")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
