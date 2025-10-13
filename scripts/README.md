# API Exploration Scripts

Utilities for exploring and documenting the BoondManager API.

## 📁 Files

- **`explore_api.py`** - Comprehensive API exploration and documentation tool

## 🚀 Quick Start

### Explore All Endpoints

```bash
# Basic exploration (view only)
python scripts/explore_api.py

# Save all responses to JSON files
python scripts/explore_api.py --save

# Use specific project ID
python scripts/explore_api.py --project-id 8 --save
```

### Explore Specific Endpoints

```bash
# Explore projects search
python scripts/explore_api.py --endpoint projects --save

# Explore project productivity (requires project ID)
python scripts/explore_api.py --endpoint productivity --project-id 8 --save

# Explore with search keywords
python scripts/explore_api.py --endpoint projects --keywords "modernisation" --save

# Explore contacts
python scripts/explore_api.py --endpoint contacts --save
```

## 📊 What It Does

The exploration script:

1. **Calls Real API Endpoints** - Makes actual requests to BoondManager
2. **Shows Response Structure** - Displays the JSON structure hierarchically
3. **Extracts Key Fields** - Highlights important data fields
4. **Saves Responses** (optional) - Saves full JSON responses to `docs/api_responses/`
5. **Documents Patterns** - Helps understand API response formats

## 🎯 Use Cases

### 1. Update Tool Documentation

After running the exploration, use the responses to improve tool docstrings:

```python
# Before (generic)
@tool
async def get_project_productivity(project_id: int) -> Dict[str, Any]:
    """Get productivity data for a project."""

# After (specific based on real API response)
@tool
async def get_project_productivity(project_id: int) -> Dict[str, Any]:
    """Get productivity data for a project.

    Returns:
        Dictionary with structure:
        {
            "data": [
                {
                    "id": "productivity-id",
                    "type": "productivity",
                    "attributes": {
                        "resource": {
                            "id": 234,
                            "firstName": "John",
                            "lastName": "Doe"
                        },
                        "workedDays": 12.5,
                        "timesReport": {"id": "timesheet-123"}
                    }
                }
            ]
        }
    """
```

### 2. Create Response Examples

Use saved JSON files to create realistic test fixtures:

```python
# tests/fixtures/project_productivity.json
{
  "data": [
    {
      "id": "prod-1",
      "attributes": {
        "resource": {
          "id": 234,
          "firstName": "Elodie",
          "lastName": "LEGUAY"
        },
        "workedDays": 12
      }
    }
  ]
}
```

### 3. Validate Agent Behavior

Compare agent parsing logic against real API responses:

```bash
# Get real response
python scripts/explore_api.py --endpoint productivity --project-id 8 --save

# Then test agent
python -m src.agents.project_agent

# Compare: Does agent parse the same fields correctly?
```

### 4. Discover New Fields

Find additional fields not yet exposed in tools:

```bash
python scripts/explore_api.py --endpoint information --project-id 8

# Output might reveal:
# • customFields
# • metadata
# • additionalAttributes
# → Add these to tool descriptions!
```

## 📋 Output Examples

### Console Output

```
🚀 ================================================================ 🚀
     BOONDMANAGER API EXPLORATION - COMPREHENSIVE SCAN
🚀 ================================================================ 🚀

======================================================================
🔍 Exploring: GET /projects (Search Projects)
======================================================================

   ✅ Success! Found 25 projects

   📊 Response Structure:
      📦 data:
         📋 Array with 25 items
            Sample item [0]:
               • id (str): 12345
               • type (str): projects
               📦 attributes:
                  • title (str): Project Alpha
                  • reference (str): PRJ12345
                  📦 state:
                     • id (int): 1
                     • value (str): Active

   🎯 Sample Project (first result):
      ID: 12345
      Title: Project Alpha
      Reference: PRJ12345
      State: {'id': 1, 'value': 'Active'}

   💾 Saved response to: docs/api_responses/projects_search_20251010_143022.json
```

### Saved JSON Files

Files are saved to `docs/api_responses/` with timestamps:

```
docs/api_responses/
├── projects_search_20251010_143022.json
├── project_12345_profile_20251010_143023.json
├── project_12345_productivity_20251010_143024.json
├── project_12345_information_20251010_143025.json
├── project_12345_orders_20251010_143026.json
├── project_12345_tasks_20251010_143027.json
├── project_12345_rights_20251010_143028.json
└── contacts_20251010_143029.json
```

## 🔧 Available Options

```
usage: explore_api.py [-h]
                     [--endpoint {all,projects,productivity,information,orders,tasks,rights,contacts}]
                     [--project-id PROJECT_ID]
                     [--save]
                     [--keywords KEYWORDS]

Explore BoondManager API endpoints and document response structures

optional arguments:
  -h, --help            show this help message and exit
  --endpoint {all,projects,productivity,information,orders,tasks,rights,contacts}
                        Specific endpoint to explore (default: all)
  --project-id PROJECT_ID
                        Specific project ID to use for exploration
  --save                Save API responses to JSON files in docs/api_responses/
  --keywords KEYWORDS   Keywords to search for when exploring projects
```

## 📚 Endpoints Explored

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/projects` | GET | Search all projects with filters |
| `/projects/{id}` | GET | Get project profile by ID |
| `/projects/{id}/productivity` | GET | Get resource assignments & timesheets |
| `/projects/{id}/information` | GET | Get detailed project information |
| `/projects/{id}/orders` | GET | Get project orders |
| `/projects/{id}/tasks` | GET | Get project tasks |
| `/projects/{id}/rights` | GET | Get project access rights |
| `/contacts` | GET | Get all contacts |

## 🎨 Output Format

The script provides a structured view of API responses:

1. **Response Structure** - Tree view of JSON structure
2. **Key Fields** - Highlighted important fields
3. **Sample Data** - Preview of actual values
4. **Type Information** - Data types for each field
5. **Array Counts** - Number of items in lists

## 💡 Tips

### Finding a Project ID

```bash
# Search for a specific project first
python scripts/explore_api.py --endpoint projects --keywords "alpha"

# Note the ID from output, then explore that project
python scripts/explore_api.py --project-id 12345 --save
```

### Comparing Endpoints

```bash
# Get profile
python scripts/explore_api.py --endpoint projects --project-id 8

# Get detailed information
python scripts/explore_api.py --endpoint information --project-id 8

# Compare: What's different between profile and information?
```

### Discovering Relationships

```bash
# Get project → note company ID in relationships
python scripts/explore_api.py --endpoint projects --project-id 8

# Then could explore that company's projects
python scripts/explore_api.py --endpoint projects --keywords "company-name"
```

## 🔍 Understanding the Output

### Structure Symbols

- 📦 `dict` - Dictionary/object
- 📋 `Array` - List/array
- • `field` - Simple value (string, number, boolean)

### Example Reading

```
📦 data:
   📋 Array with 2 items
      Sample item [0]:
         • id (str): 234
         📦 attributes:
            • firstName (str): Elodie
            • lastName (str): LEGUAY
```

**Interpretation**:
- `data` is a dictionary containing an array
- Array has 2 items
- Each item has an `id` field (string)
- Each item has an `attributes` object
- `attributes` contains `firstName` and `lastName` strings

## 🚧 Troubleshooting

### Authentication Errors

```bash
# Verify .env credentials
cat .env | grep BOOND

# Test basic API access
python -c "from src.integrations.boond_client import BoondManagerClient; import asyncio; asyncio.run(BoondManagerClient().get_projects())"
```

### Project Not Found

```bash
# Search first to find valid IDs
python scripts/explore_api.py --endpoint projects --save

# Look at saved JSON for valid project IDs
cat docs/api_responses/projects_search_*.json | grep '"id"'
```

### Permission Errors

Some endpoints may require specific permissions. If you get 403 errors:
- Check your API token permissions
- Try different project IDs
- Verify you have access to those resources

## 📝 Next Steps

After running exploration:

1. **Review saved JSON files** in `docs/api_responses/`
2. **Update tool docstrings** with real response structures
3. **Create test fixtures** from real responses
4. **Document new fields** discovered in responses
5. **Improve agent prompts** with field-specific examples

## 🔗 Related Files

- `src/tools/project_tools.py` - Tools to update with discoveries
- `tests/test_project_tools.py` - Tests to improve with real data
- `src/agents/project_agent.py` - Agent to enhance with examples
