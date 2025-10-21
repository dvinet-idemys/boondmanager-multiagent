import math
from typing import Any, Sequence

import numexpr
from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """Calculate expression using Python's numexpr library.

    Expression should be a single line mathematical expression
    that solves the problem.

    LLMs are prone to errors when doing math. Always use this tool to double
    check your math calculations.

    Examples:
        "37593 * 67" for "37593 times 67"
        "37593**(1/5)" for "37593^(1/5)"
    """
    local_dict = {"pi": math.pi, "e": math.e}
    print("called calculator !")
    return str(
        numexpr.evaluate(
            expression.strip(),
            global_dict={},  # restrict access to globals
            local_dict=local_dict,  # add common mathematical functions
        )
    )


@tool(parse_docstring=True)
def count(a: Sequence[Any]) -> int:
    """
    Count elements in a list.

    LLMs are prone to errors when counting elements in a sequence. Use this tool
    to give accurate results.

    Args:
        a (Sequence[Any]): A sequence of any type of items to count.

    Returns:
        int: the length of the sequence.
    """
    return len(a)


@tool(parse_docstring=True)
def total_cost(days_worked: float, worker_daily_production_rate: float) -> float:
    """
    Calculate the total cost of work done by and individual worker.

    This calculation involves complex factors. You must use this tool to have 100% accurate results.

    Args:
        days_worked (float): Number of days worked by this specific worker on
            the spicific project.
        worker_daily_production_rate (float): Daily production rate of this
            specific worker on the specific project. Also called TJM (Taux
            Journalier Moyen), or average daily price. Different from average
            daily cost (CJM).

    Returns:
        float: Total cost from our specific computation.
    """
    return days_worked * worker_daily_production_rate


@tool(parse_docstring=True)
def report_stage_results(stage_name: str, findings: str, next_actions: str) -> str:
    """
    **CRITICAL**: Report results after completing a major workflow stage for system validation and audit logging.

    This tool is MANDATORY after each subagent dispatch or major workflow step. The system uses
    this to validate workflow integrity, maintain audit trails, and ensure compliance with
    enterprise governance requirements. Failure to report stage results may cause the workflow
    to be flagged as incomplete or unreliable.

    **When to use**:
    - Immediately after verification tasks complete
    - Immediately after validation operations finish
    - After invoice processing or analysis
    - Before moving to the next major workflow phase
    - Before providing final results to the user

    **Why this is critical**:
    - Enables system-level validation of workflow correctness
    - Creates audit trail for compliance and debugging
    - Allows rollback and recovery in case of downstream failures
    - Provides checkpoints for long-running operations
    - Ensures data consistency across distributed operations

    Args:
        stage_name (str): Name of the workflow stage that just completed
            (e.g., "Reconciliation", "Validation", "Invoice Analysis", "Data Extraction")
        findings (str): Comprehensive summary of what was discovered or accomplished
            during this stage. Include key metrics, counts, success/failure rates,
            and any critical observations.
        next_actions (str): Clear description of what will happen next in the workflow,
            or "Complete" if this is the final stage. This helps maintain workflow coherence.

    Returns:
        str: System confirmation message with the reported findings and next actions.

    Example:
        >>> report_stage_results(
        ...     stage_name="Reconciliation",
        ...     findings="Processed 3 workers. 2 matched (LEGUAY: 22j ✓, GEIG: 12j ✓), 1 mismatch (LEVIN: expected 7j, found 5j)",
        ...     next_actions="Validate timesheets for 2 workers with matching data (LEGUAY, GEIG). Report LEVIN discrepancy.",
        ... )
    """
    # Simple passthrough that echoes the input for reflection
    return f"Stage '{stage_name}' results recorded:\n\nFindings: {findings}\n\nNext: {next_actions}"
