import json
import pathlib
from typing import Literal, NotRequired

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.runtime import Runtime
from pydantic import TypeAdapter
from typing_extensions import TypedDict

from src import llm_config

# TODO: move to llm_config
revisor_model = llm_config.get_llm()

REVISOR_PROMPT = (
    pathlib.Path(__file__).parent.parent.parent / "docs/DISPATCH_VERIFICATION_REQUIREMENTS.md"
).read_text()


class ValidationSummary(TypedDict):
    total_tasks: int
    failed_tasks: int
    passed_tasks: int
    critical_issues: int


class ValidationError(TypedDict):
    task_index: int
    task: tuple[str, str]
    violation: str
    details: str
    suggestion: str


class Revision(TypedDict):
    revision_status: Literal["approved", "rejected"]
    validated_calls: NotRequired[
        list[tuple[str, str]]
    ]  # list of validated (subagent, prompt) pairs
    errors: NotRequired[list[ValidationError]]


class RevisorState(AgentState):
    revisions: NotRequired[list[Revision]]


class ToolCallRevisorMiddleware(AgentMiddleware):
    def __init__(self, revised_tool_call: str, revisor_prompt: str = None):
        self.revised_tool_call = revised_tool_call

        if revisor_prompt is None:
            self.revisor_prompt = REVISOR_PROMPT
        else:
            self.revisor_prompt = revisor_prompt

    def after_model(self, state: RevisorState, runtime: Runtime):
        """Revise model output. Send back to beginning if rejected, continue
        if approved."""

        for call in state["messages"][-1].tool_calls:
            print(f"tool call: {call}")
            print()

            if call["name"] != self.revised_tool_call:
                return

            print("revising tool call.")

            type_adapter = TypeAdapter(Revision)

            schema = type_adapter.json_schema()
            structured_model = revisor_model.with_structured_output(schema)

            response = structured_model.invoke(
                [
                    SystemMessage(self.revisor_prompt),
                    HumanMessage(json.dumps(call["args"])),
                ]
            )

            print(f"""Revisor output:
{response}

from message:

{state["messages"][-1]}
""")
