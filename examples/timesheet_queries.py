"""Example queries for the BoondManager timesheet agent.

This file demonstrates how to use the timesheet agent for various use cases.
"""

import asyncio

from src.agents.timesheet_agent import create_timesheet_agent


async def basic_queries():
    """Basic timesheet queries."""
    print("=== Basic Timesheet Queries ===\n")

    agent = create_timesheet_agent()

    queries = [
        # Get all timesheets for a worker
        "Get all timesheets for worker 28",
        # Get detailed daily entries
        "Show me the daily entries for timesheet 5",
        # Get specific information
        "What is the state of timesheet 5?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        async for message in agent.astream({"messages": [("user", query)]}):
            response = message.get("tools", {}) or message.get("model", {})
            for msg in response.get("messages", []):
                if hasattr(msg, "content") and msg.content:
                    print(f"Response: {msg.content}\n")


async def analysis_queries():
    """Analysis-focused timesheet queries."""
    print("\n=== Analysis Queries ===\n")

    agent = create_timesheet_agent()

    queries = [
        # Project breakdown
        "What projects did worker 28 work on in timesheet 5?",
        # Time analysis
        "How many production days vs internal days in timesheet 5?",
        # Date range analysis
        "What dates did worker 28 work in September 2025?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        async for message in agent.astream({"messages": [("user", query)]}):
            response = message.get("tools", {}) or message.get("model", {})
            for msg in response.get("messages", []):
                if hasattr(msg, "content") and msg.content:
                    print(f"Response: {msg.content}\n")


async def combined_queries():
    """Queries that combine multiple tools."""
    print("\n=== Combined Queries ===\n")

    agent = create_timesheet_agent()

    queries = [
        # Worker timesheet summary
        "Give me a summary of all timesheets for worker 28 with their states",
        # Detailed breakdown for a specific period
        "Find the timesheet for worker 28 in September 2025 and show all work days",
        # Validation status check
        "What is the validation status of worker 28's timesheets?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        async for message in agent.astream({"messages": [("user", query)]}):
            response = message.get("tools", {}) or message.get("model", {})
            for msg in response.get("messages", []):
                if hasattr(msg, "content") and msg.content:
                    print(f"Response: {msg.content}\n")


async def main():
    """Run all example queries."""
    await basic_queries()
    await analysis_queries()
    await combined_queries()


if __name__ == "__main__":
    asyncio.run(main())
