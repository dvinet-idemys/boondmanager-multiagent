# Project Agent Examples

This directory contains example scripts demonstrating the capabilities of the BoondManager Project Agent.

## 📁 Files

- `project_queries.py` - Comprehensive examples of natural language queries

## 🚀 Quick Start

### Run Example Queries

```bash
# Make sure you're in the project root and virtual environment is activated
cd /path/to/boondmanager-multiagent
source .venv/bin/activate

# Run the example queries
python examples/project_queries.py
```

## 🎯 Query Examples

### 1. Simple Project Lookup

```python
from src.agents.project_agent import create_project_agent

agent = create_project_agent()

# Find a project by name
query = "Fetch the project id for project alpha"

async for message in agent.astream({"messages": [("user", query)]}):
    print(message)
```

**Expected Output:**
```
Project Alpha has ID: 12345
```

### 2. Worker Information

```python
# Get workers on a specific project
query = "Give me names and ids for workers associated with project id 4"

async for message in agent.astream({"messages": [("user", query)]}):
    print(message)
```

**Expected Output:**
```
Workers on project 4:
• Elodie LEGUAY (ID: 234)
• Didier GEIG (ID: 567)
```

### 3. Multi-Step Queries

```python
# Complex query requiring multiple tool calls
query = "What's the status and workers for project Modernisation?"

async for message in agent.astream({"messages": [("user", query)]}):
    print(message)
```

**Expected Output:**
```
Project Modernisation (ID: 8) is Active.

Workers:
• Elodie LEGUAY (ID: 234) - 12 days
• Didier GEIG (ID: 567) - 22 days
```

## 🛠️ Available Query Patterns

### Project Discovery
- ✅ "Find project [name]"
- ✅ "Fetch the project id for project [name]"
- ✅ "Search for projects with keyword '[keyword]'"
- ✅ "Find all projects for company id [id]"

### Worker/Resource Queries
- ✅ "Who is working on project [name/id]?"
- ✅ "Give me workers associated with project [id]"
- ✅ "Get resource assignments for project [id]"
- ✅ "Show me consultants on project [name]"

### Project Details
- ✅ "Get details for project [id]"
- ✅ "What's the status of project [name/id]?"
- ✅ "Get all information for project [id]"

### Orders & Tasks
- ✅ "What are the orders for project [id]?"
- ✅ "Show me tasks in project [id]"
- ✅ "Get billing orders for project [name]"

### Multi-Step Combinations
- ✅ "Find project [name] and tell me who works on it"
- ✅ "What's the status and workers for project [name]?"
- ✅ "Get the project id for [name] and show me its tasks"

## 🔧 Customizing Queries

### Create Your Own Script

```python
import asyncio
from src.agents.project_agent import create_project_agent

async def my_custom_query():
    agent = create_project_agent()

    queries = [
        "Your custom query here",
        "Another query",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        async for message in agent.astream({"messages": [("user", query)]}):
            if "messages" in message:
                for msg in message["messages"]:
                    if hasattr(msg, "content") and msg.content:
                        print(f"Response: {msg.content}")

if __name__ == "__main__":
    asyncio.run(my_custom_query())
```

## 📊 Understanding Agent Responses

The agent returns structured data that includes:

### Project Data Structure
```json
{
  "data": [
    {
      "id": "12345",
      "type": "projects",
      "attributes": {
        "reference": "PRJ12345",
        "title": "Project Alpha",
        "state": {
          "id": 1,
          "value": "Active"
        }
      },
      "relationships": {
        "company": {
          "data": {
            "id": "123",
            "type": "companies"
          }
        }
      }
    }
  ]
}
```

### Productivity/Worker Data Structure
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
        "timesReport": {
          "id": "timesheet-id"
        }
      }
    }
  ]
}
```

## 🐛 Troubleshooting

### Agent doesn't find the project
- Check if the project name is spelled correctly
- Try using partial keywords: "alpha" instead of "Project Alpha"
- Verify the project exists in BoondManager

### API authentication errors
- Ensure `.env` file has valid credentials:
  ```
  BOOND_USER_TOKEN=your_token
  BOOND_CLIENT_TOKEN=your_client_token
  BOOND_CLIENT_KEY=your_key
  ```

### Tool execution fails
- Check network connectivity
- Verify API permissions for your credentials
- Review error messages in agent output

## 🔗 Related Files

- `src/tools/project_tools.py` - Tool implementations
- `src/agents/project_agent.py` - Agent configuration
- `src/integrations/boond_client.py` - API client

## 📚 Next Steps

1. **Extend Tools**: Add more endpoint wrappers to `src/tools/project_tools.py`
2. **Create Specialized Agents**: Build agents for resources, timesheets, invoices
3. **Add Validation**: Implement response validation and error handling
4. **Build UI**: Create a web interface or CLI for the agent
