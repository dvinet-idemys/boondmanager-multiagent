
from typing import Any, Sequence

from langchain_core.tools import tool


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
