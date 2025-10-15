"""Planner Agent - Transforms user queries into clear, actionable work instructions.

This agent analyzes user queries and reformulates them into direct, unambiguous instructions
that can be executed by other agents. It extracts structure from vague requests and makes
implicit requirements explicit.
"""

import asyncio
from typing import Any

from langchain.agents import AgentState
from langchain.tools.tool_node import _ToolNode
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph

from src.llm_config import get_llm
from src.middleware.planning import Todo, write_todos

PLANNER = "planner"
CRITIC = "critic"
TRANSFORM = "transform"
TOOL_CALL = "tool_call"

PLANNER_AGENT_PROMPT = """You are a strategic planner for HR workflow automation that creates simple, executable task lists from user requests.

## System Context
You operate within an HR department that uses:
- **BoondManager CRM**: Cloud-based CRM for managing consultants, projects, timesheets (CRA/times-reports), invoices, and client relationships
- **Primary workflows**: Timesheet validation, invoice generation, consultant activity tracking, project management
- **Key entities in BoondManager**: Resources (workers/consultants), Projects, Timesheets (times-reports), Deliveries (work assignments), Orders, Invoices, Companies (clients), Contacts
- **Common operations**: Reconcile email data with CRA data, validate timesheets, generate invoices, send notifications

## Available Subagents

Your task lists will be executed by an orchestrator that delegates to specialized subagents. Keep tasks at a **business logic level**, not technical implementation:

**verification**: Matches external data (emails, reports) with internal BoondManager data. Handles queries like "verify worker X worked Y days on project Z" or "find matching timesheet data for workers in email"

**validation**: Validates timesheets and orders to mark them ready for billing. Handles validation workflows that are prerequisites for invoicing.

**invoice**: Fetches and analyzes invoice data from BoondManager. Searches invoices, retrieves details, and provides financial information.

**Note**: Do NOT specify API endpoints, function calls, or technical implementation details. The subagents will handle all technical operations.

## Your Role
Transform user requests into simple, actionable task lists.
Extract intent → Identify concrete tasks → Output bullet points only.

## Information Retrieval
If you need information about company processes, workflows, or standard procedures:
- Ask specific questions about the process (e.g., "What is the standard process for email validation?")
- Your questions will be answered with relevant process documentation
- Use this information to create task lists that follow company standards

## Output Format: SIMPLE BULLET POINTS ONLY

Your output must be a simple bullet-point list of tasks. NO elaborate sections, NO verbose explanations.

### Format Requirements:
- Use simple bullet points (-)
- One task per line
- Keep tasks specific and actionable
- Include key entities (names, dates, IDs) inline
- Mark parallel-capable tasks with [parallel]
- Mark sequential dependencies with [after: task X]

### Example Output

Given: "Verify and validate workers from Alexis's email for September 2025"

- Extract worker data from email: names, days worked, amounts, projects
- Verify each worker's email data against BoondManager timesheet records for September 2025 [parallel per worker]
- Validate timesheets for workers where data matches [parallel per worker]
- Generate verification report: successful validations and mismatches

---

## Transformation Rules
1. **Be Specific**: Include exact names, dates, values, operations
2. **Keep It Simple**: Direct bullet points, no elaborate formatting
3. **No Vague Terms**: Use concrete entities
4. **Show Dependencies**: Use [parallel] or [after: X] annotations
5. **One Task Per Line**: Each bullet is one actionable step
6. **Business Logic Level**: Describe WHAT needs to be done, not HOW (no API endpoints, function names, or technical implementation)

## Output Instructions

Your output should follow one of these formats:

### If you need process information:
Start your response with: "QUESTION: [your specific question about company process]"
Example: "QUESTION: What is the standard process for validating worker timesheets from email?"

### If you have enough information:
Provide ONLY a simple bullet-point task list. Do not call any tools.
If the user request is unclear, add a "CLARIFICATIONS NEEDED:" section with bullet-point questions.

### What NOT to do:
- ❌ NO elaborate section headers like "OBJECTIVE", "CONTEXT", "EXECUTION STEPS"
- ❌ NO verbose explanations or paragraphs
- ❌ NO nested sub-bullets or complex formatting
- ✅ YES simple, flat bullet-point list of tasks
"""

CRITIQUE_PROMPT = """You are a process knowledge expert and task list reviewer for an HR department using BoondManager CRM. You have two roles:

## Role 1: Answer Process Questions (RAG Simulation)
When the planner asks "QUESTION: [...]", provide relevant process documentation.

## Role 2: Critique Task Lists
When the planner provides a task list, analyze it against the original user request and company processes.
Be constructive but thorough: catch missing tasks, unnecessary steps, unclear instructions, and logical issues.

Remember: The planner should output SIMPLE BULLET POINTS ONLY, not elaborate sections.

## Company Process Knowledge

You have access to documented company processes. Validate that task lists follow these processes:

### EMAIL VALIDATION PROCESS
For email validation requests, the standard process is:
1. **Verify Data**: Compare data from email with data from internal database
   - Extract worker names, days worked, and totals from email
   - Query internal database for each worker's actual records
   - Compare email values vs database values for each worker
2. **Validate Matching Workers**: For each worker where verification data matches:
   - Validate the worker's timesheet in the system
   - Mark as validated/approved
3. **Generate Report**: Create a comprehensive report containing:
   - List of workers with failed verifications (mismatches between email and database)
   - List of workers with validated timesheets (successful validation)
   - Clear summary of actions taken and outcomes

**Important Process Rules:**
- Verification MUST happen before validation
- Only workers with matching data should be validated
- Workers with mismatches should NOT be validated automatically
- Report must clearly separate failed verifications from successful validations

## Critique Framework

Evaluate the task list across these dimensions:

### 1. COMPLETENESS
- Does the task list address all aspects of the user request?
- Are there implicit requirements that were missed?
- Are all necessary entities, data points, and operations included?

### 2. CLARITY
- Are the tasks specific and actionable?
- Does each task have sufficient context (WHO, WHAT, WHEN, WHERE)?
- Are dependencies between tasks clearly marked with [parallel] or [after: X]?
- Can an executor follow this list without additional clarification?

### 3. CORRECTNESS
- Are the tasks logically ordered?
- Do the tasks actually achieve the stated objective?
- Are parallel vs sequential designations correct?
- Does the list follow BoondManager workflow standards?

### 4. SIMPLICITY
- Is the output a simple bullet-point list (not elaborate sections)?
- Are tasks atomic and actionable?
- Is formatting clean and minimal?

### 5. ABSTRACTION LEVEL
- Are tasks at business logic level (WHAT) rather than implementation level (HOW)?
- Are there any API endpoints, function calls, or technical details that should be removed?
- Do tasks delegate properly to subagents without specifying their internal operations?

### 6. BOONDMANAGER ALIGNMENT
- Do tasks correctly reference BoondManager entities (Resources, Projects, Timesheets, etc.)?
- Does the workflow follow documented company processes?

## Output Format

Structure your critique as follows:

### STRENGTHS
What the task list does well (be specific)

### ISSUES FOUND

**Completeness Issues:**
- [List missing tasks, entities, or operations]

**Clarity Issues:**
- [List ambiguous or underspecified tasks]

**Correctness Issues:**
- [List logical errors, wrong ordering, or incorrect dependencies]

**Simplicity Issues:**
- [Flag if output uses elaborate sections instead of simple bullets]

**Abstraction Level Issues:**
- [Flag tasks with API endpoints, function calls, or technical implementation details]

**BoondManager Issues:**
- [Flag incorrect entity references or workflow violations]

### RECOMMENDED IMPROVEMENTS
Concrete suggestions for enhancing the task list:
1. [Specific actionable improvement]
2. [Specific actionable improvement]
...

---

## Output Format

### If responding to a QUESTION:
Provide the relevant process documentation directly.
Start with: "ANSWER: " followed by the process information.
Do NOT critique - just answer the question.

### If critiquing a plan:
- If the plan is excellent and needs no improvements, write exactly: "000-NO_CRITIQUE-000"
- Otherwise, provide detailed, actionable feedback in the format above
- Quote specific parts of the plan when identifying issues
- Do NOT call any tools, only respond with text
- Focus on substance over style: missing logic matters more than formatting
"""

tools = [write_todos]
tools_dict = {t.name: t for t in tools}
tool_node = _ToolNode(tools)


class PlannerState(AgentState):
    """State for the reflexion planner agent.

    Tracks the user's original request, the evolving plan through critique cycles,
    and the final todos once the plan is finalized.
    """

    prompt: str  # Original user request
    plan: str  # Current plan text
    critique_count: int  # Number of critique cycles completed
    todos: list[Todo]  # Final todos (generated after plan is approved)


def planner(state: PlannerState):
    """Generate or refine a task list based on user request and any previous critique or answers.

    On first call: generates initial task list from user request (may ask questions)
    On subsequent calls: refines task list based on critic's feedback or incorporates answered information
    """
    model = get_llm()

    messages = [SystemMessage(PLANNER_AGENT_PROMPT), HumanMessage(state["prompt"])]

    # Check if we have any feedback from the critic (answer or critique)
    if len(state.get("messages", [])) > 0:
        # Find the last critic message (could be answer or critique)
        last_critic_msg = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and (
                "ANSWER:" in msg.content
                or "STRENGTHS" in msg.content
                or "ISSUES FOUND" in msg.content
            ):
                last_critic_msg = msg
                break

        if last_critic_msg:
            # Check if it's an answer to a question
            if "ANSWER:" in last_critic_msg.content:
                messages.append(
                    HumanMessage(f"Your question was answered:\n\n{last_critic_msg.content}")
                )
                messages.append(
                    HumanMessage(
                        "Now create a complete task list using this process information. Remember: simple bullet points only."
                    )
                )
            else:
                # It's a critique - include the previous task list
                if state.get("plan") is not None:
                    messages.append(
                        HumanMessage(f"Here is your previous task list:\n\n{state['plan']}")
                    )
                messages.append(HumanMessage(f"Here is the critique:\n\n{last_critic_msg.content}"))
                messages.append(
                    HumanMessage(
                        "Please revise the task list addressing the critique feedback. Remember: simple bullet points only."
                    )
                )

    response = model.invoke(messages)

    # Update plan only if it's not a question
    new_plan = state.get("plan", "")
    if "QUESTION:" not in response.content:
        new_plan = response.content

    return {
        "messages": [response],
        "plan": new_plan,
    }


def critic(state: PlannerState):
    """Answer planner questions OR evaluate task lists.

    Role 1 (Q&A): If planner asked a question, provide process documentation
    Role 2 (Critique): If planner provided a task list, review for completeness and compliance

    Returns either process answer, detailed critique, or approval signal.
    """
    model = get_llm()

    # Get the last planner message
    last_planner_msg = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage):
            last_planner_msg = msg
            break

    # Check if planner asked a question
    if last_planner_msg and "QUESTION:" in last_planner_msg.content:
        # Extract the question
        question = last_planner_msg.content

        response = model.invoke(
            [
                SystemMessage(CRITIQUE_PROMPT),
                HumanMessage(f"Original user request:\n\n{state['prompt']}"),
                HumanMessage(f"Planner's question:\n\n{question}"),
                HumanMessage(
                    "Please provide the relevant process documentation to answer this question."
                ),
            ]
        )

        # Don't increment count for Q&A, only for critiques
        return {
            "messages": [response],
        }

    # Otherwise, critique the task list
    response = model.invoke(
        [
            SystemMessage(CRITIQUE_PROMPT),
            HumanMessage(f"Original user request:\n\n{state['prompt']}"),
            HumanMessage(f"Generated task list:\n\n{state['plan']}"),
        ]
    )

    # Increment critique count only for actual critiques
    new_count = state.get("critique_count", 0) + 1

    return {
        "messages": [response],
        "critique_count": new_count,
    }


def should_continue_planning(state: PlannerState) -> str:
    """Determine if we should continue refining or finalize the task list.

    Returns:
        - TRANSFORM: if task list is approved (no critique) or max iterations reached
        - PLANNER: if task list needs refinement (either critique feedback or answered question)
    """
    last_message = state["messages"][-1]
    critique_count = state.get("critique_count", 0)

    # Check if this was an answer to a question (RAG simulation)
    if "ANSWER:" in last_message.content:
        print("💡 Process information provided, planner will incorporate it\n")
        return PLANNER

    # Check if critic approved the task list
    if "000-NO_CRITIQUE-000" in last_message.content:
        print(f"✓ Task list approved after {critique_count} critique(s)\n")
        return TRANSFORM

    # Check if we've hit max iterations (prevent infinite loops)
    MAX_CRITIQUES = 3
    if critique_count >= MAX_CRITIQUES:
        print(f"⚠ Max iterations ({MAX_CRITIQUES}) reached, proceeding to transform\n")
        return TRANSFORM

    print(f"↻ Refining task list (iteration {critique_count}/{MAX_CRITIQUES})\n")
    return PLANNER


def transform_plan_to_todos(state: PlannerState):
    """Transform the finalized plan into structured todos.

    Extracts execution steps from the plan and converts them into
    actionable todo items with appropriate status.
    """
    model = get_llm().bind_tools(tools)

    response = model.invoke(
        [
            SystemMessage(
                """You are converting a finalized task list into structured todos.

Extract each bullet-point task from the list and create a todo item for it.
Maintain the order and dependency information from the task list.
Set the first todo(s) as 'in_progress' and the rest as 'pending'.

Each todo should be:
- Specific and actionable
- Include relevant context from the task list (names, dates, entities)
- Marked with appropriate status

You MUST call the write_todos tool with the extracted todos."""
            ),
            HumanMessage(f"Original request:\n{state['prompt']}"),
            HumanMessage(f"Finalized task list:\n\n{state['plan']}"),
            HumanMessage(
                "Convert this task list into structured todos using the write_todos tool."
            ),
        ]
    )

    return {"messages": [response]}


def create_planner_graph() -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
    """Create a planner agent with reflexion loop: planner → critic → planner → transform.

    The reflexion loop allows the planner to iteratively refine the plan based on
    critic feedback until the plan meets quality standards or max iterations reached.

    Flow:
        1. START → PLANNER: Generate initial plan
        2. PLANNER → CRITIC: Evaluate plan quality
        3. CRITIC → [PLANNER or TRANSFORM]: Refine or finalize
        4. TRANSFORM → TOOL_CALL: Convert plan to todos
        5. TOOL_CALL → END: Execute write_todos and complete

    Returns:
        Configured LangGraph agent ready to analyze and reformulate queries.
    """

    builder = StateGraph(PlannerState)

    # Add nodes for reflexion loop
    builder.add_node(PLANNER, planner)
    builder.add_node(CRITIC, critic)
    builder.add_node(TRANSFORM, transform_plan_to_todos)
    builder.add_node(TOOL_CALL, tool_node)

    # Build reflexion loop: planner → critic → [planner or transform]
    builder.add_edge(START, PLANNER)
    builder.add_edge(PLANNER, CRITIC)
    builder.add_conditional_edges(
        CRITIC,
        should_continue_planning,
    )
    builder.add_edge(TRANSFORM, TOOL_CALL)
    builder.add_edge(TOOL_CALL, END)

    graph = builder.compile()

    return graph


async def demo_planner_agent():
    """Demo function to test the planner agent with example queries."""
    print("=== BoondManager Planner Agent Demo ===\n")

    agent = create_planner_graph()

    # Example queries - from vague to specific
    queries = [
        # Complex query with data
        """Verify and validate these workers from Alexis's email:

Hi Dimitri,

Here is the breakdown for the projects for September 2025.

- Project: Modernisation Ligne Production - Multi commande

LEGUAY Elodie       22j             14452
GEIG Didier         12j             7860

- Project: Migration Cloud AWS - Tps partiel

LEVIN Jon           7j              4606

- Project: Application Mobile Interne - Basic

RENEE ZHAO Ruike    21j             15400
LEVIN Jon           15j             11370
DENECE Philippe     22j             14454
FINN Chelsea        17j             11917
LEVY Daniel         22j             15400

Total:                              95459

Best,
Alexis.
""",
        # # Ambiguous query
        # "Handle the timesheet stuff for this month",
    ]

    query_responses = []

    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 70}")
        print(f"Query {i}:")
        print(f"{'=' * 70}")
        print(query[:200] + "..." if len(query) > 200 else query)
        print(f"{'=' * 70}\n")

        try:
            async for message in agent.astream(
                {"prompt": query},
                stream_mode="updates",
            ):
                print(message)
                print("\n")
                # response = message.get("tools", {}) or message.get("model", {})
                # for msg in response.get("messages", []):
                #     format_message(msg)
        except Exception as e:
            print(f"Error: {e}")
            print(message)

        # query_responses.append((query[:100], msg.content[:500]))
        print("-" * 70)

    print("\n\n=== Summary ===\n")
    for i, (query, response) in enumerate(query_responses, 1):
        print(f"\nQuery {i}: {query}...")
        print(f"Response preview: {response}...\n")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_planner_agent())
