"""Project resolution node - match project names to BoondManager IDs using ReAct agent."""

import logging
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from src.integrations.boond_client import BoondManagerClient
from src.models.state import InvoiceWorkflowState
from src.llm_config import get_llm

logger = logging.getLogger(__name__)


@tool
async def get_boondmanager_projects() -> str:
    """Fetch all projects from BoondManager API.

    Returns JSON with projects including id, name, and client_id.
    """
    client = BoondManagerClient()
    response = await client.get_projects()

    projects = []
    for proj in response.get("data", []):
        projects.append({
            "id": proj.get("id"),
            "name": proj.get("attributes", {}).get("name", ""),
            "client_id": proj.get("relationships", {}).get("company", {}).get("data", {}).get("id")
        })

    import json
    return json.dumps(projects, indent=2)


async def resolve_projects(state: InvoiceWorkflowState) -> InvoiceWorkflowState:
    """Resolve project names to BoondManager IDs using ReAct agent.

    Args:
        state: Workflow state with parsed consultant activities

    Returns:
        Updated state with resolved project_id and client_id
    """
    logger.info("Project resolution node - using ReAct agent")

    try:
        # Get unique project names
        unique_projects = set()
        for activity in state["consultant_activities"]:
            if activity.get("project_name"):
                unique_projects.add(activity["project_name"])

        logger.info(f"Resolving {len(unique_projects)} unique projects")

        # Create ReAct agent with tool
        llm = get_llm()
        agent = create_react_agent(
            llm,
            tools=[get_boondmanager_projects],
        )

        # Agent prompt
        prompt = f"""# Project Name Resolution Task

## Objective
Match email project names to BoondManager project IDs.

## Email Project Names
{list(unique_projects)}

## Instructions
1. Fetch all BoondManager projects using the tool
2. Match each email project name to a BoondManager project
3. Use fuzzy matching for similar names (case-insensitive, partial matches)
4. Return JSON mapping with format:

```json
{{
  "email_project_name": {{
    "project_id": "matched_id",
    "client_id": "client_id",
    "matched_name": "actual_boond_name"
  }}
}}
```

Return ONLY the JSON mapping, nothing else."""

        # Run agent
        result = await agent.ainvoke({"messages": [("user", prompt)]})

        # Parse agent response
        import json
        last_message = result["messages"][-1].content
        project_mapping = json.loads(last_message)

        # Update consultant activities
        for activity in state["consultant_activities"]:
            project_name = activity.get("project_name")
            if project_name and project_name in project_mapping:
                mapping = project_mapping[project_name]
                activity["project_id"] = mapping["project_id"]
                activity["client_id"] = mapping["client_id"]
                activity["project_name"] = mapping["matched_name"]

                logger.info(f"Resolved '{project_name}' → {mapping['project_id']}")

        state["current_step"] = "reconciliation"

    except Exception as e:
        logger.error(f"Project resolution failed: {e}")
        state["errors"].append(f"Project resolution error: {str(e)}")
        state["current_step"] = "completed"

    return state
