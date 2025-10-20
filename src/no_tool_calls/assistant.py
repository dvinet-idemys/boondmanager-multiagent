from dataclasses import dataclass
from typing import Callable

from langchain.chat_models import BaseChatModel
from langchain.messages import SystemMessage
from langchain.tools import BaseTool
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from src.no_tool_calls.routing import (
    create_entry_node,
    create_primary_assistant_router,
    create_router_fn,
    create_subagent_route,
    pop_dialog_state,
)
from src.no_tool_calls.state import State
from src.no_tool_calls.tools import create_tool_node_with_fallback


class AssistantNode:
    def __init__(self, model: BaseChatModel, system_prompt: str, tools: list[BaseTool], truncate_msgs: bool = False):
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools
        self.truncate_msgs = truncate_msgs

        self.runnable = self.model.bind_tools(self.tools)
        self.runnable_is_graph = False

    def acall(self):
        async def _acall(state: State, config: RunnableConfig):
            # TODO
            # if self.truncate_msgs:
            #     state["messages"] = [state.get("messages", ["", ""])[-2:]]

            if state.get("messages") is None or len(state["messages"]) == 0:
                state["messages"] = [SystemMessage(self.system_prompt)]

            if not isinstance(state["messages"][0], SystemMessage):
                state["messages"] = [SystemMessage(self.system_prompt)] + state["messages"]

            while True:
                if self.runnable_is_graph:
                    new_state = await self.runnable.ainvoke(state, config)
                    result = new_state["messages"][1:]  # remove injected system message from history
                    break
                else:
                    result = await self.runnable.ainvoke(state["messages"])

                if not result.tool_calls and (
                    not result.content
                    or isinstance(result.content, list)
                    and not result.content[0].get("text")
                ):
                    messages = state["messages"] + [("user", "Respond with a real output.")]
                    state = {**state, "messages": messages}
                else:
                    break

            return {"messages": result}

        return _acall

    def __call__(self, state: State, config: RunnableConfig):
        if state.get("messages") is None or len(state["messages"]) == 0:
            state["messages"] = [SystemMessage(self.system_prompt)]

        if not isinstance(state["messages"], SystemMessage):
            state["messages"] = [SystemMessage(self.system_prompt)] + state["messages"]

        while True:
            if self.runnable_is_graph:
                result = self.runnable.invoke(state, config)["messages"]
                break
            else:
                result = self.runnable.invoke(state["messages"])

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break

        return {"messages": result}


@dataclass
class Subagent:
    name: str
    full_name: str
    description: str
    node: AssistantNode
    tools: list[BaseTool]
    to_subagent_fn: Callable


class AssistantWithSubagents(AssistantNode):
    def __init__(
        self,
        model: BaseChatModel,
        system_prompt: str,
        tools: list[BaseTool],
        subagents: list[Subagent],
        name: str = "primary_assistant",
        truncate_msgs: bool = False
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools + [subagent.to_subagent_fn for subagent in subagents]
        self.subagents = subagents
        self.name = name
        self.truncate_msgs = truncate_msgs

        self.runnable_is_graph = True

        self.node = AssistantNode(model, system_prompt, self.tools)

        builder = StateGraph(State)

        for subagent in self.subagents:
            builder.add_node(
                f"enter_{subagent.name}",
                create_entry_node(subagent.full_name, subagent.name),
            )
            builder.add_node(subagent.name, subagent.node.acall())
            builder.add_edge(f"enter_{subagent.name}", subagent.name)

            builder.add_node(
                f"{subagent.name}_tools", create_tool_node_with_fallback(subagent.tools)
            )

            builder.add_edge(f"{subagent.name}_tools", subagent.name)
            builder.add_conditional_edges(
                subagent.name,
                create_subagent_route(subagent.name),
                [f"{subagent.name}_tools", "leave_skill"],
            )

        builder.add_node("leave_skill", pop_dialog_state)
        builder.add_edge("leave_skill", "primary_assistant")

        # Primary assistant
        builder.add_node("primary_assistant", self.node.acall())
        builder.add_node("primary_assistant_tools", create_tool_node_with_fallback(self.tools))

        # add main agent and subagents edges after creation
        builder.add_conditional_edges(
            START,
            create_router_fn(self.name, [s.name for s in self.subagents]),
            [s.name for s in self.subagents] + ["primary_assistant"],
        )

        # The assistant can route to one of the delegated assistants,
        # directly use a tool, or directly respond to the user
        builder.add_conditional_edges(
            "primary_assistant",
            create_primary_assistant_router(self.subagents),
            [f"enter_{subagent.name}" for subagent in self.subagents]
            + [
                "primary_assistant_tools",
                END,
            ],
        )
        builder.add_edge("primary_assistant_tools", "primary_assistant")

        # Compile graph
        memory = InMemorySaver()
        self.runnable = builder.compile(
            checkpointer=memory,
            name=f"{self.name} Graph",
            # TODO: interrupt before sensitive tools
            # interrupt_before=[
            #     "update_flight_sensitive_tools",
            #     "book_car_rental_sensitive_tools",
            #     "book_hotel_sensitive_tools",
            #     "book_excursion_sensitive_tools",
            # ],
        )
