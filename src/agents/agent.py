"""
React Agent Implementation with LangGraph

A simple React (Reasoning + Acting) agent that loops between:
1. LLM reasoning and tool selection
2. Tool execution
3. Back to LLM or END
"""

from dataclasses import dataclass
from typing import Annotated, Any

from langchain.tools.tool_node import _ToolNode as ToolNode
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphInterrupt
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition
from langgraph.types import Send, interrupt
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


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
    return ToolNode(tools, wrap_tool_call=handler, awrap_tool_call=handler).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


@dataclass
class Subagent:
    """Configuration for a subagent with its delegation tool.

    Attributes:
        name: Unique identifier for the subagent
        agent: The ReactAgent instance to delegate to
        delegation_tool: Pydantic model defining the delegation tool schema
    """

    name: str
    agent: "ReactAgent"
    delegation_tool: type[BaseModel]


# ============================================================================
# State Definition
# ============================================================================


class AgentState(TypedDict):
    """State for the React agent."""

    messages: Annotated[list[BaseMessage], add_messages]


# ============================================================================
# React Agent Class
# ============================================================================


class ReactAgent(Runnable):
    """React agent that loops between LLM reasoning and tool execution.

    This agent implements the ReAct (Reasoning + Acting) pattern:
    1. LLM reasons about the task and decides which tools to use
    2. Tools are executed (or delegated to subagents)
    3. Results are fed back to LLM
    4. Loop continues until task is complete

    Args:
        model: The chat model to use for reasoning
        system_prompt: System prompt to guide agent behavior
        tools: List of tools available to the agent
        subagents: Optional list of Subagent instances for delegation
        name: Optional name for the agent (used for graph identification)
    """

    def __init__(
        self,
        model: BaseChatModel,
        system_prompt: str,
        tools: list[BaseTool],
        subagents: list[Subagent] | None = None,
        name: str | None = None,
    ):
        """Initialize the React agent.

        Args:
            model: BaseChatModel instance (e.g., ChatOpenAI)
            system_prompt: Instructions for the agent's behavior
            tools: List of BaseTool instances available to agent
            subagents: Optional list of Subagent instances for delegation
            name: Optional name for the agent (used for graph identification)
        """
        self.model = model
        self.system_prompt = system_prompt
        self.subagents = subagents or []
        self.name = name

        # Build subagent lookup by name AND by delegation tool class name
        self.subagent_map: dict[str, Subagent] = {
            subagent.name: subagent for subagent in self.subagents
        }
        self.subagent_by_tool_name: dict[str, Subagent] = {
            subagent.delegation_tool.__name__: subagent for subagent in self.subagents
        }

        # Create delegation tools if subagents exist
        delegation_tools = []
        if self.subagents:
            # Add individual delegation tools
            delegation_tools.extend([s.delegation_tool for s in self.subagents])
            # Add generic batch delegation tool
            delegation_tools.append(self._create_delegation_tool())

        # Combine regular tools with delegation tools
        self.tools = list(tools)
        all_tools = self.tools + delegation_tools

        # Bind all tools to model
        self.llm_with_tools = self.model.bind_tools(all_tools)

        # Build the graph
        self.graph = self._build_graph()

    def _create_delegation_tool(self) -> type[BaseModel]:
        """Create a dynamic delegation tool that accepts a list of subagent delegation models.

        Returns:
            A Pydantic BaseModel class representing the delegation tool
        """

        # Create list of available subagent names
        available_names = ', '.join(s.name for s in self.subagents)

        # Create simplified docstring (individual tools have their own descriptions)
        delegation_docstring = f"""Batch delegation tool for sending multiple similar requests to ONE subagent in parallel.

Available subagents: {available_names}

Note: Each subagent also has its own individual delegation tool with detailed descriptions.
Use this batch tool when you need to send multiple similar requests to the same subagent.

Usage:
- Specify the subagent_name (exact match required)
- Provide a list of string requests describing the tasks
- All requests will be sent to the specified subagent in parallel

⚠️ CRITICAL REQUEST PATTERN REQUIREMENT:

All requests in a single delegation MUST follow the SAME pattern/template, varying ONLY specific values.

✅ CORRECT (same pattern, different values):
  requests: [
    "Get total cost for worker Alice SMITH on project X in September 2025",
    "Get total cost for worker Bob JONES on project Y in September 2025",
    "Get total cost for worker Carol BROWN on project Z in September 2025"
  ]

❌ WRONG (different patterns/operations):
  requests: [
    "Get total cost for worker Alice SMITH in September 2025",
    "Get project details for project X",
    "Count days worked by Bob JONES"
  ]

This ensures consistent parallel processing and reliable result aggregation.
If you need different operations, make separate delegation tool calls.
"""

        class DelegateToSubagents(BaseModel):
            subagent_name: str = Field(
                description=f"Name of the subagent to delegate to. Must be one of: {', '.join(s.name for s in self.subagents)}"
            )
            requests: list[str] = Field(
                description="List of task descriptions (as strings) to send to the subagent. Each string should contain all necessary context and information."
            )

        # Override the docstring with our dynamic version
        DelegateToSubagents.__doc__ = delegation_docstring

        # Store the tool name for routing
        self._delegation_tool_name = DelegateToSubagents.__name__

        return DelegateToSubagents

    def _create_subagent_wrapper(self, subagent: Subagent):
        """Create a wrapper function that executes subagent and returns only final response as ToolMessage.

        This prevents message pollution - parent agent only sees the final answer,
        not all intermediate reasoning/tool calls from the subagent.

        The wrapper converts the subagent's final AIMessage into a ToolMessage that
        the parent LLM expects in response to the delegation tool call.

        Args:
            subagent: The Subagent configuration

        Returns:
            Callable that executes subagent and extracts final response as ToolMessage
        """
        async def wrapper(state: AgentState) -> dict:
            # Execute the subagent graph with the incoming state
            result = await subagent.agent.graph.ainvoke(state)

            # Extract only the LAST message (final response from subagent)
            final_message = result["messages"][-1]

            # Get the content from the final message
            content = final_message.content if hasattr(final_message, 'content') else str(final_message)

            # Extract tool_call_id from the incoming HumanMessage name field
            # (we set this in _route_to_subagents when creating Send objects)
            tool_call_id = None
            for msg in state.get("messages", []):
                if hasattr(msg, "name") and msg.name:
                    tool_call_id = msg.name
                    break

            # Convert to ToolMessage with the matching tool_call_id
            if tool_call_id:
                tool_response = ToolMessage(
                    content=content,
                    tool_call_id=tool_call_id,
                )
                return {"messages": [tool_response]}
            else:
                # Fallback: return the original AI message
                # This shouldn't happen in normal operation
                return {"messages": [final_message]}

        return wrapper

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.

        Returns:
            Compiled StateGraph
        """
        # Create tool node
        tool_node = create_tool_node_with_fallback(self.tools)

        # Create graph
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("llm", self._call_llm)
        graph.add_node("tools", tool_node)

        # Add each subagent's compiled graph as a node, wrapped to extract only final response
        for subagent in self.subagents:
            # Wrap subagent to return only final message as ToolMessage
            graph.add_node(
                subagent.name,
                self._create_subagent_wrapper(subagent)
            )

        # Add edges
        graph.add_edge(START, "llm")

        # Conditional routing from llm
        if self.subagents:
            # Route to tools, subagents (via Send), or END
            graph.add_conditional_edges(
                "llm",
                self._route_after_llm,
            )
        else:
            # Standard routing to tools or END
            graph.add_conditional_edges(
                "llm",
                tools_condition,
            )

        # Loop back from tools to llm
        graph.add_edge("tools", "llm")

        # Loop back from each subagent to llm
        for subagent in self.subagents:
            graph.add_edge(subagent.name, "llm")

        memory = InMemorySaver()

        # Compile with formatted name if provided
        if self.name:
            graph_name = f"{self.name.title()} Graph"
            return graph.compile(
                checkpointer=memory,
                name=graph_name,
            )
        return graph.compile(
            checkpointer=memory,
        )

    def _call_llm(self, state: AgentState) -> dict:
        """Call the LLM with system prompt and current messages.

        Args:
            state: Current agent state with messages

        Returns:
            Updated state with LLM response
        """
        messages = state["messages"]

        # Prepend system prompt if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=self.system_prompt)] + messages

        response = self.llm_with_tools.invoke(messages)

        return {"messages": [response]}

    def _expand_batch_tool_calls(self, state: AgentState) -> AgentState:
        """Expand batch delegation tool calls into individual tool calls.

        When LLM calls the batch tool with multiple requests, this creates
        N individual tool calls (one per request) so each gets its own tool_call_id.

        Args:
            state: Current agent state

        Returns:
            Modified state with expanded tool calls
        """
        messages = list(state["messages"])

        # Find the last AI message with tool calls
        for i in reversed(range(len(messages))):
            msg = messages[i]
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                expanded_tool_calls = []

                for tool_call in msg.tool_calls:
                    tool_name = tool_call["name"]

                    # Expand batch delegation tool into individual calls
                    if tool_name == self._delegation_tool_name:
                        args = tool_call["args"]
                        subagent_name = args.get("subagent_name", "")
                        requests = args.get("requests", [])

                        # Get the delegation tool for this subagent
                        if subagent_name in self.subagent_map:
                            subagent = self.subagent_map[subagent_name]
                            delegation_tool_name = subagent.delegation_tool.__name__

                            # Create individual tool call for each request
                            for idx, request_str in enumerate(requests):
                                individual_call = {
                                    "name": delegation_tool_name,
                                    "args": {"requests": request_str},
                                    "id": f"{tool_call['id']}__{idx}",  # Unique ID per request
                                    "type": "tool_call"
                                }
                                expanded_tool_calls.append(individual_call)
                    else:
                        # Keep non-batch tool calls as-is
                        expanded_tool_calls.append(tool_call)

                # Replace tool_calls in the AI message
                from langchain_core.messages import AIMessage
                new_ai_message = AIMessage(
                    content=msg.content,
                    tool_calls=expanded_tool_calls
                )
                messages[i] = new_ai_message
                break

        return {"messages": messages}

    def _route_to_subagents(self, state: AgentState) -> list[Send]:
        """Route to subagents using Send API.

        This creates Send objects for both batch and individual delegation tool calls,
        enabling parallel processing across multiple subagents.

        Args:
            state: Current agent state

        Returns:
            List of Send objects for subagent invocations
        """
        # First, expand any batch tool calls into individual calls
        expanded_state = self._expand_batch_tool_calls(state)
        messages = expanded_state["messages"]

        # Find the last AI message with tool calls (after expansion)
        last_ai_message = None
        for msg in reversed(messages):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                last_ai_message = msg
                break

        if not last_ai_message:
            return []

        sends = []
        for tool_call in last_ai_message.tool_calls:
            tool_name = tool_call["name"]
            args = tool_call["args"]

            # After expansion, all delegation calls are individual (by class name)
            # Batch tool calls have been expanded in _expand_batch_tool_calls
            if tool_name in self.subagent_by_tool_name:
                subagent = self.subagent_by_tool_name[tool_name]

                # Extract the request field - try "requests" first, then "request"
                request_content = args.get("requests", args.get("request", ""))

                # If request_content is a string, use it directly
                # Pass tool_call_id through HumanMessage name field
                if isinstance(request_content, str):
                    sends.append(
                        Send(
                            subagent.name,
                            {"messages": [HumanMessage(
                                content=request_content,
                                name=tool_call["id"]  # Store tool_call_id in name field
                            )]},
                        )
                    )

        return sends

    def _route_after_llm(self, state: AgentState) -> str | list[Send]:
        """Route to tools, subagents (via Send), or END based on LLM output.

        Routing logic:
        1. Use tools_condition to check if there are tool calls
        2. If any delegation tool is called → return list of Send objects for subagents
        3. If other tools are called → route to "tools"
        4. Otherwise → route to END

        Args:
            state: Current agent state

        Returns:
            Next node name ("tools" or END) OR list of Send objects for parallel subagent invocation
        """
        # First check if there are any tool calls using tools_condition
        route = tools_condition(state)

        # If no tool calls, end
        if route == END:
            return END

        # Check if any delegation tool is being called
        messages = state["messages"]
        last_message = messages[-1]

        # Check for delegation tools and route to subagents via Send
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            # If it's a delegation tool, route to subagents
            if (tool_name == self._delegation_tool_name or
                tool_name in self.subagent_by_tool_name):
                # Return Send objects directly from LLM node
                return self._route_to_subagents(state)

        # Regular tool calls
        return "tools"

    def invoke(
        self,
        input: dict[str, Any] | list[BaseMessage],
        config: RunnableConfig | None = None,
    ) -> dict[str, Any]:
        """Synchronously invoke the agent.

        Args:
            input: Either a dict with "messages" key or a list of messages
            config: Optional runnable configuration

        Returns:
            Final state with all messages
        """
        # Normalize input
        if isinstance(input, list):
            input = {"messages": input}

        return self.graph.invoke(input, config)

    async def ainvoke(
        self,
        input: dict[str, Any] | list[BaseMessage],
        config: RunnableConfig | None = None,
    ) -> dict[str, Any]:
        """Asynchronously invoke the agent.

        Args:
            input: Either a dict with "messages" key or a list of messages
            config: Optional runnable configuration

        Returns:
            Final state with all messages
        """
        # Normalize input
        if isinstance(input, list):
            input = {"messages": input}

        return await self.graph.ainvoke(input, config)
