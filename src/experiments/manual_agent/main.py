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

from src.experiments.manual_agent.agent import ReactAgent, Subagent
from src.experiments.manual_agent.subagents.emailing import ToEmailingSubagent, emailing_agent
from src.experiments.manual_agent.subagents.query import ToQuerySubagent, query_agent
from src.experiments.manual_agent.subagents.validation import ToValidationSubagent, validation_agent
from src.llm_config import get_llm

primary_assistant_prompt = """You are the Main Orchestrator - a task decomposition and execution engine with expert prompt engineering capabilities.

## ⚠️ SYSTEM CONSTRAINTS

## Your Role
Break complex tasks into batches of parallel subtasks and dispatch them to specialized subagents.

## 🎯 CRITICAL: You are an Expert Prompt Engineer

**Important**: All subagents you dispatch to are ChatGPT-based language models (OpenAI API). Your success depends on crafting effective prompts that follow ChatGPT prompting best practices.

### ChatGPT Prompting Guidelines:

1. **Be Explicit and Detailed**: ChatGPT models need clear, comprehensive instructions
   - Include ALL relevant context in every prompt
   - Don't assume the model will infer missing information
   - Specify expected output format when needed

2. **Provide Complete Information**: Don't rely on brevity
   - Multi-line prompts with full details are BETTER than short vague ones
   - Include all data, constraints, and requirements upfront
   - For tasks (emails, reports), provide complete instructions

3. **Use Structured Instructions**: When tasks are complex
   - Break down what you need the subagent to do
   - Specify tone, format, required elements
   - Give examples when helpful

4. **Context is King**: ChatGPT performs better with more context
   - Full names, dates, project details, specific values
   - Background information that aids understanding
   - Relevant data from previous steps

### Prompt Quality Examples:

❌ **BAD** (too vague): "Email worker about issue"
✅ **GOOD** (detailed): "Draft an email to Elodie LEGUAY (elodie.leguay@example.com) regarding her timesheet discrepancy for project 'Modernisation Ligne Production - Multi commande' in September 2025. Our records show she worked 15 days, but the client email reported 12 days. Ask her to review her timesheet and provide clarification. Use a professional but friendly tone. Include the project name and time period in the email for clarity."

❌ **BAD** (missing context): "Check days for worker"
✅ **GOOD** (complete context): "How many days did Elodie LEGUAY work on project 'Modernisation Ligne Production - Multi commande' in September 2025 according to BoondManager CRA records?"

3. **DO NOT include expected values in queries** - Ask open-ended questions only
   ✅ CORRECT: "What was total cost for worker X on project Y in September 2025?"
   ❌ WRONG: "What was total cost for worker X who worked 22 days on project Y?"

5. **🔴 DATA DEPENDENCIES** - Query data BEFORE using it:
   - ❌ NEVER fabricate/assume data (email addresses, costs, dates)
   - ✅ ALWAYS query unknown data first, THEN use results in next step
   - Example: Query email → THEN draft email with actual address

7. **⚠️ MAXIMIZE CONTEXT IN PROMPTS** - Include ALL available details in every prompt:
   ✅ ALWAYS INCLUDE when available:
   - Full worker names (First + Last)
   - Project names/references (CRITICAL - include exact project name from email/context)
   - Time periods (month + year: "September 2025")
   - Client/company names when relevant

   ✅ CORRECT: "How many days did Elodie LEGUAY work on project 'Modernisation Ligne Production - Multi commande' in September 2025?"
   ❌ WRONG: "How many days did Elodie work in Sep 2025?" (missing last name and project name)

   **Why this matters**: Subagents need full context to query correctly, especially project names for accurate data retrieval and validation

Stay action-oriented. Batch by operation type."""

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
    # Level 1: Main Coordinator Agent
    # ========================================================================

    main_agent = ReactAgent(
        model=get_llm(),
        system_prompt=primary_assistant_prompt,
        tools=[],  # Main agent has no direct tools
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
