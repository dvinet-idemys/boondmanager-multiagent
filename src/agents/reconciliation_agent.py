import asyncio
from typing import Any

from langchain.agents import AgentState, create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph

from src.agents.project_agent import project_agent_tool
from src.agents.resource_agent import resource_agent_tool
from src.agents.timesheet_agent import timesheet_agent_tool
from src.format_utils import format_message
from src.llm_config import get_llm
from src.tools.common_tools import total_cost

PROJECT_AGENT_PROMPT = """You are a specialized agent for requesting data from various subagents handling data from BoondManager CRM.

Your primary responsibilities:
1. **Understand natural language queries** about reconciliation requests:
    Matching projects, workers, tasks, and orders from our internal data to external data
2. **Select the right subagents to call to fetch the requested data
3. **Parse and synthesize** the subagent responses into clear, machine-readable answers
4. **Handle multi-step queries** by chaining tools when needed

## Core Capabilities

### Reconciliation

- Use the subagents at your disposal to request information from various parts of the internal database.
- Go from external data with arbitrary format, and find the corresponding data in the system.

### Total cost computation

You may be asked to compute the cost of a worker for a period. This involves complex computation,
so you must use the total_cost tool and not try to compute it by hand. This is critical as we need 100%
accuracy.

### Subagents

You have subagents at your disposal, exposed as tools. Be proactive in your use of them.

If you think you are missing subagents, immediately stop execution and return a help request.

## Query Handling Strategy

### Example 1:
User: Verify that worker A worked 12 days on project B for X € in October 2025
You:
- Call the projects subagent, ask it for worker a's timesheet id for October 2025, and rate for project B
- Call the timesheet subagent, ask it to count the number of days worked on project B for this timesheet id
- Use the total_cost tool to compute total cost for this worker and period
- Present your results

## Important Rules

1. **Tool-First Approach**: ALWAYS use tools to fetch data. NEVER fabricate information.
2. **Error Handling**: If a tool fails, report the error clearly and suggest alternatives.
3. **Data Parsing**: Extract relevant information from JSON responses - focus on 'data', 'attributes', 'relationships'.
4. **Clarity**: Provide structured, easy-to-read responses with bullet points or tables when appropriate.
6. **Chain Tools**: For complex queries, use multiple tools sequentially.

## Response Format

**Success Response:**
- Provide clear, structured answers
- Include relevant IDs and names

**Error Response:**
- State what went wrong
- Explain the error message
- Suggest alternative approaches

You are precise, efficient, and helpful. Execute queries exactly as specified.
Return complex data in a computer-readable format like JSON or XML.
Return simple data with very minimal formating.
Remember your audience is another agent, not a human.
"""


def create_reconciliation_agent(
    model: BaseChatModel | None = None,
) -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
    """Create a standalone reconciliation agent with all fetching-related subagents.

    Args:
        model: LLM model to use. If None, uses default from llm_config.

    Returns:
        Configured LangGraph agent ready to handle reconciliation queries.
    """
    if model is None:
        model = get_llm()

    agent = create_agent(
        model,
        tools=[
            project_agent_tool,
            timesheet_agent_tool,
            resource_agent_tool,
            total_cost,
        ],
        system_prompt=PROJECT_AGENT_PROMPT,
    )

    return agent


@tool(parse_docstring=True)
async def reconciliation_agent_tool(prompt: str):
    """
    ## Core Capabilities

    ### Data Reconciliation
    - Match projects, workers, tasks, and orders from internal data to external data
    - Verify worker time and costs against external records
    - Cross-reference data across project, timesheet, and resource systems

    ### Multi-Source Data Synthesis
    - Query multiple subagents (project, timesheet, resource) to gather complete information
    - Chain tools sequentially to build comprehensive reconciliation reports
    - Handle complex verification scenarios requiring data from multiple systems

    ### Total Cost Computation
    - Compute accurate worker costs for specific periods using the total_cost tool
    - Calculate costs across projects and time periods
    - Ensure 100% accuracy in financial calculations

    ### Subagent Coordination
    - Project agent: Access project details, worker assignments, and delivery rates
    - Timesheet agent: Retrieve daily time entries and work patterns
    - Resource agent: Look up worker information and identifiers

    Args:
        prompt (str): A clear and concise prompt to send to the agent as input.
    """

    async for message in create_reconciliation_agent().astream({"messages": [("user", prompt)]}):
        # # Print the agent's response
        response = message.get("tools", {}) or message.get("model", {})
        for msg in response.get("messages", []):
            format_message(msg, pad_left = 2)
            # if hasattr(msg, "content") and msg.content:
            #     print(f"Agent: {msg.content}")

    return msg.content

    ret = await create_reconciliation_agent().ainvoke({"messages": prompt})

    return ret.get("messages", [""])[-1].content


async def demo_project_agent():
    """Demo function to test the project agent with example queries."""
    print("=== BoondManager Reconciliation Agent Demo ===\n")

    agent = create_reconciliation_agent()

    # Example queries
    queries = [
        "Verify that worker Elodie LEGUAY worked 12 days on project modernisation in September 2025",
        "Did worker Didier Geig work 12 days on project modernisation in september 2025 ?",
        "Was total cost for worker Jon LEVIN on the project where he worked the least 4680 in September 2025 ?",
        "What was the total cost for worker Jon LEVIN on the project where he worked the most in September 2025 ?",
        "Find LEVIN Jon's average daily rate for project Tps partiel",
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
    asyncio.run(demo_project_agent())
