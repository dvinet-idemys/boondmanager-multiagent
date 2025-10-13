# BoondManager Project Agent 🤖

A standalone LangGraph-based AI agent for fetching and parsing project data from BoondManager CRM using natural language queries.

## 📋 Overview

This agent enables natural language interaction with the BoondManager API, specifically focused on **project data operations**. It understands queries like:

- *"Fetch the project id for project alpha"*
- *"Give me names and ids for workers associated with project id 4"*
- *"What's the status and workers for project Modernisation?"*

### Key Features

✅ **Natural Language Understanding** - Ask questions in plain language
✅ **Intelligent Tool Selection** - Automatically chooses the right API endpoints
✅ **Multi-Step Reasoning** - Chains multiple API calls for complex queries
✅ **Error Handling** - Graceful degradation with helpful error messages
✅ **Extensible Architecture** - Easy to add new endpoints and capabilities

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Query (NL)                         │
│          "Give me workers on project Alpha"                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Project Agent (LangGraph)                 │
│  • Understands intent                                       │
│  • Selects appropriate tools                                │
│  • Orchestrates multi-step workflows                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│search_      │ │get_project_ │ │get_project_ │
│projects     │ │by_id        │ │productivity │
└─────┬───────┘ └─────┬───────┘ └─────┬───────┘
      │               │               │
      └───────────────┼───────────────┘
                      │
                      ▼
          ┌───────────────────────┐
          │ BoondManager API      │
          │ (REST endpoints)      │
          └───────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- BoondManager API credentials
- Virtual environment

### Installation

```bash
# Clone and navigate to project
cd boondmanager-multiagent

# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies (already installed via pyproject.toml)
# Dependencies: langgraph, httpx, pydantic, deepagents, langchain-openai
```

### Configuration

Create/verify `.env` file with your credentials:

```env
# BoondManager API
BOOND_USER_TOKEN=your_user_token
BOOND_CLIENT_TOKEN=your_client_token
BOOND_CLIENT_KEY=your_signing_key

# LLM Configuration (optional - defaults to local)
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=dummy
LLM_MODEL=openai/gpt-oss-20b
LLM_TEMPERATURE=0
```

### Basic Usage

```python
import asyncio
from src.agents.project_agent import create_project_agent

async def main():
    # Create the agent
    agent = create_project_agent()

    # Ask a question
    query = "Fetch the project id for project alpha"

    # Stream the response
    async for message in agent.astream({"messages": [("user", query)]}):
        if "messages" in message:
            for msg in message["messages"]:
                if hasattr(msg, "content") and msg.content:
                    print(msg.content)

asyncio.run(main())
```

### Run Examples

```bash
# Run comprehensive example queries
python examples/project_queries.py

# Run demo from agent module
python -m src.agents.project_agent
```

## 🛠️ Available Tools

The agent has access to 7 specialized tools that wrap BoondManager API endpoints:

### Core Tools (Phase 1 - High Priority)

| Tool | Endpoint | Purpose | Example Query |
|------|----------|---------|---------------|
| `search_projects` | `GET /projects` | Find projects by keywords, company, dates, etc. | "Find project Alpha" |
| `get_project_by_id` | `GET /projects/{id}` | Get basic project data by ID | "Get details for project 4" |
| `get_project_productivity` | `GET /projects/{id}/productivity` | Get resource assignments & timesheets | "Who works on project 4?" |

### Extended Tools (Phase 2 - Medium Priority)

| Tool | Endpoint | Purpose | Example Query |
|------|----------|---------|---------------|
| `get_project_information` | `GET /projects/{id}/information` | Get detailed project information | "Get full details for project 4" |
| `get_project_orders` | `GET /projects/{id}/orders` | Get project orders & billing | "What are orders for project 8?" |
| `get_project_tasks` | `GET /projects/{id}/tasks` | Get project tasks | "Show tasks in project 15" |
| `get_project_rights` | `GET /projects/{id}/rights` | Get access rights | "Who can access project 4?" |

## 📝 Example Queries

### Simple Lookups

```python
# Find a project by name
"Fetch the project id for project alpha"
"Find project Modernisation"

# Get project details
"Get details for project 4"
"What is the status of project 12345?"
```

### Worker/Resource Queries

```python
# Find workers on a project
"Give me names and ids for workers associated with project id 4"
"Who is working on project alpha?"
"Get resource assignments for project 12"
```

### Multi-Step Queries

```python
# Complex queries requiring multiple API calls
"What's the status and workers for project Modernisation?"
"Find project Alpha and tell me who works on it"
```

### Filtered Searches

```python
# Search with filters
"Find all projects for company id 123"
"Search for projects created this month"
"Show active projects"
```

## 📂 Project Structure

```
boondmanager-multiagent/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── project_agent.py          # Standalone project agent
│   ├── tools/
│   │   ├── __init__.py
│   │   └── project_tools.py          # 7 LangChain tools
│   ├── integrations/
│   │   ├── auth.py
│   │   └── boond_client.py           # BoondManager API client
│   ├── config.py
│   └── llm_config.py
├── examples/
│   ├── README.md                     # Examples documentation
│   └── project_queries.py            # Example queries script
├── tests/
│   └── test_project_tools.py         # Unit tests for tools
├── .env                              # Configuration (not in repo)
└── PROJECT_AGENT_README.md           # This file
```

## 🧪 Testing

```bash
# Run tool unit tests
pytest tests/test_project_tools.py -v

# Run with coverage
pytest tests/test_project_tools.py --cov=src/tools --cov-report=html

# Run specific test
pytest tests/test_project_tools.py::test_search_projects_by_keywords -v
```

## 🔧 Tool Details

### search_projects

**Purpose**: Find projects using various filters

**Parameters**:
- `keywords` (str) - Search term for project name/code
- `project_types` (List[int]) - Filter by project type IDs
- `project_states` (List[int]) - Filter by state IDs
- `companies` (List[int]) - Filter by company IDs
- `start_date` (str) - Start date (YYYY-MM-DD)
- `end_date` (str) - End date (YYYY-MM-DD)
- `period_dynamic` (str) - Dynamic period (today, thisWeek, thisMonth)

**Returns**: List of matching projects with IDs, names, states, companies

### get_project_productivity

**Purpose**: Get workers and timesheet assignments for a project

**Parameters**:
- `project_id` (int) - Project unique identifier

**Returns**: Resource assignments with:
- Worker names and IDs
- Timesheet/CRA IDs
- Worked days
- Allocation details

## 🎯 Use Cases

### Use Case 1: Project ID Resolution
**Scenario**: User knows project name but not ID

**Query**: *"Fetch the project id for project alpha"*

**Agent Workflow**:
1. Calls `search_projects(keywords="alpha")`
2. Extracts project ID from response
3. Returns: *"Project Alpha has ID: 12345"*

---

### Use Case 2: Worker Lookup
**Scenario**: Find consultants assigned to a project

**Query**: *"Give me names and ids for workers associated with project id 4"*

**Agent Workflow**:
1. Calls `get_project_productivity(project_id=4)`
2. Parses resource data
3. Returns formatted list of workers with IDs

---

### Use Case 3: Multi-Step Analysis
**Scenario**: Get comprehensive project overview

**Query**: *"What's the status and workers for project Modernisation?"*

**Agent Workflow**:
1. Calls `search_projects(keywords="Modernisation")` → project_id
2. Calls `get_project_by_id(project_id)` → status
3. Calls `get_project_productivity(project_id)` → workers
4. Synthesizes response with all information

## 🔌 Extending the Agent

### Adding New Tools

1. **Define the tool** in `src/tools/project_tools.py`:

```python
@tool
async def get_project_custom_data(project_id: int) -> Dict[str, Any]:
    """Your tool description here."""
    client = BoondManagerClient()
    return await client._make_request(f"projects/{project_id}/custom")
```

2. **Export the tool** in `src/tools/__init__.py`:

```python
from src.tools.project_tools import get_project_custom_data

__all__ = [..., "get_project_custom_data"]
```

3. **Add to agent** in `src/agents/project_agent.py`:

```python
agent = async_create_deep_agent(
    tools=[
        # ... existing tools
        get_project_custom_data,
    ],
    # ...
)
```

### Adding New Endpoints to BoondManagerClient

Update `src/integrations/boond_client.py`:

```python
async def get_custom_endpoint(self, param: int) -> Dict[str, Any]:
    """Fetch custom data."""
    return await self._make_request(f"custom/{param}")
```

## 🐛 Troubleshooting

### Common Issues

**1. Authentication Errors**
```
Solution: Verify .env credentials, check token expiration
```

**2. Project Not Found**
```
Solution: Try partial keyword search, check project exists in BoondManager
```

**3. Import Errors**
```bash
# Ensure you're in project root and venv is activated
cd /path/to/boondmanager-multiagent
source .venv/bin/activate
python -m src.agents.project_agent
```

**4. Tool Execution Fails**
```
Solution: Check API permissions, network connectivity, review error messages
```

## 📊 API Response Structures

### Project Search Response
```json
{
  "data": [
    {
      "id": "12345",
      "type": "projects",
      "attributes": {
        "reference": "PRJ12345",
        "title": "Project Alpha",
        "state": {"id": 1, "value": "Active"}
      },
      "relationships": {
        "company": {"data": {"id": "123", "type": "companies"}}
      }
    }
  ]
}
```

### Productivity Response
```json
{
  "data": [
    {
      "id": "resource-id",
      "attributes": {
        "resource": {
          "id": 234,
          "firstName": "Elodie",
          "lastName": "LEGUAY"
        },
        "workedDays": 12,
        "timesReport": {"id": "timesheet-1"}
      }
    }
  ]
}
```

## 🚧 Future Enhancements

### Phase 3: Write Operations (Future)
- Add POST/PUT/DELETE endpoint support
- Implement approval workflows for modifications
- Add transaction rollback mechanisms

### Phase 4: Additional Agents
- Resource Agent (worker/consultant operations)
- Client Agent (company/contact operations)
- Timesheet Agent (CRA operations)
- Invoice Agent (billing operations)

### Phase 5: Advanced Features
- Multi-agent orchestration for complex workflows
- Caching layer for frequently accessed data
- Webhooks for real-time data updates
- Web UI for agent interaction

## 📚 Related Documentation

- [Examples Documentation](examples/README.md) - Detailed query examples
- [API Documentation](https://doc.boondmanager.com) - BoondManager API reference
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph) - Framework docs

## 🤝 Contributing

To extend this agent:

1. Add new tools in `src/tools/project_tools.py`
2. Update agent configuration in `src/agents/project_agent.py`
3. Add tests in `tests/test_project_tools.py`
4. Update documentation in examples and this README

## 📄 License

[Your License]

---

**Built with**: LangGraph, LangChain, deepagents, BoondManager API

**Status**: ✅ Production-ready for read operations | 🚧 Write operations planned
