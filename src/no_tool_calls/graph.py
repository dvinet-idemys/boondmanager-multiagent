import asyncio
import uuid

from langgraph.types import Command

from src.llm_config import get_llm
from src.no_tool_calls.assistant import AssistantWithSubagents
from src.no_tool_calls.subagents.query import query_subagent

primary_assistant_prompt = """
You are a helpful HR assistant for our small company.
Your primary role is to search within our HR database to answer customer queries.
If a user requests information, or to do an action,
delegate the task to the appropriate specialized assistant by invoking the corresponding tool. You are not able to make these types of changes yourself.
Only the specialized assistants are given permission to do this for the user.
The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls.
Provide detailed information to the customer, and always double-check the database before concluding that information is unavailable.
When delegating, be persistent. Expand your query bounds if the first query returns no results.
If a search comes up empty, expand your search before giving up.
"""

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


async def main() -> int:
    # Example queries
    queries = [
        f"""
        Verify days worked and totals for each worker in this email.
        {EMAIL}
        """,
        # f"""
        # Validate timesheets when days worked and totals match.
        # Query results:
        # LEGUAY Elodie       12j             7860
        # GEIG Didier         22j             14432
        # Original Email:
        # {EMAIL}
        # """,
        # f"""
        # Validate timesheets when days worked and totals match.
        # Query results:
        # LEGUAY Elodie       15j             7860
        # GEIG Didier         22j             14432
        # Original Email:
        # {EMAIL}
        # """,
        # f"""
        # Generate invoices for projects in this email. Check that each worker's timesheet
        # were validated. Only generate invoices for projects where all timesheets were
        # validated.
        # Original Email:
        # {EMAIL}
        # """,
    ]

    for query in queries:
        print("==========" + query + "==========")
        thread_id = str(uuid.uuid4())

        config = {
            "configurable": {
                # Checkpoints are accessed by thread_id
                "thread_id": thread_id,
            }
        }

        graph = AssistantWithSubagents(
            get_llm(), primary_assistant_prompt, [], [query_subagent]
        ).runnable
        # print(graph.get_graph(xray=True).draw_mermaid())

        ret = await graph.ainvoke(
            {
                "messages": [query],
            },
            config=config,
        )

        int_res = (i for i in range(100))

        # print(ret)
        while (interrupt := ret.get("__interrupt__")) is not None:
            print(interrupt)
            ret = await graph.ainvoke(Command(resume=next(int_res)), config=config)

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
