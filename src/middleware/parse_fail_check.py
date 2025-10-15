from typing import Callable

from langchain.agents.middleware import (
    AgentMiddleware,
    ModelRequest,
)
from langchain.agents.middleware.types import ModelResponse
from langchain_core.messages import AIMessage


class CheckParsingFailureMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ):
        for attempt in range(3):
            ret = handler(request)

            assistant_message: AIMessage
            for msg in ret.result:
                assistant_message = msg

            if assistant_message.content == "" and len(assistant_message.tool_calls) == 0:
                print("received empty message")
                print(f"full response: {ret}")
                print(f"\nRetry {attempt + 1}/3")
            else:
                return ret

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler,
    ):
        for attempt in range(3):
            ret = await handler(request)

            assistant_message: AIMessage
            for msg in ret.result:
                assistant_message = msg

            if assistant_message.content == "" and len(assistant_message.tool_calls) == 0:
                print("received empty message")
                print(f"full response: {ret}")
                print(f"\nRetry {attempt + 1}/3")
            else:
                return ret
