from langchain.tools.tool_node import _ToolNode
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.errors import GraphInterrupt
from langgraph.types import interrupt


def handle_tool_error(state) -> dict:
    error = state.get("error")

    # reraise GraphInterrupts for interrupts to work correctly
    if isinstance(error, GraphInterrupt):
        raise error

    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


# dummy handler to interrupt all tool calls
def handler(request, execute):
    # print(f"got interrupt: {interrupt(request.tool_call)}")
    return execute(request)


def create_tool_node_with_fallback(tools: list) -> dict:
    return _ToolNode(tools, wrap_tool_call=handler, awrap_tool_call=handler).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )
