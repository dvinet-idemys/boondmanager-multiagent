import uuid

from langchain.messages import ToolMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command


def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)


async def invoke_and_print_agent(agent: CompiledStateGraph, prompt: str):
    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            # Checkpoints are accessed by thread_id
            "thread_id": thread_id,
        },
        "recursion_limit": 100,
    }

    _printed = set()
    # We can reuse the tutorial questions from part 1 to see how it does.
    agent_input = {"messages": [("user", prompt)]}

    while True:
        events = agent.astream(agent_input, config, stream_mode="values")
        async for event in events:
            _print_event(event, _printed)
        snapshot = agent.get_state(config)
        messages = []

        if not snapshot.next:
            break

        else:
            # We have an interrupt! The agent is trying to use a tool, and the user can approve or deny it
            # Note: This code is all outside of your graph. Typically, you would stream the output to a UI.
            # Then, you would have the frontend trigger a new run via an API call when the user has provided input.
            user_input = input(
                "Do you approve of the above actions? Type 'y' to continue;"
                " otherwise, explain your requested changed.\n\n"
            )
            if user_input == "y":
                agent_input = (
                    Command(
                        resume={"decisions": [{"type": "approve"}]}  # or "edit", "reject"
                    ),
                )
            else:
                agent_input = (
                    Command(
                        resume={
                            "decisions": [
                                {
                                    "type": "reject",
                                    # An explanation about why the action was rejected
                                    "message": user_input,
                                }
                            ]
                        }
                    ),
                )
