from typing import TYPE_CHECKING, Callable

from langchain.messages import ToolMessage
from langgraph.graph import END
from langgraph.prebuilt import tools_condition
from pydantic import BaseModel

from src.no_tool_calls.state import State

if TYPE_CHECKING:
    from src.no_tool_calls.assistant import Subagent


def create_primary_assistant_router(subagents: list["Subagent"]):
    def route_primary_assistant(
        state: State,
    ):
        route = tools_condition(state)

        if route == END:
            return END

        tool_calls = state["messages"][-1].tool_calls
        if tool_calls:
            for subagent in subagents:
                if tool_calls[0]["name"] == subagent.to_subagent_fn.__name__:
                    return f"enter_{subagent.name}"

            return "primary_assistant_tools"

        raise ValueError("Invalid route")

    return route_primary_assistant


# This node will be shared for exiting all specialized assistants
def pop_dialog_state(state: State) -> dict:
    """Pop the dialog stack and return to the main assistant.

    This lets the full graph explicitly track the dialog flow and delegate control
    to specific sub-graphs.
    """
    messages = []
    subagent_messages = state.get("subagent_messages")

    # Handle truncated subagent exit
    if subagent_messages is not None:
        # Extract the last message from subagent (the result)
        if subagent_messages:
            last_msg = subagent_messages[-1]
            # Add subagent result to main message history
            messages.append(
                ToolMessage(
                    content=f"Subagent completed. Result: {last_msg.content if hasattr(last_msg, 'content') else str(last_msg)}",
                    tool_call_id=state["messages"][-1].tool_call_id,
                )
            )
        return {
            "dialog_state": "pop",
            "messages": messages,
            "subagent_messages": "clear",  # Clear isolated history
        }

    # Handle normal subagent exit (full context mode)
    if state["messages"][-1].tool_calls:
        # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )

    return {
        "dialog_state": "pop",
        "messages": messages,
    }


# Each delegated workflow can directly respond to the user
# When the user responds, we want to return to the currently active workflow
# Used when resuming execution of the graph.
def create_router_fn(assistant_name: str, subagent_names: list[str]):
    def route_to_workflow(state: State):
        """If we are in a delegated state, route directly to the appropriate assistant."""

        dialog_state = state.get("dialog_state")
        if not dialog_state:
            return "primary_assistant"

        depth = 1
        while depth <= len(dialog_state):
            last_state = dialog_state[-depth]
            if last_state == assistant_name:
                return "primary_assistant"
            elif last_state in subagent_names:
                return last_state
            else:
                depth += 1

        raise RuntimeError(
            f"couldn't walk dialog state back. dialog state: {state['dialog_state']}"
        )

    return route_to_workflow


def create_entry_node(
    assistant_name: str, new_dialog_state: str, truncate_state: bool = False
) -> Callable:
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        tool_call = state["messages"][-1].tool_calls[0]

        if truncate_state:
            # Extract the request from the tool call arguments
            request = tool_call.get("args", {}).get("request", "")

            # Create isolated message history with just the task
            isolated_messages = [
                ToolMessage(
                    content=f"You are now the {assistant_name}. Your task:\n\n{request}\n\n"
                    f"Use the provided tools to complete this task. "
                    f"When finished, call CompleteOrEscalate to return control.",
                    tool_call_id=tool_call_id,
                )
            ]

            return {
                "subagent_messages": isolated_messages,
                "dialog_state": new_dialog_state,
            }
        else:
            # Default: full context - add transition message to main messages
            return {
                "messages": [
                    ToolMessage(
                        content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                        f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                        " and the booking, update, other other action is not complete until after you have successfully invoked the appropriate tool."
                        " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                        " Do not mention who you are - just act as the proxy for the assistant.",
                        tool_call_id=tool_call_id,
                    )
                ],
                "dialog_state": new_dialog_state,
            }

    return entry_node


class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs."""

    cancel: bool = True
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            "example 3": {
                "cancel": False,
                "reason": "I need to search the user's emails or calendar for more information.",
            },
        }


def create_subagent_route(subagent_name: str):
    def subagent_route(state: State):
        route = tools_condition(state)

        if route == END:
            return "leave_skill"

        tool_calls = state["messages"][-1].tool_calls

        did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
        if did_cancel:
            return "leave_skill"

        return f"{subagent_name}_tools"

    return subagent_route
