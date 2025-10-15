"""Standalone project agent for fetching and parsing BoondManager project data."""

import asyncio
from typing import Any

from langchain.agents import AgentState, create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph

from src.llm_config import get_llm
from src.middleware.parse_fail_check import CheckParsingFailureMiddleware
from src.tools.project_tools import (
    get_project_by_id,
    get_project_deliveries,
    get_project_orders,
    get_project_productivity,
    search_projects,
)

# Agent system prompt
PROJECT_AGENT_PROMPT = """You are a specialized agent for fetching and parsing project data from BoondManager CRM.

Your primary responsibilities:
1. **Understand natural language queries** about projects, workers, tasks, and orders
2. **Select the right tool(s)** to fetch the requested data
3. **Parse and synthesize** the API responses into clear, human-readable answers
4. **Handle multi-step queries** by chaining tools when needed

## Core Capabilities

### Project Discovery
- Use `search_projects` to find projects by name, keywords, or filters
- Always start with search if you only have a project name (not ID)

### Project Details
- Use `get_project_by_id` for project information

### Resource & Worker Information
- Use `get_project_productivity` to find workers/consultants on a project
- This tool reveals worker names, IDs, and timesheet associations

### Orders
- Use `get_project_orders` for billing and order information

### Deliveries
- Use `get_project_deliveries` to get the average daily price excluding tax
of workers associated with the project
- Deliveries are units of work done by workers on projects.

## Query Handling Strategy

### Example 1: "Fetch the project id for project alpha"
1. Call `search_projects(keywords="alpha")`
2. Extract the project ID from the response
3. Return: "Project Alpha has ID: {id}"

### Example 2: "Give me names and ids for workers associated with project id 4"
1. Call `get_project_productivity(project_id=4)`
2. Parse the productivity data for resource information
3. Return: "Workers on project 4: [name] (ID: [id]), [name] (ID: [id])"

### Example 3: "What's the status and workers for project Modernisation?"
1. Call `search_projects(keywords="Modernisation")` -> extract project_id
2. Call `get_project_by_id(project_id=...)` -> get status
3. Call `get_project_productivity(project_id=...)` -> get workers
4. Synthesize: "Project Modernisation (ID: X) is [status]. Workers: [names]"

## Important Rules

1. **Tool-First Approach**: ALWAYS use tools to fetch data. NEVER fabricate information.
2. **Error Handling**: If a tool fails, report the error clearly and suggest alternatives.
3. **Data Parsing**: Extract relevant information from JSON responses - focus on 'data', 'attributes', 'relationships'.
4. **Clarity**: Provide structured, easy-to-read responses with bullet points or tables when appropriate.
5. **Verify IDs**: When given a project name, use `search_projects` first to get the ID.
6. **Chain Tools**: For complex queries, use multiple tools sequentially.

## Response Format

**Success Response:**
- Provide clear, structured answers
- Include relevant IDs and names

**Error Response:**
- State what went wrong
- Explain the error message
- Suggest alternative approaches

## Example Interactions

User: "Find project Alpha"
You:
1. Use `search_projects(keywords="alpha")`
2. Response: "Found project: Alpha (ID: 12345, State: Active)"

User: "Who works on project 4?"
You:
1. Use `get_project_productivity(project_id=4)`
2. Response: "Workers on project 4:
    • First Name LAST NAME (ID: <id>)

You are precise, efficient, and helpful. Execute queries exactly as specified.
Return complex data in a computer-readable format like JSON or XML.
Return simple data with very minimal formating.
Remember your audience is another agent, not a human.
"""


def create_project_agent(
    model: BaseChatModel | None = None,
) -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
    """Create a standalone project agent with all project-related tools.

    Args:
        model: LLM model to use. If None, uses default from llm_config.

    Returns:
        Configured LangGraph agent ready to handle project queries.

    Example:
        >>> agent = create_project_agent()
        >>> async for message in agent.astream({"messages": [
        ...     ("user", "Fetch the project id for project alpha")
        ... ]}):
        ...     print(message)
    """
    if model is None:
        model = get_llm()

    agent = create_agent(
        model,
        tools=[
            search_projects,
            get_project_by_id,
            get_project_productivity,
            get_project_orders,
            get_project_deliveries
        ],
        middleware=[CheckParsingFailureMiddleware()],
        system_prompt=PROJECT_AGENT_PROMPT,
    )

    return agent

@tool(parse_docstring=True)
async def project_agent_tool(prompt: str):
    """
    ## Core Capabilities

    ### Project Discovery
    - Always start with search if you only have a project name (not ID)

    ### Project Details

    ### Resource & Worker Information
    - This tool reveals worker names, IDs, and timesheet associations

    ### Orders
    - For billing and order information

    ### Deliveries
    - Deliveries are units of work done by workers on projects.
    - Get the average daily price excluding tax of workers associated with the project

    Args:
        prompt (str): A clear and concise prompt to send to the agent as input.
    """

    ret = await create_project_agent().ainvoke({"messages": prompt})

    return ret.get("messages", [""])[-1].content



async def demo_project_agent():
    """Demo function to test the project agent with example queries."""
    print("=== BoondManager Project Agent Demo ===\n")

    agent = create_project_agent()

    # Example queries
    queries = [
        # "Fetch the project id for project modernisation",
        # "give me a json list of project names and their id",
        # "Give me names and ids for workers associated with project id 8",
        # "What projects are associated with company Roche ?",
        # "give me all the information you have on projects for Veolia"
        # "give me all client names and their projects"
        "find projects where elodie leguay is working.  what is her daily rate without tax. explain your reasoning"
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
    asyncio.run(demo_project_agent())
