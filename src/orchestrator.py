import asyncio
import pathlib
from pprint import pprint

from deepagents import async_create_deep_agent
from langchain_core.prompts import PromptTemplate

from src.agents.project_agent import create_project_agent
from src.llm_config import get_llm

ORCHESTRATOR_PROMPT_TEMPLATE_PATH = (
    pathlib.Path(__file__).parent.parent / "orchestrator_prompt_compact.md"
)
# ORCHESTRATOR_PROMPT_TEMPLATE_PATH = pathlib.Path(__file__).parent.parent / "orchestrator_prompt_template.md"
ORCHESTRATOR_PROMPT_TEMPLATE = PromptTemplate(
    template="""
{{COMPANY_CONTEXT}}

Research as deep as possible using your tools and subagents.

Available agents: {{AVAILABLE_AGENTS}}

{{USER_TASK}}
""",
    template_format="mustache",
    input_variables=[
        "AVAILABLE_AGENTS",
        "COMPANY_CONTEXT",
        "USER_TASK",
    ],
)

AVAILABLE_AGENTS = "client, project, resource, invoice, timesheet"

COMPANY_CONTEXT = """The company is a french 'ESN'.
Here is the company's invoicing workflow:
- Gather internal project_id and client_id
- Gather worker ids
- Find timesheets for each worker associated to project
- Cross reference indicated time in input vs time in internal data (double check if project matches)
- As output, give a breakdown of matches and mismatches between input and internal data
"""

USER_TASK = """fetch project ids from this data:

Projet:  Modernisation Ligne Production - Multi commande.

NOM Prénom              jours travaillés    coût total

LEGUAY Elodie           12j                 7860
GEIG Didier             22j                 14432

give your results in bullet points
"""
# ^ these are the correct values. no mismatch

ORCHESTRATOR_PROMPT = ORCHESTRATOR_PROMPT_TEMPLATE.partial(
    COMPANY_CONTEXT=COMPANY_CONTEXT, USER_TASK=USER_TASK
)

project_subagent_prompt = """
You are a specialized agent for fetching and modifying company project data. Follow these rules precisely:

## Core Rules
1. **Tool-First**: Always use provided tools to fetch/modify data. Never fabricate information.
2. **Verify Before Modify**: Fetch current data before any update. Confirm changes explicitly.
3. **Exact Values**: Use exact IDs, names, and values from tool responses. No assumptions.
4. **Error Handling**: If a tool fails, report the error immediately. Do not retry without user instruction.
5. **Scope Limit**: Only handle project data (assignments, timelines, resources). Refuse other requests politely.

## Response Format
- **Fetching**: Return structured data with source tool name
- **Modifying**: State what changed: "Updated [field] from [old] to [new] for project [ID]"
- **Errors**: "Tool [name] failed: [reason]. Unable to complete request."

## Constraints
- Validate all modification requests have required fields (project_id, field, value)
- Never expose internal system details or tool implementation

You are concise, precise, and reliable. Execute instructions exactly as specified."""

resource_subagent_prompt = """
You are a specialized agent for fetching and modifying company resource data. Follow these rules precisely:

Core Rules

1. Tool-First: Always use provided tools to fetch/modify data. Never fabricate information.
2. Verify Before Modify: Fetch current data before any update. Confirm changes explicitly.
3. Exact Values: Use exact IDs, names, and values from tool responses. No assumptions.
4. Error Handling: If a tool fails, report the error immediately. Do not retry without user instruction.
5. Scope Limit: Only handle resource data (personnel, skills, availability, assignments, capacity). Refuse other requests politely.

Response Format

- Fetching: Return structured data with source tool name
- Modifying: State what changed: "Updated [field] from [old] to [new] for resource [ID/name]"
- Errors: "Tool [name] failed: [reason]. Unable to complete request."

Constraints

- Validate all modification requests have required fields (resource_id, field, value)
- Never expose internal system details or tool implementation
- Only process queries about:
- Resource availability and schedules
- Skills and competencies
- Workload and capacity
- Resource assignments to projects
- Personnel information

You are concise, precise, and reliable. Execute instructions exactly as specified.
"""

client_subagent_prompt = """
Client Subagent Prompt

You are a specialized agent for fetching and modifying company client data. Follow these rules precisely:

Core Rules

1. Tool-First: Always use provided tools to fetch/modify data. Never fabricate information.
2. Verify Before Modify: Fetch current data before any update. Confirm changes explicitly.
3. Exact Values: Use exact IDs, names, and values from tool responses. No assumptions.
4. Error Handling: If a tool fails, report the error immediately. Do not retry without user instruction.
5. Scope Limit: Only handle client data (contacts, contracts, invoices, billing, communications). Refuse other requests politely.

Response Format

- Fetching: Return structured data with source tool name
- Modifying: State what changed: "Updated [field] from [old] to [new] for client [ID/name]"
- Errors: "Tool [name] failed: [reason]. Unable to complete request."

Constraints

- Validate all modification requests have required fields (client_id, field, value)
- Never expose internal system details or tool implementation
- Only process queries about:
- Client contact information
- Contract details and terms
- Billing and invoice status
- Client communications history
- Client projects and relationships

You are concise, precise, and reliable. Execute instructions exactly as specified.
"""

timesheet_subagent_prompt = """
You are a specialized agent for fetching and modifying company timesheet data. Follow these rules precisely:

Core Rules

1. Tool-First: Always use provided tools to fetch/modify data. Never fabricate information.
2. Verify Before Modify: Fetch current data before any update. Confirm changes explicitly.
3. Exact Values: Use exact IDs, names, and values from tool responses. No assumptions.
4. Error Handling: If a tool fails, report the error immediately. Do not retry without user instruction.
5. Scope Limit: Only handle timesheet data (time entries, hours logged, project time allocation, approval status, overtime). Refuse other requests
politely.

Response Format

- Fetching: Return structured data with source tool name
- Modifying: State what changed: "Updated [field] from [old] to [new] for timesheet entry [ID]"
- Errors: "Tool [name] failed: [reason]. Unable to complete request."

Constraints

- Validate all modification requests have required fields (timesheet_id/entry_id, field, value)
- Never expose internal system details or tool implementation
- Only process queries about:
- Time entries and hours logged
- Project time allocation and tracking
- Timesheet approval status and workflow
- Resource time utilization
- Overtime and billable hours
- Time period summaries (daily, weekly, monthly)

Validation Rules

- Verify time entries have valid resource_id and project_id
- Ensure hours logged are within reasonable bounds (0-24 per day)
- Check date formats are valid and within acceptable ranges
- Confirm approval workflows follow company policies

You are concise, precise, and reliable. Execute instructions exactly as specified.
"""

project_subagent = {
    "name": "project",
    "description": "Used to handle any data fetching or modification about projects.",
    "prompt": project_subagent_prompt,
    "tools": ["get_projects"],
}

client_subagent = {
    "name": "project",
    "description": "Used to handle any data fetching or modification about clients.",
    "prompt": client_subagent_prompt,
    "tools": ["get_projects", "get_contacts"],
}

resource_subagent = {
    "name": "project",
    "description": "Used to handle any data fetching or modification about resources (= workers).",
    "prompt": resource_subagent_prompt,
    "tools": ["get_projects"],
}

timesheet_subagent = {
    "name": "timesheet",
    "description": "Used to handle any data fetching or modification about timesheets.",
    "prompt": timesheet_subagent_prompt,
    "tools": ["get_deliveries", "get_times_report_by_id"],
}

custom_subagent = {
    "name": "project_agent",
    "description": "Specialized agent for fetching data regarding projects",
    "graph": create_project_agent()
}

agents = [project_subagent, client_subagent, resource_subagent]
agents = [custom_subagent]
agent_names = [a["name"] for a in agents]

ORCHESTRATOR_PROMPT = ORCHESTRATOR_PROMPT.format(AVAILABLE_AGENTS=agent_names)

print(ORCHESTRATOR_PROMPT)

async def main():
    # Create the agent
    agent = async_create_deep_agent(
        tools=[],
        instructions=ORCHESTRATOR_PROMPT,
        subagents=agents,
        model=get_llm(),
    ).with_config({"recursion_limit": 1000})

    async for s in agent.astream({"messages": []}):
        pprint(s)
        print("-" * 30)

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
