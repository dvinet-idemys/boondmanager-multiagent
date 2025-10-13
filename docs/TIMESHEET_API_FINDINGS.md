# BoondManager Timesheet API - Findings

**Date**: 2025-10-10
**Scope**: Timesheet/Timesreport endpoints
**Status**: ✅ Complete with real data

---

## 🎯 Essential Endpoints

This documentation covers the **2 core endpoints** for timesheet queries:

1. **`GET /resources/{id}/timesreports`** - Get all timesheets for a worker
2. **`GET /timesreports/{id}`** - Get detailed timesheet with daily entries

---

## ⚠️ CRITICAL: Timesheet Structure

### The Most Important Discovery

**Daily time entries are in `data.attributes.regularTimes[]`, NOT in `data[]`!**

The timesheet detail endpoint uses a nested structure:
- `data` contains a **single object** (not array) with timesheet metadata
- `data.attributes.regularTimes[]` contains **daily time entries**
- `included[]` contains **related entities** (workers, projects, orders)

### Visual Structure

```
Timesheet Detail Response
│
├─ data ← Single timesheet object
│   ├─ attributes.term = "2025-09" ← Period (YYYY-MM)
│   ├─ attributes.state = "validated" ← Validation state
│   ├─ attributes.regularTimes[] ← Daily time entries HERE!
│   │   └─ [{startDate, duration, project, delivery}, ...]
│   ├─ attributes.exceptionalTimes[] ← Overtime entries
│   └─ attributes.absencesTimes[] ← Absence entries
│
├─ relationships
│   ├─ resource.data.id = "28" ← Worker ID
│   ├─ projects.data[] ← All projects in this timesheet
│   └─ orders.data[] ← Related orders
│
└─ included[] ← Related entities (workers, projects, orders)
    └─ [worker details, project details, order details]
```

---

## 📊 Endpoint 1: Get Worker Timesheets

### `GET /resources/{id}/timesreports`

**Purpose**: Get all timesheets for a specific worker/resource

**Real Response Structure**:
```json
{
  "meta": {
    "totals": {
      "rows": 1
    },
    "version": "9.0.5.3"
  },
  "data": [
    {
      "id": "5",
      "type": "timesreport",
      "attributes": {
        "term": "2025-09",
        "creationDate": "2025-09-24T15:33:48+0200",
        "updateDate": "2025-09-24T15:34:46+0200",
        "closed": false,
        "state": "validated"
      },
      "relationships": {
        "resource": {
          "data": {"id": "28", "type": "resource"}
        },
        "projects": {
          "data": [
            {"id": "8", "type": "project"}
          ]
        }
      }
    }
  ]
}
```

### Key Fields

| Field Path | Type | Example | Notes |
|------------|------|---------|-------|
| **Timesheet Identification** ||||
| `data[].id` | string | `"5"` | Timesheet ID |
| `data[].attributes.term` | string | `"2025-09"` | Period (YYYY-MM format) |
| **Status** ||||
| `data[].attributes.state` | string | `"validated"` | State: validated/pending/rejected |
| `data[].attributes.closed` | boolean | `false` | Is timesheet locked? |
| **Dates** ||||
| `data[].attributes.creationDate` | string | `"2025-09-24T15:33:48+0200"` | Created timestamp |
| `data[].attributes.updateDate` | string | `"2025-09-24T15:34:46+0200"` | Last updated |
| **Relationships** ||||
| `data[].relationships.resource.data.id` | string | `"28"` | Worker/resource ID |
| `data[].relationships.projects.data[]` | array | `[{"id": "8"}]` | Projects in timesheet |

### Important Notes

1. ✅ **Multiple timesheets**: One per month/period per worker
2. ✅ **State values**: "validated", "pending", "rejected"
3. ✅ **Closed timesheets**: Cannot be modified when closed=true
4. ⚠️ **Term format**: Always YYYY-MM (e.g., "2025-09" for September 2025)

### Query Example

**User Query**: *"Get all timesheets for worker 28"*

**API Call**: `GET /resources/28/timesreports`

**Parse**:
```python
timesheets = response["data"]
for ts in timesheets:
    ts_id = ts["id"]                    # "5"
    period = ts["attributes"]["term"]    # "2025-09"
    state = ts["attributes"]["state"]    # "validated"
    print(f"Timesheet {ts_id} for {period}: {state}")
```

---

## ⭐ Endpoint 2: Get Timesheet Details (CRITICAL)

### `GET /timesreports/{id}`

**Purpose**: Get detailed timesheet with daily time entries

**This is THE endpoint for**: *"What did worker X do each day?"* queries

### Real Response Structure (Simplified)

```json
{
  "meta": {
    "expectedValidatorsAllowedForValidate": [],
    "expectedValidatorsAllowedForUnValidate": [
      {"id": "2", "firstName": "Dimitri", "lastName": "VINET"}
    ]
  },
  "data": {
    "id": "5",
    "type": "timesreport",
    "attributes": {
      "term": "2025-09",
      "state": "validated",
      "closed": false,
      "workUnitRate": 1,
      "regularTimes": [
        {
          "id": "75",
          "calendar": "calendar",
          "startDate": "2025-09-15",
          "duration": 1,
          "row": 6,
          "workUnitType": {
            "reference": 1,
            "activityType": "production",
            "name": "Normale"
          },
          "delivery": {
            "id": "18",
            "title": "",
            "startDate": "2025-09-15",
            "endDate": "2025-12-31"
          },
          "project": {
            "id": "8",
            "reference": "Modernisation Ligne Production - Multi commande"
          },
          "batch": null
        },
        {
          "id": "87",
          "startDate": "2025-09-01",
          "duration": 1,
          "workUnitType": {
            "reference": 9,
            "activityType": "internal",
            "name": "Intercontrat"
          },
          "delivery": null,
          "project": null,
          "batch": null
        }
      ],
      "exceptionalTimes": [],
      "absencesTimes": []
    },
    "relationships": {
      "resource": {
        "data": {"id": "28", "type": "resource"}
      },
      "projects": {
        "data": [{"id": "8", "type": "project"}]
      },
      "orders": {
        "data": [{"id": "11", "type": "order"}]
      }
    }
  },
  "included": [
    {
      "id": "28",
      "type": "resource",
      "attributes": {
        "firstName": "Elodie",
        "lastName": "Leguay"
      }
    },
    {
      "id": "8",
      "type": "project",
      "attributes": {
        "reference": "Modernisation Ligne Production - Multi commande"
      }
    }
  ]
}
```

### Key Fields - Daily Entry Structure

| What You Need | Where to Find It | Type | Example |
|---------------|------------------|------|---------|
| **Entry ID** | `data.attributes.regularTimes[].id` | string | `"75"` |
| **Work Date** | `data.attributes.regularTimes[].startDate` | string | `"2025-09-15"` |
| **Duration** | `data.attributes.regularTimes[].duration` | number | `1` (1 = 1 day) |
| **Activity Type** | `data.attributes.regularTimes[].workUnitType.activityType` | string | `"production"` |
| **Activity Name** | `data.attributes.regularTimes[].workUnitType.name` | string | `"Normale"` |
| **Project ID** | `data.attributes.regularTimes[].project.id` | string | `"8"` (null for internal) |
| **Project Name** | `data.attributes.regularTimes[].project.reference` | string | `"Modernisation..."` |
| **Delivery ID** | `data.attributes.regularTimes[].delivery.id` | string | `"18"` |
| **Worker ID** | `data.relationships.resource.data.id` | string | `"28"` |

### Activity Types

| Activity Type | Meaning | Billable? | Example |
|---------------|---------|-----------|---------|
| `production` | Client work | Yes | Working on project deliveries |
| `internal` | Company work | No | Training, intercontract, structure |
| `absence` | Time off | No | Vacation, sick leave |

### Parsing Logic - Step by Step

**User Query**: *"What did worker 28 do each day in timesheet 5?"*

**Step 1**: Call API
```python
response = await get_timesheet_by_id(timesheet_id=5)
```

**Step 2**: Extract basic info
```python
timesheet = response["data"]
worker_id = timesheet["relationships"]["resource"]["data"]["id"]
period = timesheet["attributes"]["term"]
state = timesheet["attributes"]["state"]
```

**Step 3**: Process daily entries
```python
daily_entries = timesheet["attributes"]["regularTimes"]

production_days = []
internal_days = []

for entry in daily_entries:
    work_date = entry["startDate"]
    duration = entry["duration"]
    activity_type = entry["workUnitType"]["activityType"]

    if activity_type == "production":
        project_name = entry["project"]["reference"]
        production_days.append({
            "date": work_date,
            "duration": duration,
            "project": project_name,
            "delivery_id": entry["delivery"]["id"]
        })
    elif activity_type == "internal":
        activity_name = entry["workUnitType"]["name"]
        internal_days.append({
            "date": work_date,
            "duration": duration,
            "activity": activity_name
        })
```

**Step 4**: Summarize
```python
print(f"Timesheet {timesheet_id} ({period}) - Worker {worker_id}")
print(f"Production days: {len(production_days)}")
print(f"Internal days: {len(internal_days)}")
print(f"State: {state}")
```

### Critical Notes

1. ⚠️ **Daily entries in attributes.regularTimes[]**: NOT in `data[]` array
2. ⚠️ **Single object response**: `data` is an object, not an array
3. ⚠️ **Null projects for internal work**: Check `activityType` to distinguish
4. ✅ **Duration as days**: 1 = 1 full working day
5. ✅ **Multiple entry arrays**: regularTimes (normal), exceptionalTimes (overtime), absencesTimes (time off)

---

## 🎯 Data Type Reference

### Consistent Patterns

| Type | Format | Example | Notes |
|------|--------|---------|-------|
| **IDs** | string | `"5"`, `"28"` | Always strings, never integers |
| **Dates** | string (ISO) | `"2025-09-15"` | Format: YYYY-MM-DD |
| **DateTimes** | string (ISO+TZ) | `"2025-09-24T15:33:48+0200"` | With timezone offset |
| **Periods** | string | `"2025-09"` | Format: YYYY-MM |
| **Duration** | number | `1`, `0.5` | In days (1 = full day) |
| **State** | string | `"validated"` | validated/pending/rejected |
| **Activity Type** | string | `"production"` | production/internal/absence |

---

## 🔑 Quick Reference Table

### When to Use Which Endpoint

| User Query | Endpoint | Key Fields |
|------------|----------|------------|
| "Get timesheets for worker 28" | `GET /resources/28/timesreports` | `data[].{id, attributes.term, attributes.state}` |
| "Show daily entries for timesheet 5" | `GET /timesreports/5` | `data.attributes.regularTimes[]` |
| "What projects in timesheet 5?" | `GET /timesreports/5` | `data.attributes.regularTimes[].project.reference` |
| "How many production days?" | `GET /timesreports/5` | Filter `regularTimes[]` by `activityType="production"` |

### Common Parsing Patterns

**Get All Timesheets for Worker**:
```python
response = get_resource_timesheets(resource_id=28)
timesheets = response["data"]
for ts in timesheets:
    print(f"{ts['attributes']['term']}: {ts['attributes']['state']}")
```

**Get Daily Breakdown**:
```python
response = get_timesheet_by_id(timesheet_id=5)
entries = response["data"]["attributes"]["regularTimes"]

for entry in entries:
    if entry["workUnitType"]["activityType"] == "production":
        print(f"{entry['startDate']}: {entry['project']['reference']}")
```

**Calculate Total Days by Type**:
```python
response = get_timesheet_by_id(timesheet_id=5)
entries = response["data"]["attributes"]["regularTimes"]

production_total = sum(
    e["duration"] for e in entries
    if e["workUnitType"]["activityType"] == "production"
)
internal_total = sum(
    e["duration"] for e in entries
    if e["workUnitType"]["activityType"] == "internal"
)

print(f"Production: {production_total} days, Internal: {internal_total} days")
```

---

## 📖 Integration with Project Tools

### Connecting Timesheets to Projects

Timesheets link to projects through the productivity endpoint:

1. **From Project → Timesheet**:
   ```python
   # Get workers on project
   productivity = await get_project_productivity(project_id=8)

   # Extract worker IDs and timesheet IDs
   for delivery in productivity["data"]:
       worker_id = delivery["relationships"]["dependsOn"]["data"]["id"]
       timesheet_ids = [tr["id"] for tr in delivery["relationships"]["timesReports"]["data"]]

       # Now fetch timesheet details
       for ts_id in timesheet_ids:
           timesheet = await get_timesheet_by_id(timesheet_id=ts_id)
   ```

2. **From Worker → Projects**:
   ```python
   # Get worker's timesheets
   timesheets = await get_resource_timesheets(resource_id=28)

   # For each timesheet, find projects
   for ts_summary in timesheets["data"]:
       ts_detail = await get_timesheet_by_id(timesheet_id=ts_summary["id"])

       # Extract unique projects
       projects = set()
       for entry in ts_detail["data"]["attributes"]["regularTimes"]:
           if entry["project"]:
               projects.add(entry["project"]["reference"])

       print(f"Period {ts_summary['attributes']['term']}: {projects}")
   ```

---

## ✅ Tool Documentation Status

### Completed
- ✅ `get_resource_timesheets` - Get all timesheets for a worker
- ✅ `get_timesheet_by_id` - Get detailed timesheet with daily entries

### Agent Prompt Enhancements

Add to agent system prompt:
```
When parsing timesheet detail responses:
1. Daily entries are in data.attributes.regularTimes[], NOT data[]
2. Filter by activityType: "production" = billable, "internal" = non-billable
3. Project info is nested: entry.project.{id, reference}
4. Duration is in days: 1 = 1 full working day
5. For internal work, project field is null
```

---

**Status**: ✅ Documentation complete for 2 core timesheet endpoints
**Next**: Integration with project agent for combined queries
