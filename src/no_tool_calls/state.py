from typing import Annotated, Literal, Optional

from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import TypedDict


def update_dialog_stack(left: list[str], right: Optional[str] | Optional[list[str]]) -> list[str]:
    """Push or pop the state."""

    # we sometimes need to init from an existing state
    # right will be the existing state, so replace current by this
    # left will always be empty
    if isinstance(right, list):
        return right

    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    dialog_state: Annotated[
        list[str],
        update_dialog_stack,
    ]
