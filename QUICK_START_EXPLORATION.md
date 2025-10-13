# 🚀 Quick Start: API Exploration

**Goal**: Generate accurate documentation for your BoondManager API tools in 5 minutes.

---

## ⚡ One-Command Exploration

```bash
python scripts/explore_api.py --save
```

**This will**:
- ✅ Call all BoondManager API endpoints
- ✅ Display response structures in your terminal
- ✅ Save JSON responses to `docs/api_responses/`
- ✅ Show you exactly what data is available

---

## 📊 What You'll See

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

   🎯 Sample Project (first result):
      ID: 12345
      Title: Project Alpha
      Reference: PRJ12345

   💾 Saved response to: docs/api_responses/projects_search_20251010_143022.json

======================================================================
🔍 Exploring: GET /projects/12345/productivity
======================================================================

   ✅ Success! Found 2 productivity records

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

   💾 Saved response to: docs/api_responses/project_12345_productivity_20251010_143023.json

[... continues for all endpoints ...]

======================================================================
✅ EXPLORATION COMPLETE!
======================================================================

📁 All responses saved to: /path/to/docs/api_responses
   Use these responses to improve tool documentation!
```

---

## 📁 What Gets Created

After running exploration, you'll have:

```
docs/api_responses/
├── projects_search_20251010_143022.json          ← All projects
├── project_12345_profile_20251010_143023.json    ← Project details
├── project_12345_productivity_20251010_143024.json  ← Workers! ⭐
├── project_12345_information_20251010_143025.json
├── project_12345_orders_20251010_143026.json
├── project_12345_tasks_20251010_143027.json
├── project_12345_rights_20251010_143028.json
└── contacts_20251010_143029.json
```

---

## 🎯 Use the Results

### 1. See Worker Data Structure

```bash
# Look at productivity response (your main use case!)
cat docs/api_responses/project_*_productivity_*.json | jq '.data[0].attributes.resource'
```

**Expected output**:
```json
{
  "id": 234,
  "firstName": "Elodie",
  "lastName": "LEGUAY",
  "reference": "RES234"
}
```

Now you know:
- Worker ID is at `data[].attributes.resource.id`
- Names are at `data[].attributes.resource.firstName/lastName`
- Timesheet ID is at `data[].attributes.timesReport.id`

### 2. Update Tool Docstring

Edit `src/tools/project_tools.py`:

```python
@tool
async def get_project_productivity(project_id: int) -> Dict[str, Any]:
    """Get productivity data for a project including workers and timesheets.

    Returns:
        Dictionary with structure:
        {
            "data": [
                {
                    "attributes": {
                        "resource": {
                            "id": 234,              ← Worker ID here!
                            "firstName": "Elodie",
                            "lastName": "LEGUAY"
                        },
                        "workedDays": 12.5,
                        "timesReport": {
                            "id": "TR-123"          ← Timesheet ID here!
                        }
                    }
                }
            ]
        }
    """
```

### 3. Test Your Agent

```bash
python -m src.agents.project_agent
```

Now your agent knows exactly where to find worker IDs and names!

---

## 🔧 Advanced Options

### Explore Specific Project

```bash
# If you know a project ID
python scripts/explore_api.py --project-id 8 --save
```

### Search for Project First

```bash
# Find project ID by name
python scripts/explore_api.py --endpoint projects --keywords "modernisation"

# Output shows: Project ID: 8

# Then explore that project
python scripts/explore_api.py --project-id 8 --save
```

### Just View (Don't Save)

```bash
# Quick look without saving files
python scripts/explore_api.py
```

---

## ✅ Success Checklist

After running exploration:

- [ ] ✅ Script completed without errors
- [ ] ✅ JSON files created in `docs/api_responses/`
- [ ] ✅ Reviewed `project_*_productivity_*.json` (your key use case)
- [ ] ✅ Noted structure of worker IDs and timesheet IDs
- [ ] ✅ Updated tool docstrings with real field paths
- [ ] ✅ Tested agent with queries like "Who works on project 8?"

---

## 🎓 Learn from the Output

The exploration shows you:

1. **Exact field names** - No more guessing `user_id` vs `userId` vs `id`
2. **Data types** - Is ID a string or int? Are amounts floats or decimals?
3. **Nesting structure** - How deep are fields nested?
4. **Array vs Object** - Is `data` an array or single object?
5. **Available fields** - What fields exist that you haven't used yet?

---

## 🐛 Troubleshooting

### Script fails immediately

```bash
# Check you're in project root
pwd
# Should be: /path/to/boondmanager-multiagent

# Activate venv
source .venv/bin/activate
```

### Authentication errors

```bash
# Verify .env exists and has credentials
cat .env | grep BOOND_
```

### No projects found

```bash
# Your API token might not have access
# Try checking with curl
curl -H "X-Jwt-Client-BoondManager: YOUR_TOKEN" https://ui.boondmanager.com/api/projects
```

---

## 🚀 Ready!

```bash
# One command to document everything
python scripts/explore_api.py --save

# Then use the JSON files to improve your tool documentation
# The agent will be more accurate with real response structures!
```

---

**Next Steps**:
1. ✅ Run exploration: `python scripts/explore_api.py --save`
2. 📖 Review: Check `docs/api_responses/*.json`
3. ✏️ Update: Improve tool docstrings with real structures
4. 🧪 Test: Verify agent handles real data correctly

**Documentation**: See `EXPLORATION_GUIDE.md` for detailed workflows
