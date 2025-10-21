"""
Main entry point for the React Agent with nested subagent delegation.

This demonstrates a 3-level hierarchy:
- Level 1: Main coordinator (delegates to weather/calculator)
- Level 2: Calculator coordinator (delegates to addition/multiplication)
- Level 3: Leaf specialists (execute actual tools)
"""

import asyncio
import uuid

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.agents.agent import ReactAgent, Subagent
from src.agents.subagents.emailing import ToEmailingSubagent, emailing_agent
from src.agents.subagents.query import ToQuerySubagent, query_agent
from src.agents.subagents.validation import ToValidationSubagent, validation_agent
from src.indexing.index_policies import index_policies
from src.llm_config import get_llm
from src.tools.policy_rag_tool import (
    create_policy_listing_tool,
    create_policy_retrieval_tool,
)

# TODO: implement summarization
# TODO: move majority of policy guidance to policy tools
primary_assistant_prompt = """You are the Main Orchestrator - a task decomposition and delegation specialist.

## Your Role
Break complex tasks into batches of parallel subtasks and dispatch them to specialized subagents.

## 📚 CRITICAL: Use Policy Guidance
You have access to comprehensive organizational policies through the `retrieve_policy` tool.

**🔴 MANDATORY: Consult policies BEFORE starting any workflow**

Use policy retrieval for:
- Workflow procedures (timesheet validation, discrepancy handling)
- Delegation best practices (how to craft effective prompts)
- Error handling protocols
- Standard processes and templates

**How to use**:
```
retrieve_policy("How should I handle timesheet validation discrepancies?")
retrieve_policy("Best practices for delegating to query agent")
retrieve_policy("Prompt engineering guidelines for ChatGPT subagents")
```

**Tip**: Run `list_policy_categories()` to see all available guidance.

## Core Principles (Details in Policies)

1. **Explicit Context**: Subagents are ChatGPT models - provide COMPLETE information
   - Full names (First + Last)
   - Exact project names
   - Specific time periods (month + year)
   - All relevant data

2. **Data Dependencies**: NEVER assume data - query first, use second
   - Query email address → THEN draft email
   - Query cost → THEN compare

3. **Batch Similar Tasks**: Use batch delegation for 3+ similar operations

**When uncertain about HOW to delegate → retrieve_policy("prompt engineering guidelines")**

Stay action-oriented. Consult policies proactively."""

EMAIL = """
Hi Dimitri,

Here is the breakdown for the projects at Roche, Veolia and SAUR for September 2025.

- Project

LAST First Name     days worked     total cost

- Modernisation Ligne Production - Multi commande

LEGUAY Elodie       12j             7860
GEIG Didier         22j             14432
"""


async def main():
    """Example usage of the React agent with nested subagent delegation."""

    # ========================================================================
    # Initialize Policy RAG System
    # ========================================================================
    print("📚 Initializing Policy RAG System...")
    try:
        policy_vectorstore = index_policies()
        retrieve_policy = create_policy_retrieval_tool(policy_vectorstore)
        list_policies = create_policy_listing_tool(policy_vectorstore)
        policy_tools = [retrieve_policy, list_policies]
        print("✅ Policy RAG tools ready\n")
    except Exception as e:
        print(f"⚠️  Policy RAG initialization failed: {e}")
        print("⚠️  Continuing without policy tools...\n")
        policy_tools = []

    # ========================================================================
    # Level 1: Main Coordinator Agent
    # ========================================================================

    main_agent = ReactAgent(
        model=get_llm(),
        system_prompt=primary_assistant_prompt,
        tools=policy_tools,  # Policy RAG tools available to orchestrator
        subagents=[
            Subagent(
                name="query",
                agent=query_agent,
                delegation_tool=ToQuerySubagent,
            ),
            Subagent(
                name="validation",
                agent=validation_agent,
                delegation_tool=ToValidationSubagent,
            ),
            Subagent(
                name="emailing",
                agent=emailing_agent,
                delegation_tool=ToEmailingSubagent,
            ),
        ],
        name="Main Coordinator",
    )

    # ========================================================================
    # Example Queries
    # ========================================================================

    queries = [
        # f"""
        # Verify days worked and totals for each worker in this email.
        # {EMAIL}
        # """,
        # f"""
        # Validate timesheets when days worked and totals match.
        # Query results:
        # LEGUAY Elodie       12j             7860
        # GEIG Didier         22j             14432
        # Original Email:
        # {EMAIL}
        # """,
        f"""
        Validate timesheets when days worked and totals match.
        Send an email to the worker when they don't.
        Then instruct the emailing agent to wait for a response.
        Query results:
        LEGUAY Elodie       15j             9300
        Original Email:
        {EMAIL}
        """,
    ]
    # GEIG Didier         22j             14432

    for query in queries:
        print(f"\n{'=' * 60}")
        print(f"Query: {query}")
        print("=" * 60)

        thread_id = str(uuid.uuid4())
        config = {
            "configurable": {
                # Checkpoints are accessed by thread_id
                "thread_id": thread_id,
            }
        }

        result = await main_agent.ainvoke([HumanMessage(content=query)], config)

        while (interrupt := result.get("__interrupt__")) is not None:
            print(interrupt)
            resume = input("your response here: ")
            result = await main_agent.ainvoke(Command(resume=resume), config=config)

        # Print final response
        final_message = result["messages"][-1]
        print(f"\nFinal Answer: {final_message.content}")


if __name__ == "__main__":
    asyncio.run(main())
