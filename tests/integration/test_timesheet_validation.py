"""Integration tests for timesheet validation workflow.

These tests verify the complete agent orchestration flow:
Main Coordinator → Validation Agent → Validation Tools → BoondManager API

⚠️ IMPORTANT: These are REAL integration tests that:
- Hit the actual BoondManager API (not mocked)
- Require valid credentials in .env
- Use real timesheet data from test environment
- Modify actual timesheet states (unvalidate → validate)
"""

import uuid
from typing import Any, Dict

import pytest
from langchain_core.messages import HumanMessage

from src.agents.main_coordinator import create_main_coordinator
from src.tools.timesheet_tools import get_timesheet_by_id
from src.tools.validation_tool import unvalidate_timesheet, validate_timesheet

# ============================================================================
# Test Configuration
# ============================================================================

# Test data from BoondManager test environment
TEST_TIMESHEET_ID = 5  # Known timesheet in test environment
TEST_VALIDATOR_ID = 2  # Known validator resource ID


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
        print(f"✅ Timesheet {timesheet_id} already in non-validated state: {current_state}")


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


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_validate_timesheet_workflow():
    """Test complete timesheet validation workflow through agent orchestration.

    Flow:
    1. Setup: Unvalidate timesheet to ensure pending state
    2. Execute: Main agent validates timesheet via validation_agent
    3. Verify: Check timesheet is in validated state

    This tests:
    - Agent delegation (Main → Validation Agent)
    - Tool execution (validate_timesheet)
    - API integration (BoondManager validation endpoint)
    - State changes (pending → validated)
    """
    print(f"\n{'=' * 80}")
    print(f"TEST: Validate Timesheet {TEST_TIMESHEET_ID}")
    print(f"{'=' * 80}\n")

    # ========================================================================
    # Phase 1: Setup - Ensure timesheet is in pending state
    # ========================================================================
    print("📋 PHASE 1: Setup - Unvalidate timesheet")
    await ensure_timesheet_pending(TEST_TIMESHEET_ID, TEST_VALIDATOR_ID)

    initial_state = await get_timesheet_state(TEST_TIMESHEET_ID)
    assert initial_state in ["waitingForValidation", "pending"], (
        f"Setup failed: Timesheet {TEST_TIMESHEET_ID} should be in non-validated state, "
        f"but state is '{initial_state}'"
    )
    print(f"✅ Timesheet {TEST_TIMESHEET_ID} confirmed in non-validated state: {initial_state}\n")

    # ========================================================================
    # Phase 2: Execute - Agent validates timesheet
    # ========================================================================
    print("🤖 PHASE 2: Execute - Agent validation workflow")

    # Create agent using shared factory
    main_agent = create_main_coordinator()

    # Create unique thread for this test
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Send validation request
    query = f"Validate timesheet {TEST_TIMESHEET_ID} with validator {TEST_VALIDATOR_ID}"
    print(f"📤 Sending request: {query}")

    result = await main_agent.ainvoke([HumanMessage(content=query)], config)

    # Get final response
    final_message = result["messages"][-1]
    print(f"📬 Agent response: {final_message.content[:200]}...")

    # ========================================================================
    # Phase 3: Verify - Check timesheet state
    # ========================================================================
    print("\n✅ PHASE 3: Verify - Check validation result")

    # Verify timesheet is now validated
    timesheet_data = await assert_timesheet_validated(TEST_TIMESHEET_ID)

    # Extract warnings from the full timesheet response (not validation response)
    # Note: warnings are in the validation API response, not the get timesheet response
    # We'll check the agent response instead
    if "warning" in final_message.content.lower():
        print(f"⚠️  Agent reported validation warnings in response")
    else:
        print("✅ No warnings mentioned in agent response")

    # Verify agent response mentions validation success
    assert (
        "validated" in final_message.content.lower()
        or "success" in final_message.content.lower()
    ), f"Agent response should mention validation success: {final_message.content}"

    print(f"\n{'=' * 80}")
    print("✅ TEST PASSED: Timesheet validation workflow completed successfully")
    print(f"{'=' * 80}\n")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(reason="Requires multiple test timesheets - implement when test data available")
async def test_batch_validation_workflow():
    """Test batch validation of multiple timesheets.

    Flow:
    1. Setup: Unvalidate multiple timesheets
    2. Execute: Agent validates all timesheets in batch
    3. Verify: All timesheets are validated

    This tests:
    - Batch delegation to validation_agent
    - Parallel validation operations
    - Multiple state changes
    """
    # TODO: Implement when multiple test timesheets are available
    # Test data needed: List of timesheet IDs with known validator
    pass


@pytest.mark.asyncio
@pytest.mark.integration
async def test_direct_validation_tool():
    """Test validation tool directly (no agent orchestration).

    This is a simpler test to verify the validation tool and API integration
    work correctly before testing the full agent workflow.
    """
    print(f"\n{'=' * 80}")
    print(f"TEST: Direct Validation Tool - Timesheet {TEST_TIMESHEET_ID}")
    print(f"{'=' * 80}\n")

    # Setup: Ensure non-validated state
    print("📋 Setup: Unvalidate timesheet")
    await ensure_timesheet_pending(TEST_TIMESHEET_ID, TEST_VALIDATOR_ID)

    initial_state = await get_timesheet_state(TEST_TIMESHEET_ID)
    assert initial_state in ["waitingForValidation", "pending"], (
        f"Expected non-validated state, got '{initial_state}'"
    )
    print(f"✅ Timesheet {TEST_TIMESHEET_ID} in non-validated state: {initial_state}\n")

    # Execute: Validate directly with tool
    print("🔧 Execute: Call validate_timesheet tool")
    result = await validate_timesheet.ainvoke(
        {"timesheet_id": TEST_TIMESHEET_ID, "expected_validator_id": TEST_VALIDATOR_ID}
    )

    # Verify: Check response
    assert "data" in result, f"Validation failed: {result}"
    state = result.get("data", {}).get("attributes", {}).get("state", "unknown")
    assert state == "validated", f"Expected validated state, got '{state}'"

    # Verify: Check API state
    final_state = await get_timesheet_state(TEST_TIMESHEET_ID)
    assert final_state == "validated"

    print("✅ Direct validation tool test passed\n")


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s", "-m", "integration"])
