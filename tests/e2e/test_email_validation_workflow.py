"""End-to-end tests for email-based timesheet validation workflow.

This test suite validates the complete workflow:
1. Parse email with worker timesheet data
2. Query BoondManager for actual timesheet data
3. Compare email data vs BoondManager data
4. When matched: Validate timesheets
5. When mismatched: Report discrepancy (do NOT send email unless explicitly requested)

⚠️ IMPORTANT: These are REAL e2e tests that:
- Use the Main Coordinator agent (full 3-level hierarchy)
- Hit the actual BoondManager API (not mocked)
- Require valid credentials in .env
- Modify actual timesheet states (validate/unvalidate)
"""

import uuid
from typing import Dict, Any

import pytest
from langchain_core.messages import HumanMessage

from src.agents.main_coordinator import create_main_coordinator
from src.tools.timesheet_tools import get_timesheet_by_id
from src.tools.validation_tool import unvalidate_timesheet

# ============================================================================
# Test Configuration
# ============================================================================

# Sample email from client with timesheet data
SAMPLE_EMAIL = """
Hi Dimitri,

Here is the breakdown for the projects at Roche, Veolia and SAUR for September 2025.

- Project

LAST First Name     days worked     total cost

- Modernisation Ligne Production - Multi commande

LEGUAY Elodie       12j             7860
GEIG Didier         22j             14432
"""

# Test data from BoondManager test environment
TEST_VALIDATOR_ID = 2  # Known validator resource ID

# Expected worker data from email
EMAIL_WORKER_DATA = [
    {"name": "LEGUAY Elodie", "days": 12, "cost": 7860},  # This will MATCH
    {"name": "GEIG Didier", "days": 22, "cost": 14432},   # This will be WRONG in query
]


# ============================================================================
# Test Utilities
# ============================================================================


async def get_timesheet_state(timesheet_id: int) -> str:
    """Get current validation state of a timesheet.

    Args:
        timesheet_id: Timesheet ID to check

    Returns:
        State string: "validated", "waitingForValidation", "rejected", or "unknown"
    """
    result = await get_timesheet_by_id.ainvoke({"timesheet_id": timesheet_id})

    if "data" in result and result["data"] is not None:
        return result["data"]["attributes"]["state"]

    return "unknown"


async def ensure_timesheet_pending(timesheet_id: int, validator_id: int) -> None:
    """Ensure timesheet is in waitingForValidation state (unvalidate if needed).

    Args:
        timesheet_id: Timesheet ID to prepare
        validator_id: Validator resource ID for unvalidation
    """
    current_state = await get_timesheet_state(timesheet_id)

    if current_state == "validated":
        print(f"📝 Unvalidating timesheet {timesheet_id} (current state: {current_state})")
        result = await unvalidate_timesheet.ainvoke(
            {"timesheet_id": timesheet_id, "expected_validator_id": validator_id}
        )
        new_state = result.get("data", {}).get("attributes", {}).get("state", "unknown")
        print(f"✅ Timesheet {timesheet_id} unvalidated (new state: {new_state})")
    else:
        print(
            f"✅ Timesheet {timesheet_id} already in non-validated state: {current_state}"
        )


async def assert_timesheet_validated(timesheet_id: int) -> Dict[str, Any]:
    """Assert that timesheet is in validated state.

    Args:
        timesheet_id: Timesheet ID to verify

    Returns:
        Full timesheet data for additional assertions

    Raises:
        AssertionError: If timesheet is not validated
    """
    result = await get_timesheet_by_id.ainvoke({"timesheet_id": timesheet_id})

    assert "data" in result, f"Failed to fetch timesheet {timesheet_id}: {result}"
    assert result["data"] is not None, f"Timesheet {timesheet_id} not found"

    state = result["data"]["attributes"]["state"]
    assert state == "validated", (
        f"Expected timesheet {timesheet_id} to be validated, but state is '{state}'"
    )

    print(f"✅ Verified timesheet {timesheet_id} is validated")
    return result


async def assert_timesheet_not_validated(timesheet_id: int) -> Dict[str, Any]:
    """Assert that timesheet is NOT in validated state.

    Args:
        timesheet_id: Timesheet ID to verify

    Returns:
        Full timesheet data for additional assertions

    Raises:
        AssertionError: If timesheet is validated
    """
    result = await get_timesheet_by_id.ainvoke({"timesheet_id": timesheet_id})

    assert "data" in result, f"Failed to fetch timesheet {timesheet_id}: {result}"
    assert result["data"] is not None, f"Timesheet {timesheet_id} not found"

    state = result["data"]["attributes"]["state"]
    assert state != "validated", (
        f"Expected timesheet {timesheet_id} to NOT be validated, but state is '{state}'"
    )

    print(f"✅ Verified timesheet {timesheet_id} is NOT validated (state: {state})")
    return result


def extract_draft_ids(agent_response: str) -> list:
    """Extract draft IDs from agent response.

    Args:
        agent_response: Final agent response text

    Returns:
        List of draft IDs mentioned
    """
    draft_ids = []
    # Look for draft-YYYYMMDD-HHMMSS pattern
    import re
    draft_pattern = r"draft-\d{8}-\d{6}"
    found_drafts = re.findall(draft_pattern, agent_response)
    draft_ids.extend(found_drafts)
    return draft_ids


# ============================================================================
# E2E Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_validation_workflow_one_match_one_mismatch():
    """Test validation workflow with one matching and one mismatched timesheet.

    Flow:
    1. User provides email with 2 workers: Elodie (12j) and Didier (22j)
    2. Query results show: Elodie (12j) MATCHES, Didier (15j) MISMATCHES
    3. Agent validates ONLY Elodie's timesheet (the matching one)
    4. Agent reports discrepancy for Didier but does NOT send email (not requested)
    5. Verify: Elodie's timesheet is validated
    6. Verify: Didier's timesheet is NOT validated
    7. Verify: No emails were drafted or sent

    This tests:
    - Selective validation based on data matching
    - Agent respects "do not send email" implicit instruction
    - Correct timesheet state changes
    - Discrepancy reporting without email workflow
    """
    print(f"\n{'=' * 80}")
    print("TEST: Email Validation Workflow - One Match, One Mismatch")
    print(f"{'=' * 80}\n")

    # ========================================================================
    # Phase 1: Setup - Get test timesheet IDs and ensure pending state
    # ========================================================================
    print("🤖 PHASE 1: Setup - Identify and prepare test timesheets\n")

    # Create main agent to query for timesheet IDs
    main_agent = create_main_coordinator(policy_tools=[])
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Query for Elodie's timesheet ID
    elodie_query = "Get the timesheet ID for LEGUAY Elodie for September 2025"
    print(f"📤 Querying: {elodie_query}")
    result = await main_agent.ainvoke([HumanMessage(content=elodie_query)], config)
    elodie_response = result["messages"][-1].content
    print(f"📬 Response: {elodie_response[:200]}...\n")

    # Extract timesheet ID from response (look for number patterns)
    import re
    elodie_id_matches = re.findall(r'\btimesheet[_\s]+(?:id[:\s]+)?(\d+)\b', elodie_response.lower())
    if not elodie_id_matches:
        # Try other patterns
        elodie_id_matches = re.findall(r'\bid[:\s]+(\d+)\b', elodie_response.lower())

    assert elodie_id_matches, f"Could not find Elodie's timesheet ID in response: {elodie_response}"
    elodie_timesheet_id = int(elodie_id_matches[0])
    print(f"✅ Found Elodie's timesheet ID: {elodie_timesheet_id}\n")

    # Query for Didier's timesheet ID
    didier_query = "Get the timesheet ID for GEIG Didier for September 2025"
    print(f"📤 Querying: {didier_query}")
    result = await main_agent.ainvoke([HumanMessage(content=didier_query)], config)
    didier_response = result["messages"][-1].content
    print(f"📬 Response: {didier_response[:200]}...\n")

    # Extract timesheet ID from response
    didier_id_matches = re.findall(r'\btimesheet[_\s]+(?:id[:\s]+)?(\d+)\b', didier_response.lower())
    if not didier_id_matches:
        didier_id_matches = re.findall(r'\bid[:\s]+(\d+)\b', didier_response.lower())

    assert didier_id_matches, f"Could not find Didier's timesheet ID in response: {didier_response}"
    didier_timesheet_id = int(didier_id_matches[0])
    print(f"✅ Found Didier's timesheet ID: {didier_timesheet_id}\n")

    # Ensure both timesheets are in pending state
    print("📋 Ensuring both timesheets are in pending state...")
    await ensure_timesheet_pending(elodie_timesheet_id, TEST_VALIDATOR_ID)
    await ensure_timesheet_pending(didier_timesheet_id, TEST_VALIDATOR_ID)

    elodie_initial_state = await get_timesheet_state(elodie_timesheet_id)
    didier_initial_state = await get_timesheet_state(didier_timesheet_id)

    print(f"✅ Elodie's timesheet {elodie_timesheet_id} state: {elodie_initial_state}")
    print(f"✅ Didier's timesheet {didier_timesheet_id} state: {didier_initial_state}\n")

    # ========================================================================
    # Phase 2: Execute - Agent validates matching timesheet only
    # ========================================================================
    print("📧 PHASE 2: Execute - Agent validation with one match, one mismatch\n")

    # Create new thread for validation workflow
    validation_thread_id = str(uuid.uuid4())
    validation_config = {"configurable": {"thread_id": validation_thread_id}}

    # Query with one matching (Elodie 12j) and one wrong (Didier 15j vs email 22j)
    query = f"""
Validate timesheets when days worked and totals match.
Do NOT send emails - just report discrepancies.

Query results:
LEGUAY Elodie       12j             7860
GEIG Didier         15j             9840

Original Email:
{SAMPLE_EMAIL}
"""

    print(f"📤 Sending validation request:\n{query}\n")
    result = await main_agent.ainvoke([HumanMessage(content=query)], validation_config)

    # Get final response
    final_message = result["messages"][-1]
    print(f"📬 Agent response:\n{final_message.content}\n")

    # ========================================================================
    # Phase 3: Verify - Check validation results
    # ========================================================================
    print("✅ PHASE 3: Verify - Check selective validation\n")

    response_text = final_message.content.lower()

    # 1. Agent should recognize Elodie's data matches
    assert (
        "leguay" in response_text or "elodie" in response_text
    ), f"Agent should mention Elodie: {final_message.content}"

    # 2. Agent should recognize Didier's data mismatch
    assert (
        ("geig" in response_text or "didier" in response_text)
        and ("mismatch" in response_text or "discrepancy" in response_text or "difference" in response_text or "15" in response_text or "22" in response_text)
    ), f"Agent should mention Didier's mismatch: {final_message.content}"

    # 3. No emails should be drafted (not requested)
    draft_ids = extract_draft_ids(final_message.content)
    assert len(draft_ids) == 0, f"Agent should NOT draft emails (not requested): {final_message.content}"

    # 4. Verify Elodie's timesheet is validated
    print(f"\n🔍 Checking Elodie's timesheet {elodie_timesheet_id} state...")
    await assert_timesheet_validated(elodie_timesheet_id)

    # 5. Verify Didier's timesheet is NOT validated
    print(f"🔍 Checking Didier's timesheet {didier_timesheet_id} state...")
    await assert_timesheet_not_validated(didier_timesheet_id)

    # 6. Agent should mention validation success for matching
    assert (
        "validated" in response_text or "approved" in response_text
    ), f"Agent should mention validation: {final_message.content}"

    print(f"\n{'=' * 80}")
    print("✅ TEST PASSED: Selective validation - matched timesheet validated, mismatched not")
    print(f"   - Elodie (MATCH): Validated ✅")
    print(f"   - Didier (MISMATCH): NOT validated ❌")
    print(f"   - Emails drafted: {len(draft_ids)} (expected: 0)")
    print(f"{'=' * 80}\n")


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    # Run e2e tests with verbose output
    pytest.main([__file__, "-v", "-s", "-m", "e2e"])
