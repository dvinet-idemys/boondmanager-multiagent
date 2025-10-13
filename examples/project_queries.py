"""Example natural language queries for the project agent.

Run this file to test the project agent with various query patterns.
"""

import asyncio
from pprint import pprint

from src.agents.project_agent import create_project_agent


async def run_query(agent, query: str):
    """Execute a single query and print results."""
    print(f"\n{'='*70}")
    print(f"QUERY: {query}")
    print('='*70)

    try:
        async for message in agent.astream({"messages": [("user", query)]}):
            if "messages" in message:
                for msg in message["messages"]:
                    if hasattr(msg, "content") and msg.content:
                        print(f"\n{msg.content}")
            elif message:
                # Print intermediate steps if needed
                pass
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def main():
    """Run example queries demonstrating project agent capabilities."""

    print("\n" + "🤖 BoondManager Project Agent - Example Queries ".center(70, "="))
    print("\nThis demonstrates various natural language query patterns.\n")

    # Create the agent
    agent = create_project_agent()

    # ========================================================================
    # CATEGORY 1: Simple Project Lookup
    # ========================================================================

    print("\n" + " CATEGORY 1: Simple Project Lookup ".center(70, "-"))

    await run_query(
        agent,
        "Fetch the project id for project alpha"
    )

    await run_query(
        agent,
        "Find project Modernisation"
    )

    await run_query(
        agent,
        "Search for projects with keyword 'production'"
    )

    # ========================================================================
    # CATEGORY 2: Worker/Resource Queries
    # ========================================================================

    print("\n" + " CATEGORY 2: Worker/Resource Queries ".center(70, "-"))

    await run_query(
        agent,
        "Give me names and ids for workers associated with project id 4"
    )

    await run_query(
        agent,
        "Who is working on project alpha?"
    )

    await run_query(
        agent,
        "Get the resource assignments for project 12"
    )

    # ========================================================================
    # CATEGORY 3: Multi-Step Queries
    # ========================================================================

    print("\n" + " CATEGORY 3: Multi-Step Queries ".center(70, "-"))

    await run_query(
        agent,
        "What's the status and workers for project Modernisation?"
    )

    await run_query(
        agent,
        "Find project Alpha and tell me who works on it"
    )

    # ========================================================================
    # CATEGORY 4: Detailed Information
    # ========================================================================

    print("\n" + " CATEGORY 4: Detailed Information ".center(70, "-"))

    await run_query(
        agent,
        "Get all details for project id 4"
    )

    await run_query(
        agent,
        "What are the orders for project 8?"
    )

    await run_query(
        agent,
        "Show me the tasks in project id 15"
    )

    # ========================================================================
    # CATEGORY 5: Filtered Searches
    # ========================================================================

    print("\n" + " CATEGORY 5: Filtered Searches ".center(70, "-"))

    await run_query(
        agent,
        "Find all projects for company id 123"
    )

    await run_query(
        agent,
        "Search for projects created this month"
    )

    # ========================================================================
    # CATEGORY 6: Error Handling
    # ========================================================================

    print("\n" + " CATEGORY 6: Error Handling ".center(70, "-"))

    await run_query(
        agent,
        "Get project with id 999999999"
    )

    await run_query(
        agent,
        "Find project that definitely does not exist xyz123"
    )

    print("\n" + "="*70)
    print("✅ Demo completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
