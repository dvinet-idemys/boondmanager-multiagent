# BoondManager API - Quick Reference

**6 Essential Endpoints for Project, Worker & Timesheet Queries**

---

## 📋 Endpoint Overview

### Project Endpoints
| # | Endpoint | Purpose | Returns |
|---|----------|---------|---------|
| 1 | `GET /projects` | Search projects | Array of projects |
| 2 | `GET /projects/{id}` | Project details | Single project object |
| 3 | `GET /projects/{id}/productivity` | **Workers & timesheets** | Deliveries + workers in `included[]` |
| 4 | `GET /projects/{id}/orders` | Orders & billing | Array of orders |

### Timesheet Endpoints
| # | Endpoint | Purpose | Returns |
|---|----------|---------|---------|
| 5 | `GET /resources/{id}/timesreports` | Worker's timesheets | Array of timesheets |
| 6 | `GET /timesreports/{id}` | **Daily time entries** | Single timesheet with daily breakdown |

---

## ⚠️ Critical: Productivity Endpoint

**Worker data is in `included[]`, NOT `data[]`!**

**All values (days, costs, turnover) are for the entire order period, not current month!**

```
Response Structure:
├─ data[] ← Deliveries (NOT workers!)
│   └─ relationships.dependsOn.data.id = "28" ← Worker ID reference
│   └─ attributes.regularTimesProduction = 12 ← Days worked (entire period)
│
└─ included[] ← Worker details HERE!
    └─ [id="28", type="resource"]
        ├─ attributes.firstName = "Elodie"
        └─ attributes.lastName = "Leguay"
```

---

## 🔑 Key Field Paths

### Search Projects (`GET /projects`)

```
data[].id → "8" (string!)
data[].attributes.reference → "Project Name"
data[].attributes.startDate → "2025-09-01"
data[].relationships.company.data.id → "5"
```

### Project Profile (`GET /projects/{id}`)

```
data.id → "8" (single object)
data.attributes.reference → "Project Name"
data.attributes.startDate → "2025-09-01"
data.relationships.mainManager.data.id → "2"
```

### Productivity (`GET /projects/{id}/productivity`) ⭐

```
Worker ID:     data[].relationships.dependsOn.data.id → "28"
First Name:    included[id="28"].attributes.firstName → "Elodie"
Last Name:     included[id="28"].attributes.lastName → "Leguay"
Days Worked:   data[].attributes.regularTimesProduction → 12 (entire order period)
Timesheet ID:  data[].relationships.timesReports.data[0].id → "5"
Cost:          data[].attributes.costsProductionExcludingTax → 6660 (entire period)
```

### Orders (`GET /projects/{id}/orders`)

```
Order ID:      data[].id → "11"
Number:        data[].attributes.number → "CMD2"
Total:         data[].attributes.turnoverOrderedExcludingTax → 49780 (entire period)
Invoiced:      data[].attributes.turnoverInvoicedExcludingTax → 7860 (entire period)
Remaining:     data[].attributes.deltaInvoicedExcludingTax → -41920 (entire period)
```

---

## 💻 Parsing Examples

### Find Project by Name

```python
response = await search_projects(keywords="alpha")
project_id = response["data"][0]["id"]  # "8"
project_name = response["data"][0]["attributes"]["reference"]
```

### Get Workers on Project

```python
response = await get_project_productivity(project_id=8)

# Build lookup map
included_map = {item["id"]: item for item in response["included"]}

# Parse workers
for delivery in response["data"]:
    worker_id = delivery["relationships"]["dependsOn"]["data"]["id"]
    worker = included_map[worker_id]

    print(f"Worker: {worker['attributes']['firstName']} {worker['attributes']['lastName']}")
    print(f"  ID: {worker_id}")
    print(f"  Days: {delivery['attributes']['regularTimesProduction']}")
```

### Get Order Summary

```python
response = await get_project_orders(project_id=8)

for order in response["data"]:
    total = order["attributes"]["turnoverOrderedExcludingTax"]
    invoiced = order["attributes"]["turnoverInvoicedExcludingTax"]
    print(f"Order {order['attributes']['number']}: {total/100:.2f}€")
```

---

## ⚙️ Data Types

| Type | Format | Example |
|------|--------|---------|
| IDs | string | `"8"`, `"28"` |
| Dates | ISO string | `"2025-09-01"` |
| Amounts | integer (cents) | `7860` = 78.60€ |
| Percentages | float | `15.25` = 15.25% |

---

### Timesheets (`GET /resources/{id}/timesreports`)

```
Timesheet ID:  data[].id → "5"
Period:        data[].attributes.term → "2025-09"
State:         data[].attributes.state → "validated"
Closed:        data[].attributes.closed → false
Worker ID:     data[].relationships.resource.data.id → "28"
```

### Timesheet Details (`GET /timesreports/{id}`)

```
Worker ID:     data.relationships.resource.data.id → "28"
Period:        data.attributes.term → "2025-09"
State:         data.attributes.state → "validated"
Daily Entries: data.attributes.regularTimes[] → [{startDate, duration, project}, ...]
Work Date:     data.attributes.regularTimes[0].startDate → "2025-09-15"
Duration:      data.attributes.regularTimes[0].duration → 1 (days)
Activity:      data.attributes.regularTimes[0].workUnitType.activityType → "production"
Project:       data.attributes.regularTimes[0].project.reference → "Project Name"
```

---

## 📖 Full Documentation

- **Projects**: See `docs/API_FINDINGS.md` for complete field documentation and examples
- **Timesheets**: See `docs/TIMESHEET_API_FINDINGS.md` for timesheet-specific documentation
