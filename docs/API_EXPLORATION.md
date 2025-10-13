# BoondManager API Exploration Results

**Purpose**: Document the actual response structures from BoondManager API to improve tool accuracy.

**Status**: Ready to use - Run `python scripts/explore_api.py --save` to populate this with real data

---

## 📖 How to Use This Document

1. **Run the exploration script** to fetch real API responses
2. **Review the JSON files** saved to `docs/api_responses/`
3. **Update this document** with your findings
4. **Improve tool docstrings** based on real response structures

---

## 🔍 Endpoints Explored

### 1. Search Projects - `GET /projects`

**Tool**: `search_projects`

**Test Command**:
```bash
python scripts/explore_api.py --endpoint projects --save
```

**Response Structure** (to be filled after exploration):
```json
{
  "data": [
    {
      "id": "...",
      "type": "projects",
      "attributes": {
        "title": "...",
        "reference": "...",
        "state": {...}
      },
      "relationships": {
        "company": {...}
      }
    }
  ]
}
```

**Key Fields**:
- `data[].id` - Project ID (string or int?)
- `data[].attributes.title` - Project name
- `data[].attributes.reference` - Project reference code
- `data[].attributes.state` - Project state object
- `data[].relationships.company.data.id` - Associated company ID

**Notes**:
- Add your observations here after running exploration
- Note any unexpected fields
- Document field types and formats

---

### 2. Project Profile - `GET /projects/{id}`

**Tool**: `get_project_by_id`

**Test Command**:
```bash
python scripts/explore_api.py --endpoint projects --project-id 8 --save
```

**Response Structure**:
```json
{
  "data": {
    "id": "...",
    "type": "projects",
    "attributes": {
      // Fill in after exploration
    }
  }
}
```

**Key Fields**:
- To be documented after exploration

**Differences from Search Response**:
- Note any additional fields present in profile vs search

---

### 3. Project Productivity - `GET /projects/{id}/productivity`

**Tool**: `get_project_productivity`

**Test Command**:
```bash
python scripts/explore_api.py --endpoint productivity --project-id 8 --save
```

**Response Structure**:
```json
{
  "data": [
    {
      "id": "...",
      "type": "productivity",
      "attributes": {
        "resource": {
          "id": 0,
          "firstName": "...",
          "lastName": "...",
          "reference": "..."
        },
        "workedDays": 0.0,
        "cost": 0.0,
        "timesReport": {
          "id": "..."
        }
      }
    }
  ]
}
```

**Key Fields** (Critical for worker queries):
- `data[].attributes.resource.id` - **Worker ID**
- `data[].attributes.resource.firstName` - Worker first name
- `data[].attributes.resource.lastName` - Worker last name
- `data[].attributes.workedDays` - Days worked on project
- `data[].attributes.timesReport.id` - **Timesheet/CRA ID**
- `data[].attributes.cost` - Total cost (if available)

**Important Notes**:
- This is the primary endpoint for "who works on project X?" queries
- Returns array of productivity records, one per worker
- Each record links worker ID to timesheet ID

---

### 4. Project Information - `GET /projects/{id}/information`

**Tool**: `get_project_information`

**Test Command**:
```bash
python scripts/explore_api.py --endpoint information --project-id 8 --save
```

**Response Structure**:
```json
{
  "data": {
    // Fill in after exploration
  }
}
```

**Key Fields**:
- To be documented

**Differences from Profile**:
- Note what additional information is provided here

---

### 5. Project Orders - `GET /projects/{id}/orders`

**Tool**: `get_project_orders`

**Test Command**:
```bash
python scripts/explore_api.py --endpoint orders --project-id 8 --save
```

**Response Structure**:
```json
{
  "data": [
    {
      // Fill in after exploration
    }
  ]
}
```

**Key Fields**:
- Order reference
- Order state
- Start/end dates
- Turnover amounts

---

### 6. Project Tasks - `GET /projects/{id}/tasks`

**Tool**: `get_project_tasks`

**Test Command**:
```bash
python scripts/explore_api.py --endpoint tasks --project-id 8 --save
```

**Response Structure**:
```json
{
  "data": [
    {
      // Fill in after exploration
    }
  ]
}
```

---

### 7. Project Rights - `GET /projects/{id}/rights`

**Tool**: `get_project_rights`

**Test Command**:
```bash
python scripts/explore_api.py --endpoint rights --project-id 8 --save
```

**Response Structure**:
```json
{
  "data": {
    // Fill in after exploration
  }
}
```

---

### 8. Contacts - `GET /contacts`

**Tool**: Used by search_projects for company filtering

**Test Command**:
```bash
python scripts/explore_api.py --endpoint contacts --save
```

**Response Structure**:
```json
{
  "data": [
    {
      // Fill in after exploration
    }
  ]
}
```

---

## 🎯 Critical Insights for Tool Development

### Response Pattern: Array vs Object

**Pattern Observed**:
- Search endpoints → Return `data` as **array** (even if 1 result)
- Profile endpoints → Return `data` as **object** (single item)
- Sub-resource endpoints → Return `data` as **array** (multiple items)

**Implication for Agent**:
```python
# Correct parsing for search/list endpoints
for item in response["data"]:
    process(item)

# Correct parsing for profile endpoints
item = response["data"]
process(item)
```

### Field Type Consistency

**Observations** (to be filled):
- IDs: string or int?
- Dates: ISO format? (YYYY-MM-DD)
- Amounts: float or decimal?
- States: object with id/value or just string?

### Relationship Structures

**Pattern** (JSON:API format?):
```json
{
  "relationships": {
    "company": {
      "data": {
        "id": "123",
        "type": "companies"
      }
    }
  }
}
```

### Pagination

**Check for**:
- `meta.pagination` fields?
- `links.next` for cursor pagination?
- Query params: `page`, `limit`, `offset`?

---

## 📝 Documentation Updates Needed

### Priority 1: Update Tool Docstrings

After exploration, update these tools with real response examples:

1. **`search_projects`** - Add real response structure
2. **`get_project_productivity`** - **CRITICAL** - Document worker/timesheet structure
3. **`get_project_by_id`** - Add profile structure

### Priority 2: Create Test Fixtures

Create fixtures from real responses:
- `tests/fixtures/projects_search.json`
- `tests/fixtures/project_productivity.json`
- `tests/fixtures/project_profile.json`

### Priority 3: Update Agent Prompt

Add field-specific parsing examples to agent system prompt:
```python
# Example: Parsing workers from productivity endpoint
workers = []
for record in response["data"]:
    resource = record["attributes"]["resource"]
    workers.append({
        "id": resource["id"],
        "name": f"{resource['firstName']} {resource['lastName']}",
        "days": record["attributes"]["workedDays"],
        "timesheet_id": record["attributes"]["timesReport"]["id"]
    })
```

---

## 🔄 Continuous Improvement Process

1. **Explore** → Run exploration script
2. **Document** → Fill in this document with findings
3. **Update** → Improve tool docstrings
4. **Test** → Verify agent parses correctly
5. **Iterate** → Repeat as API evolves

---

## 📁 Related Files

- **Exploration Script**: `scripts/explore_api.py`
- **Saved Responses**: `docs/api_responses/` (after running exploration)
- **Tool Definitions**: `src/tools/project_tools.py`
- **Agent Configuration**: `src/agents/project_agent.py`
- **Test Suite**: `tests/test_project_tools.py`

---

## 🚀 Next Steps

1. **Run exploration**: `python scripts/explore_api.py --save`
2. **Review JSON files**: `ls docs/api_responses/`
3. **Fill in this document** with your observations
4. **Update tool docstrings** in `src/tools/project_tools.py`
5. **Test with real queries** using `python -m src.agents.project_agent`

---

**Last Updated**: Ready for first exploration run
**Status**: Template - Run exploration to populate with real data
