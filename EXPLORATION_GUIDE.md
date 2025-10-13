# API Exploration & Documentation Guide

**Purpose**: Use the exploration script to generate accurate documentation for your BoondManager API tools.

---

## 🎯 Quick Commands

### Explore Everything
```bash
# See all endpoints with sample data
python scripts/explore_api.py

# Save all responses for documentation
python scripts/explore_api.py --save
```

### Explore Specific Project
```bash
# Use a known project ID
python scripts/explore_api.py --project-id 8 --save

# Or search first, then explore
python scripts/explore_api.py --endpoint projects --keywords "modernisation"
# → Note the project ID from output
python scripts/explore_api.py --project-id <ID> --save
```

### Focus on Key Endpoint
```bash
# Just productivity data (workers/timesheets)
python scripts/explore_api.py --endpoint productivity --project-id 8 --save
```

---

## 📋 Workflow: Improve Tool Documentation

### Step 1: Run Exploration

```bash
python scripts/explore_api.py --save
```

**Output**: JSON files in `docs/api_responses/`

### Step 2: Review Response Structure

```bash
# Look at productivity endpoint (your main use case)
cat docs/api_responses/project_*_productivity_*.json | jq '.'
```

### Step 3: Update Tool Docstrings

**Before** (generic):
```python
@tool
async def get_project_productivity(project_id: int) -> Dict[str, Any]:
    """Get productivity data for a project."""
```

**After** (with real structure):
```python
@tool
async def get_project_productivity(project_id: int) -> Dict[str, Any]:
    """Get productivity data for a project including workers and timesheets.

    Args:
        project_id: The unique project identifier

    Returns:
        Dictionary with structure:
        {
            "data": [
                {
                    "id": "productivity-record-id",
                    "type": "productivity",
                    "attributes": {
                        "resource": {
                            "id": 234,                    # Worker ID
                            "firstName": "Elodie",
                            "lastName": "LEGUAY",
                            "reference": "RES234"
                        },
                        "workedDays": 12.5,               # Days worked
                        "cost": 7860.0,                   # Total cost
                        "timesReport": {
                            "id": "TR-12345"              # Timesheet/CRA ID
                        },
                        "project": {
                            "id": 8,
                            "title": "Project Name"
                        }
                    }
                }
            ]
        }

    Example:
        >>> result = await get_project_productivity(project_id=8)
        >>> workers = result["data"]
        >>> for worker in workers:
        ...     resource = worker["attributes"]["resource"]
        ...     print(f"{resource['firstName']} {resource['lastName']}: {worker['attributes']['workedDays']} days")
        Elodie LEGUAY: 12.5 days
        Didier GEIG: 22.0 days
    """
```

### Step 4: Create Test Fixtures

```bash
# Create fixture from real response
mkdir -p tests/fixtures
cp docs/api_responses/project_8_productivity_*.json tests/fixtures/productivity_sample.json
```

Use in tests:
```python
import json
from pathlib import Path

def load_fixture(name: str) -> dict:
    """Load test fixture."""
    path = Path(__file__).parent / "fixtures" / f"{name}.json"
    return json.loads(path.read_text())

@pytest.mark.asyncio
async def test_parse_real_productivity_data():
    """Test parsing with real API response structure."""
    real_response = load_fixture("productivity_sample")

    # Test your parsing logic
    workers = real_response["data"]
    assert len(workers) == 2
    assert workers[0]["attributes"]["resource"]["firstName"] == "Elodie"
```

---

## 🔍 Understanding Real Response Structures

### Example: Productivity Endpoint

**Exploration Output**:
```
======================================================================
🔍 Exploring: GET /projects/8/productivity
======================================================================

   ✅ Success! Found 2 productivity records

   📊 Response Structure:
      📦 data:
         📋 Array with 2 items
            Sample item [0]:
               • id (str): prod-1
               • type (str): productivity
               📦 attributes:
                  📦 resource:
                     • id (int): 234
                     • firstName (str): Elodie
                     • lastName (str): LEGUAY
                  • workedDays (float): 12.5
                  📦 timesReport:
                     • id (str): TR-12345

   👥 Resource Details:

      Resource 1:
         ID: 234
         Name: Elodie LEGUAY
         Worked Days: 12.5
         Timesheet ID: TR-12345

      Resource 2:
         ID: 567
         Name: Didier GEIG
         Worked Days: 22.0
         Timesheet ID: TR-67890
```

**What This Tells You**:

1. **Data Structure**:
   - Response has `data` array
   - Each item is a productivity record
   - Not a single object, but an array (even for one project)

2. **Worker Information**:
   - Located in `attributes.resource`
   - Has `id`, `firstName`, `lastName`
   - The resource ID (234) is the **worker ID** you need!

3. **Timesheet Connection**:
   - Located in `attributes.timesReport.id`
   - This is the CRA/timesheet ID

4. **Agent Parsing Logic**:
   ```python
   # Correct way to parse
   for record in response["data"]:
       worker_id = record["attributes"]["resource"]["id"]
       worker_name = f"{record['attributes']['resource']['firstName']} {record['attributes']['resource']['lastName']}"
       timesheet_id = record["attributes"]["timesReport"]["id"]
       worked_days = record["attributes"]["workedDays"]
   ```

---

## 📊 Key Endpoints for Your Use Cases

### 1. Find Project by Name → Get ID

**Query**: *"Fetch the project id for project alpha"*

**Endpoint**: `GET /projects?keywords=alpha`

**Exploration**:
```bash
python scripts/explore_api.py --endpoint projects --keywords "alpha" --save
```

**Key Fields in Response**:
```json
{
  "data": [
    {
      "id": "12345",          ← This is the project ID you need!
      "type": "projects",
      "attributes": {
        "title": "Project Alpha",
        "reference": "PRJ12345"
      }
    }
  ]
}
```

---

### 2. Find Workers on Project

**Query**: *"Give me names and ids for workers associated with project id 4"*

**Endpoint**: `GET /projects/4/productivity`

**Exploration**:
```bash
python scripts/explore_api.py --endpoint productivity --project-id 4 --save
```

**Key Fields in Response**:
```json
{
  "data": [
    {
      "attributes": {
        "resource": {
          "id": 234,           ← Worker ID
          "firstName": "Elodie",
          "lastName": "LEGUAY"  ← Worker names
        },
        "workedDays": 12.5,
        "timesReport": {
          "id": "TR-123"       ← Timesheet ID
        }
      }
    }
  ]
}
```

---

## 🎯 Common Documentation Improvements

### 1. Response Structure Examples

**Add to every tool docstring**:
```python
Returns:
    Dictionary with structure:
    {
        "data": [...],      # Always an array, even for single results
        "meta": {...}       # Pagination info (if applicable)
    }
```

### 2. Field Type Documentation

```python
Args:
    project_id (int): Numeric project identifier (e.g., 8, not "8")
    keywords (str): Search term, case-insensitive (e.g., "alpha", "ALPHA")
```

### 3. Relationship Documentation

```python
Note:
    - Project has one-to-many relationship with productivity records
    - Each productivity record links to one resource (worker)
    - Each resource may have multiple productivity records across projects
```

### 4. Example Queries

```python
Example queries this tool handles:
    - "Get workers on project 4" → get_project_productivity(project_id=4)
    - "Who works on project Alpha?" →
        1. search_projects(keywords="Alpha") → project_id
        2. get_project_productivity(project_id=project_id)
```

---

## 🐛 Troubleshooting

### "Module not found" errors

```bash
# Ensure you're in project root
cd /path/to/boondmanager-multiagent

# Activate venv
source .venv/bin/activate

# Run with python -m
python -m scripts.explore_api --save
```

### Empty responses

```bash
# Check if you have access
python scripts/explore_api.py --endpoint projects

# If no results, check API credentials
cat .env | grep BOOND_
```

### 403 Permission errors

- Some endpoints require specific permissions
- Try different project IDs
- Verify your API token has read access

---

## ✅ Checklist: Documentation Improvement

After running exploration:

- [ ] Run exploration script: `python scripts/explore_api.py --save`
- [ ] Review saved JSON files in `docs/api_responses/`
- [ ] Update tool docstrings with real response structures
- [ ] Add example parsing code to docstrings
- [ ] Create test fixtures from real responses
- [ ] Update agent prompt with field-specific examples
- [ ] Test agent with real queries
- [ ] Verify agent correctly parses discovered fields

---

## 🚀 Ready to Use!

```bash
# 1. Explore API
python scripts/explore_api.py --save

# 2. Review responses
ls docs/api_responses/

# 3. Update documentation based on real data

# 4. Test improvements
python -m src.agents.project_agent
```

---

**Next**: Check `scripts/README.md` for detailed exploration options and output examples.
