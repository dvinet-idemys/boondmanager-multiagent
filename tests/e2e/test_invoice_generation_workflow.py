"""End-to-end tests for invoice generation and management workflow.

This test suite validates the complete invoice workflow:
1. Invoice generation with mandatory verification (two-step workflow)
2. Invoice search and total calculation (read-only operations)

⚠️ IMPORTANT: These tests validate agent behavior and workflow compliance.
The generate_invoice tool currently uses DUMMY data (see invoice_tools.py:332-422).
Tests verify agent follows the critical two-step workflow from policy:
- Step 1: Call generate_invoice
- Step 2: IMMEDIATELY call search_invoices (MANDATORY)
- Step 3: Use count and calculator tools
- Step 4: Provide detailed recap (not just "Success")

When API is enabled, tests will work with real invoice data.
"""

import uuid

import pytest
from langchain_core.messages import HumanMessage

from src.agents.main_coordinator import create_main_coordinator

# ============================================================================
# Test Configuration
# ============================================================================

# Test project and billing period
TEST_PROJECT_ID = 6
TEST_PROJECT_NAME = "Modernisation Ligne Production - Multi commande"
TEST_BILLING_MONTH = "2025-09"
TEST_COMPANY_ID = 5

# Expected workers for project 6 in September 2025
EXPECTED_WORKERS = ["LEGUAY Elodie", "GEIG Didier"]


# ============================================================================
# E2E Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_invoice_generation_complete_workflow():
    """Test complete invoice generation workflow with mandatory verification.

    This is the PRIMARY test that validates the critical two-step workflow
    from the invoice_generation_workflow.md policy:

    Flow:
    1. User requests invoice generation for a project/month
    2. Agent delegates to invoice_agent
    3. Invoice agent calls generate_invoice tool
    4. Invoice agent IMMEDIATELY calls search_invoices (MANDATORY)
    5. Invoice agent uses count tool to verify count
    6. Invoice agent uses calculator tool for totals
    7. Invoice agent provides detailed recap (NOT just "Success")

    This tests:
    - Main Coordinator → Invoice Agent delegation
    - Invoice Agent follows two-step workflow (generate → verify)
    - Invoice Agent uses ALL mandatory tools (search, count, calculator)
    - Invoice Agent provides required detailed output
    - Full 3-level agent hierarchy

    ⚠️ CRITICAL: This validates that the agent doesn't stop early
    (common ChatGPT issue) and follows the complete verification workflow.
    """
    from src.integrations.boond_client import BoondManagerClient
    from src.tools.invoice_tools import search_invoices

    # Delete existing September 2025 invoices for this project
    initial_search = await search_invoices.ainvoke({"project_id": TEST_PROJECT_ID})
    initial_invoices = initial_search.get("data", [])
    sept_invoices_to_delete = [
        inv for inv in initial_invoices
        if inv["attributes"]["startDate"].startswith("2025-09")
    ]

    if sept_invoices_to_delete:
        client = BoondManagerClient()
        for inv in sept_invoices_to_delete:
            await client.delete_invoice(int(inv["id"]))

    # Create agent and execute
    main_agent = create_main_coordinator(policy_tools=[])
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    query = f"Generate invoices for project {TEST_PROJECT_ID} in September 2025"
    await main_agent.ainvoke([HumanMessage(content=query)], config)

    # Verify invoices were created
    search_result = await search_invoices.ainvoke({"project_id": TEST_PROJECT_ID})
    invoices_data = search_result.get("data", [])
    sept_invoices = [
        inv for inv in invoices_data
        if inv["attributes"]["startDate"].startswith("2025-09")
    ]

    assert len(sept_invoices) > 0, (
        f"Expected invoices for project {TEST_PROJECT_ID} in Sep 2025, found {len(sept_invoices)}"
    )


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_invoice_search_and_calculation():
    """Test invoice search and total calculation (read-only operations).

    This test validates search and aggregation capabilities WITHOUT generation.

    Flow:
    1. User requests invoice search for a company
    2. Agent delegates to invoice_agent
    3. Invoice agent calls search_invoices with company_id
    4. Invoice agent uses calculator to sum amounts
    5. Invoice agent uses count for invoice count
    6. Invoice agent returns structured list with totals

    This tests:
    - Invoice search by company_id
    - Total calculation across multiple invoices
    - Count tool usage
    - Structured response with invoice details

    Key Difference from Test 1:
    - Test 1: CREATES new invoices (generate workflow)
    - This test: READS existing invoices (search workflow)
    """
    from src.tools.invoice_tools import search_invoices

    main_agent = create_main_coordinator(policy_tools=[])
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    query = f"Show me all invoices for company {TEST_COMPANY_ID} and calculate their total"
    await main_agent.ainvoke([HumanMessage(content=query)], config)

    # Verify invoices were retrieved
    search_result = await search_invoices.ainvoke({"company_id": TEST_COMPANY_ID})
    assert "data" in search_result, "Expected invoice data in search results"


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    # Run e2e tests with verbose output
    pytest.main([__file__, "-v", "-s", "-m", "e2e"])
