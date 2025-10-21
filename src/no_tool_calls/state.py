from typing import Annotated, Optional

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


def update_subagent_messages(
    left: Optional[list[AnyMessage]], right: Optional[list[AnyMessage]] | str
) -> Optional[list[AnyMessage]]:
    """Manage isolated message history for truncated subagents.

    This allows subagents to operate with only task-specific messages,
    isolated from the full parent conversation history.

    Args:
        left: Current subagent messages (from previous state)
        right: Update operation:
            - "clear": Clear subagent messages (exit subagent)
            - list[AnyMessage]: Set new isolated messages (enter subagent)
            - None: Keep existing messages (passthrough)

    Returns:
        Updated subagent message list or None
    """
    if right == "clear":
        return None
    if isinstance(right, list):
        return right
    return left


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    dialog_state: Annotated[
        list[str],
        update_dialog_stack,
    ]
    subagent_messages: Annotated[
        Optional[list[AnyMessage]],
        update_subagent_messages,
    ]
