"""Standalone resource agent for fetching and parsing BoondManager resource data."""

import asyncio
from typing import Any

from langchain.agents import AgentState, create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph

from src.llm_config import get_llm
from src.tools.resource_tools import (
    get_resource_by_id,
    search_resources,
)

# Agent system prompt
RESOURCE_AGENT_PROMPT = """You are a specialized agent for fetching and parsing resource (worker) data from BoondManager CRM.

Your primary responsibilities:
1. **Understand natural language queries** about workers, consultants, resources, and their information
2. **Select the right tool(s)** to fetch the requested data
3. **Parse and synthesize** the API responses into clear, human-readable answers
4. **Handle multi-step queries** by chaining tools when needed

## Core Capabilities

### Resource Discovery
- Use `search_resources` to find resources by name, keywords, or filters
- Always start with search if you only have a resource name (not ID)
- Search can be used without keywords to list all resources

### Resource Details
- Use `get_resource_by_id` for detailed resource information
- This provides comprehensive profile data including contact info and assignments

## Query Handling Strategy

### Example 1: "Find resource elodie leguay"
1. Call `search_resources(keywords="elodie leguay")`
2. Extract the resource ID from the response
3. Return: "Resource Elodie Leguay has ID: {id}"

### Example 2: "Get details for resource 28"
1. Call `get_resource_by_id(resource_id=28)`
2. Parse the resource profile data
3. Return: "Resource 28: Elodie Leguay (elodie@example.com, Active: true)"

### Example 3: "List all active resources"
1. Call `search_resources()` to get all resources
2. Filter by attributes.isActive = true
3. Return: "Active resources: [names and IDs]"

## Important Rules

1. **Tool-First Approach**: ALWAYS use tools to fetch data. NEVER fabricate information.
2. **Error Handling**: If a tool fails, report the error clearly and suggest alternatives.
3. **Data Parsing**: Extract relevant information from JSON responses - focus on 'data', 'attributes', 'relationships'.
4. **Clarity**: Provide structured, easy-to-read responses with bullet points or tables when appropriate.
5. **Verify IDs**: When given a resource name, use `search_resources` first to get the ID.
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

User: "Find resource elodie"
You:
1. Use `search_resources(keywords="elodie")`
2. Response: "Found resource: Elodie Leguay (ID: 28, Email: elodie@example.com, Active: true)"

User: "Get info on resource 28"
You:
1. Use `get_resource_by_id(resource_id=28)`
2. Response: "Resource 28:
    " Name: Elodie Leguay
    " Email: elodie@example.com
    " Active: true
    " Start Date: 2020-01-15"

You are precise, efficient, and helpful. Execute queries exactly as specified.
Return complex data in a computer-readable format like JSON or XML.
Return simple data with very minimal formatting.
Remember your audience is another agent, not a human.
"""


def create_resource_agent(
    model: BaseChatModel | None = None,
) -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
    """Create a standalone resource agent with all resource-related tools.

    Args:
        model: LLM model to use. If None, uses default from llm_config.

    Returns:
        Configured LangGraph agent ready to handle resource queries.

    Example:
        >>> agent = create_resource_agent()
        >>> async for message in agent.astream({"messages": [
        ...     ("user", "Find resource elodie leguay")
        ... ]}):
        ...     print(message)
    """
    if model is None:
        model = get_llm()

    agent = create_agent(
        model,
        tools=[
            search_resources,
            get_resource_by_id,
        ],
        system_prompt=RESOURCE_AGENT_PROMPT,
    )

    return agent


@tool(parse_docstring=True)
async def resource_agent_tool(prompt: str):
    """
    ## Core Capabilities

    ### Resource Discovery
    - Always start with search if you only have a resource name (not ID)
    - Search can be used to list all resources

    ### Resource Details
    - Get detailed information about specific resources
    - Includes contact info, employment status, and assignments

    Args:
        prompt (str): A clear and concise prompt to send to the agent as input.
"""

    ret = await create_resource_agent().ainvoke({"messages": prompt})

    return ret.get("messages", [""])[-1].content


async def demo_resource_agent():
    """Demo function to test the resource agent with example queries."""
    print("=== BoondManager Resource Agent Demo ===\n")

    agent = create_resource_agent()

    # Example queries
    queries = [
        "Find resource elodie leguay",
        "Get details for resource 28",
        "List all resources",
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
    asyncio.run(demo_resource_agent())
