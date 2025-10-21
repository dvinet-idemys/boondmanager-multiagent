"""Dispatch Task Validation Middleware.

Validates that dispatch_tasks conform to query agent requirements:
- Open-ended questions (not verification statements)
- Atomic (one entity, one metric per task)
- Complete context (worker name, time period)
- Specific and independently executable
"""

import json
from typing import Any, Literal, NotRequired

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware, hook_config
from langchain.messages import HumanMessage, SystemMessage
from langgraph.runtime import Runtime
from pydantic import TypeAdapter
from typing_extensions import TypedDict

from src import llm_config

revisor_model = llm_config.get_llm()

REVISOR_PROMPT = """You are a dispatch task validator. Validate that ALL prompts follow query agent requirements.

## Input
```json
{"subagent": "query", "prompts": ["task1", "task2", ...]}
```

## Validation Checklist (per task)

### 1. Question Format ⚠️ CRITICAL
✅ Starts with: "How many", "What", "Which"
✅ Ends with "?"
❌ No verification verbs: "verify", "confirm", "check", "validate"
❌ No expected values in question

Examples:
✅ "How many days did Elodie LEGUAY work in September 2025?"
❌ "Verify Elodie worked 22 days" (verb + expected value)

### 2. Atomicity ⚠️ CRITICAL
✅ ONE entity only (one worker)
✅ ONE metric only (days OR cost, not both)
❌ No "and" combining entities
❌ No plurals ("workers", "projects")

Examples:
✅ "How many days did Elodie LEGUAY work in September 2025?"
❌ "How many days did Elodie and Didier work?" (multiple workers)

### 3. Context Completeness ⚠️ CRITICAL
✅ Full name: First AND Last name, any order
✅ Time period: "Month YYYY" **ONLY when querying temporal/time-bound data**
❌ No vague refs: "worker A", "the worker"

**When Time Period IS Required:**
- Activity metrics: days worked, hours, costs, timesheets
- Time-bound data: absences, schedules, project assignments in a period
- Any "how many" questions about countable time-based activities

**When Time Period is NOT Required:**
- Static attributes: email, phone, job title, department, manager
- Identity data: resource ID, legal name, birth date
- Organizational structure: reporting hierarchy, team membership
- Configuration: rates, roles, permissions (unless asking about historical changes)

Examples:
✅ "What is the email address for worker Elodie LEGUAY?" (static attribute - no period needed)
✅ "What is the job title for resource Didier GEIG?" (static attribute - no period needed)
✅ "How many days did Elodie LEGUAY work in September 2025?" (temporal data - period required)
✅ "How many days did LEGUAY Elodie work in September 2025?" (temporal data - period required)
❌ "How many days did Elodie work?" (missing last name + period for temporal query)
❌ "What is the email for Elodie?" (missing last name, but no period needed)

### 4. Specificity
✅ Exact metric: "days", "cost", "hours", "rate"
❌ No vague: "how much" without metric

### 5. Independence
✅ Self-contained
❌ No refs: "previous result", "above query"

## Output Format

**All Pass:**
```json
{
    "revision_status": "approved",
    "validated_calls": [("query", "task1"), ("query", "task2")],
    "errors": []
}
```

**Any Fail:**
```json
{
    "revision_status": "rejected",
    "validated_calls": [],
    "errors": [
        {
            "task_index": 0,
            "task": ["query", "bad task"],
            "violation": "question_format",
            "details": "Uses verification verb 'verify'",
            "suggestion": "How many days did Elodie LEGUAY work in September 2025?"
        }
    ]
}
```

## Violation Types
- `question_format`: Not an open-ended question
- `atomicity`: Multiple entities or metrics
- `context_completeness`: Missing required name or time period (for temporal queries only)
- `specificity`: Vague or ambiguous
- `independence`: References other tasks

⚠️ IMPORTANT: Only flag `context_completeness` for missing time periods when the query involves temporal/time-bound data (days worked, hours, costs, timesheets, etc.). Static attributes (email, phone, job title) do NOT require time periods.

Be strict. Reject ANY critical violation. Provide concrete fix suggestions."""


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
    validated_calls: list[tuple[str, str]]  # list of validated (subagent, prompt) pairs
    errors: list[ValidationError]


class RevisorState(AgentState):
    revisions: NotRequired[list[Revision]]


class ToolCallRevisorMiddleware(AgentMiddleware):
    state_schema = RevisorState

    def __init__(self, revised_tool_call: str, revisor_prompt: str = None):
        self.revised_tool_call = revised_tool_call

        if revisor_prompt is None:
            self.revisor_prompt = REVISOR_PROMPT
        else:
            self.revisor_prompt = revisor_prompt

    def before_model(self, state: RevisorState, runtime) -> dict[str, Any] | None:
        if (revs := state.get("revisions")) is None:
            return None

        return {"messages": [f"Tool call rejected:\n{revs}"], "revisions": None}

    @hook_config(can_jump_to=["model"])
    def after_model(self, state: RevisorState, runtime: Runtime):
        """Revise model output. Send back to beginning if rejected, continue
        if approved."""

        revisions: list[Revision] = []
        tool_calls_simple = []

        for call in state["messages"][-1].tool_calls:
            tool_calls_simple.append(f"{call['name']}: {call['args']}")
            if call["name"] != self.revised_tool_call:
                continue

            if call["args"]["subagent"] != "query":
                continue

            type_adapter = TypeAdapter(Revision)

            schema = type_adapter.json_schema()
            structured_model = revisor_model.with_structured_output(
                schema, method="function_calling", tool_choice="required"
            )

            response = structured_model.invoke(
                [
                    SystemMessage(self.revisor_prompt),
                    HumanMessage(json.dumps(call["args"])),
                ]
            )

            revisions.append(response)

        if all(r["revision_status"] == "approved" for r in revisions):
            return None

        print(f"tool call(s) rejected:\n{revisions}")

        # replace unfulfilled toolmessage with humanmessage
        state["messages"][-1] = HumanMessage(
            f"tried to call tool(s): \n{chr(10).join(tool_calls_simple)}"
        )

        return {"messages": state["messages"], "revisions": revisions, "jump_to": "model"}
