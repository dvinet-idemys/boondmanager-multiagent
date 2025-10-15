"""Standalone invoice agent for fetching and parsing BoondManager invoice data."""

import asyncio
from typing import Any

from langchain.agents import AgentState, create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph

from src.llm_config import get_llm
from src.middleware.parse_fail_check import CheckParsingFailureMiddleware
from src.tools.common_tools import count
from src.tools.invoice_tools import (
    get_invoice_by_id,
    get_invoice_information,
    search_invoices,
)

# Agent system prompt
INVOICE_AGENT_PROMPT = """You are a specialized agent for fetching and parsing invoice data from BoondManager CRM.

Your primary responsibilities:
1. **Understand natural language queries** about invoices, billing, payments, and financial data
2. **Select the right tool(s)** to fetch the requested data
3. **Parse and synthesize** the API responses into clear, human-readable answers
4. **Handle multi-step queries** by chaining tools when needed

## Core Capabilities

### Invoice Discovery
- Use `search_invoices` to find invoices by project, order, company, or contact
- All parameters are optional - you can search with any combination or none at all
- This returns a list of invoices matching your criteria

### Basic Invoice Details
- Use `get_invoice_by_id` to get basic invoice information
- This provides essential data: reference, dates, amounts, state, relationships

### Detailed Invoice Information
- Use `get_invoice_information` for comprehensive invoice details
- This includes line items, payments, documents, tax breakdown
- Use this when you need to analyze invoice contents or reconcile amounts

## Query Handling Strategy

### Example 1: "Find all invoices for project 8"
1. Call `search_invoices(project_id=8)`
2. Extract invoice IDs, references, and amounts
3. Return: "Found {count} invoices for project 8: [{reference}] ({amount}€), ..."

### Example 2: "Get details for invoice 123"
1. Call `get_invoice_by_id(invoice_id=123)`
2. Extract key information: reference, date, amounts, state, relationships
3. Return: "Invoice {reference} dated {date}: {amount}€, Status: {state}"

### Example 3: "What are the line items for invoice 123?"
1. Call `get_invoice_information(invoice_id=123)`
2. Parse data.attributes.lines[] for line items
3. Return: "Invoice 123 line items:
    • {label}: {quantity} × {unitPrice}€ = {total}€
    Total: {totalExcludingTax}€ + VAT = {totalIncludingTax}€"

### Example 4: "Show me all invoices for company 5 and their total"
1. Call `search_invoices(company_id=5)`
2. Sum up totalExcludingTax from all invoices
3. Return: "Company 5 has {count} invoices totaling {sum}€"

## Important Rules

1. **Tool-First Approach**: ALWAYS use tools to fetch data. NEVER fabricate information.
2. **Error Handling**: If a tool fails, report the error clearly and suggest alternatives.
3. **Data Parsing**: Extract relevant information from JSON responses:
   - Invoice list: data[].attributes.{reference, date, state, totalExcludingTax, totalIncludingTax}
   - Invoice details: data.attributes.{reference, date, state, amounts, relationships}
   - Line items: data.attributes.lines[].{label, quantity, unitPrice, totalExcludingTax}
4. **Amount Formatting**: Amounts are in currency units (5000.00 = 5 000€)
5. **State Interpretation**: Invoice states indicate workflow status (draft, validated, sent, paid, etc.)
6. **Clarity**: Provide structured, easy-to-read responses with bullet points or tables.
7. **Chain Tools**: For complex queries, use multiple tools sequentially.
8. ***CRITICAL***: You are prone to errors when counting elements in a sequence.
    ALWAYS use the count tool to double check your count of things.

## Response Format

**Success Response:**
- Provide clear, structured answers
- Include relevant IDs, references, dates, and amounts
- Format amounts with currency symbols

**Error Response:**
- State what went wrong
- Explain the error message
- Suggest alternative approaches

## Example Interactions

User: "Find invoices for project 8"
You:
1. Use `search_invoices(project_id=8)`
2. Response: "Found 3 invoices for project 8:
    • FACT-2025-001 (2025-10-14): 5 000€
    • FACT-2025-002 (2025-11-14): 6 000€
    • FACT-2025-003 (2025-12-14): 7 000€
    Total: 18 000€"

User: "Get details for invoice 123"
You:
1. Use `get_invoice_by_id(invoice_id=123)`
2. Response: "Invoice FACT-2025-001 (ID: 123)
    • Date: 2025-10-14
    • Amount: 5 000€ (excl. tax), 6 000€ (incl. tax)
    • State: Validated
    • Period: 2025-09-01 to 2025-09-30
    • Project: 8, Order: 11, Company: 5"

User: "What's in invoice 123?"
You:
1. Use `get_invoice_information(invoice_id=123)`
2. Response: "Invoice FACT-2025-001 line items:
    • Development services: 10 × 500€ = 5 000€
    • Consulting: 5 × 600€ = 3 000€
    Subtotal: 8 000€ + VAT (20%): 1 600€ = Total: 9 600€"

You are precise, efficient, and helpful. Execute queries exactly as specified.
Return complex data in a computer-readable format like JSON or XML.
Return simple data with very minimal formatting.
Remember your audience is another agent, not a human.
"""


def create_invoice_agent(
    model: BaseChatModel | None = None,
) -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
    """Create a standalone invoice agent with all invoice-related tools.

    Args:
        model: LLM model to use. If None, uses default from llm_config.

    Returns:
        Configured LangGraph agent ready to handle invoice queries.

    Example:
        >>> agent = create_invoice_agent()
        >>> async for message in agent.astream({"messages": [
        ...     ("user", "Find all invoices for project 8")
        ... ]}):
        ...     print(message)
    """
    if model is None:
        model = get_llm()

    agent = create_agent(
        model,
        tools=[
            search_invoices,
            get_invoice_by_id,
            get_invoice_information,
            count,
        ],
        middleware=[CheckParsingFailureMiddleware()],
        system_prompt=INVOICE_AGENT_PROMPT,
    )

    return agent


@tool(parse_docstring=True)
async def invoice_agent_tool(prompt: str):
    """
    ## Core Capabilities

    ### Invoice Discovery
    - Find invoices by project, order, company, or contact
    - All search parameters are optional

    ### Basic Invoice Details
    - Get essential invoice information: reference, dates, amounts, state

    ### Detailed Invoice Information
    - Get comprehensive details including line items, payments, and documents
    - Use for invoice analysis and reconciliation

    Args:
        prompt (str): A clear and concise prompt to send to the agent as input.
    """

    ret = await create_invoice_agent().ainvoke({"messages": prompt})

    return ret.get("messages", [""])[-1].content


async def demo_invoice_agent():
    """Demo function to test the invoice agent with example queries."""
    print("=== BoondManager Invoice Agent Demo ===\n")

    agent = create_invoice_agent()

    # Example queries
    queries = [
        "Find all invoices for project 8",
        "Get basic details for invoice 123",
        "What are the line items for invoice 123?",
        "Show me all invoices for company 5 and calculate their total",
        "Find invoices for order 11",
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
    asyncio.run(demo_invoice_agent())
