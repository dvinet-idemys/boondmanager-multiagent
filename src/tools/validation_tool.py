"""Timesheet validation tools for LangChain agents to interact with BoondManager API.

This module provides tools for validating timesheets and managing approval workflows.
"""

import logging
from typing import Any, Dict

from httpx import HTTPStatusError
from langchain_core.tools import tool

from src.integrations.boond_client import BoondManagerClient

logger = logging.getLogger(__name__)


@tool(parse_docstring=True)
async def validate_timesheet(timesheet_id: int, expected_validator_id: int) -> Dict[str, Any]:
    """Validate a pending timesheet in BoondManager.

    This tool validates (approves) a timesheet that is pending validation. The validator
    must be authorized to approve the timesheet (typically the resource's manager or
    project supervisor).

    � IMPORTANT: Check the response warnings array for validation issues that may need
    attention even after successful validation.

    Args:
        timesheet_id: Unique identifier of the timesheet to validate
        expected_validator_id: Resource ID of the validator (manager/supervisor)

    Returns:
        {
            "meta": {
                "version": "...",                                    # BoondManager version
                "isLogged": true,
                "warnings": [                                        # � Validation warnings
                    {
                        "code": "moreThanNumberOfWorkingDays",      # Warning code
                        "detail": "Worker declared 23 days but calendar shows 22",
                        "project": {                                # Related project
                            "id": "8",
                            "reference": "PRJ-DEMO"
                        },
                        "delivery": {                               # Related delivery/assignment
                            "id": "18",
                            "title": "Full-stack development",
                            "startDate": "2025-09-01",
                            "endDate": "2025-12-31"
                        },
                        "workUnitType": {                           # Type of time entry
                            "reference": 1,
                            "name": "Normale"
                        }
                    }
                ],
                "expectedValidatorsAllowedForValidate": [           # Who can validate
                    {"id": "42", "firstName": "John", "lastName": "Doe"}
                ],
                "expectedValidatorsAllowedForUnvalidate": [         # Who can unvalidate
                    {"id": "42", "firstName": "John", "lastName": "Doe"}
                ],
                "expectedValidatorsAllowedForReject": [             # Who can reject
                    {"id": "42", "firstName": "John", "lastName": "Doe"}
                ]
            },
            "data": {
                "id": "5",
                "type": "timesreport",
                "attributes": {
                    "term": "2025-09",                              # Period (YYYY-MM)
                    "state": "validated",                           #  Now validated
                    "closed": false,                                # Is timesheet locked?
                    "creationDate": "2025-09-24T15:33:48+0200",
                    "updateDate": "2025-10-14T10:15:30+0200"       # Updated timestamp
                }
            }
        }

    Warning Codes (extract from meta.warnings[].code):
        - moreThanNumberOfWorkingDays: Worker declared more days than calendar shows
        - workplaceTimesMoreThanNumberOfWorkingDays: Workplace hours exceed expected
        - workplaceTimesLessThanNumberOfWorkingDays: Workplace hours below expected
        - atLeastOneAbsenceQuotaExceeded: Absence quota exceeded
        - wrongAbsences: Invalid absence entries
        - wrongMandatoryLeaves: Mandatory leave issues
        - noDeliveryOnProject: No delivery assignment on project
        - projectDoesNotExist: Referenced project not found
        - deliveryDoesNotExist: Referenced delivery not found
        - outsideContractDates: Work declared outside contract period
        - outsideDeliveryDates: Work outside delivery period
        - outsideDocumentDates: Work outside document valid dates
        - lessThanNumberOfWorkingDaysInsideContractDates: Under-declared within contract
        - moreThanNumberOfWorkingDaysInsideContractDates: Over-declared within contract
        - noSignedTimesheet: Timesheet not signed by worker
        - workUnitRatesNotEqual: Work unit rates mismatch

    Interesting Data to Extract:
        1. **Validation Status**: data.attributes.state � "validated" means success
        2. **Warnings**: meta.warnings[] � Critical validation issues requiring review
        3. **Warning Count**: len(meta.warnings) � Number of issues found
        4. **Project Issues**: Filter warnings by project ID to find project-specific problems
        5. **Delivery Issues**: warnings[].delivery � Assignment period conflicts
        6. **Authorized Validators**: meta.expectedValidatorsAllowed* � Who can manage this timesheet
        7. **Period**: data.attributes.term � Which month/period was validated
        8. **Update Timestamp**: data.attributes.updateDate � When validation occurred

    Common Warning Patterns:
        - Time discrepancies: moreThanNumberOfWorkingDays, workplaceTimesMore/LessThan...
        - Date conflicts: outsideContractDates, outsideDeliveryDates
        - Missing data: noDeliveryOnProject, noSignedTimesheet
        - Data integrity: deliveryDoesNotExist, workUnitRatesNotEqual

    Example:
        validate_timesheet(timesheet_id=5, expected_validator_id=42)
        � Validates timesheet 5 with validator resource 42
        � Returns validation status and warnings for review
    """
    client = BoondManagerClient()
    logger.info(f"Validating timesheet {timesheet_id} by validator {expected_validator_id}")

    try:
        result = await client.validate_timesheet(timesheet_id, expected_validator_id)

        # Extract key information for logging
        warnings_count = len(result.get("meta", {}).get("warnings", []))
        state = result.get("data", {}).get("attributes", {}).get("state", "unknown")

        logger.info(
            f"Successfully validated timesheet {timesheet_id}. "
            f"Status: {state}, Warnings: {warnings_count}"
        )

        return result

    except HTTPStatusError as e:
        logger.error(f"Error validating timesheet {timesheet_id}: {e}")
        return {
            "error": e.response.status_code,
            "message": f"Failed to validate timesheet {timesheet_id}.",
            "request": e.request,
            "api_response": e.response.text
        }


@tool(parse_docstring=True)
async def unvalidate_timesheet(timesheet_id: int, expected_validator_id: int) -> Dict[str, Any]:
    """Unvalidate (revoke approval of) a previously validated timesheet.

    This tool unvalidates a timesheet, reverting it from "validated" state back to
    "pending" state. Use when corrections are needed or validation was done in error.

    ⚠️ WARNING: Unvalidating may block invoicing workflows that depend on validated
    timesheets. Only use when corrections are necessary before billing.

    Args:
        timesheet_id: Unique identifier of the timesheet to unvalidate
        expected_validator_id: Resource ID of the validator (manager/supervisor)

    Returns:
        {
            "meta": {
                "version": "...",
                "warnings": [                                        # Same warnings as validate
                    {
                        "code": "moreThanNumberOfWorkingDays",
                        "detail": "Worker declared 23 days but calendar shows 22",
                        "project": {"id": "8", "reference": "PRJ-DEMO"},
                        "delivery": {...},
                        "workUnitType": {...}
                    }
                ],
                "expectedValidatorsAllowedForValidate": [...],      # Who can re-validate
                "expectedValidatorsAllowedForUnvalidate": [...],    # Who can unvalidate
                "expectedValidatorsAllowedForReject": [...]         # Who can reject
            },
            "data": {
                "id": "5",
                "type": "timesreport",
                "attributes": {
                    "term": "2025-09",
                    "state": "pending",                             # ⚠️ Now pending (unvalidated)
                    "closed": false,
                    "creationDate": "2025-09-24T15:33:48+0200",
                    "updateDate": "2025-10-14T10:30:15+0200"       # Updated timestamp
                }
            }
        }

    Use Cases:
        - Timesheet has errors that need correction before billing
        - Validation was performed by wrong validator
        - Worker needs to modify entries after validation
        - Time discrepancies discovered after validation
        - Preparing for corrections that require pending state

    Important Notes:
        1. Only validators with "unvalidate" permission can perform this action
        2. Timesheet must be in "validated" state to unvalidate
        3. Unvalidating blocks invoicing workflows until re-validated
        4. All validation warnings are re-evaluated and returned
        5. Worker can edit timesheet again after unvalidation

    Interesting Data to Extract:
        1. **State Change**: data.attributes.state → "pending" confirms unvalidation
        2. **Warnings**: meta.warnings[] → Issues that may need fixing before re-validation
        3. **Authorization**: meta.expectedValidatorsAllowedForValidate → Who can re-approve
        4. **Update Timestamp**: data.attributes.updateDate → When unvalidation occurred

    Example:
        unvalidate_timesheet(timesheet_id=5, expected_validator_id=42)
        → Reverts timesheet 5 back to pending state
        → Returns current warnings for review before re-validation
    """
    client = BoondManagerClient()
    logger.info(f"Unvalidating timesheet {timesheet_id} by validator {expected_validator_id}")

    try:
        result = await client.unvalidate_timesheet(timesheet_id, expected_validator_id)

        # Extract key information for logging
        warnings_count = len(result.get("meta", {}).get("warnings", []))
        state = result.get("data", {}).get("attributes", {}).get("state", "unknown")

        logger.info(
            f"Successfully unvalidated timesheet {timesheet_id}. "
            f"Status: {state}, Warnings: {warnings_count}"
        )

        return result

    except Exception as e:
        logger.error(f"Error unvalidating timesheet {timesheet_id}: {e}")
        return {
            "error": str(e),
            "data": None,
            "message": f"Failed to unvalidate timesheet {timesheet_id}. "
            f"Possible causes: invalid timesheet_id, validator not authorized, "
            f"timesheet not in validated state, or network error.",
        }
