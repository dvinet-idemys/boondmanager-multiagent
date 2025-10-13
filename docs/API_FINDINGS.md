# BoondManager API Exploration Findings

**Date**: 2025-10-10
**Scope**: Core project endpoints only
**Status**: ✅ Complete with real data

---

## 🎯 Essential Endpoints

This documentation covers the **4 core endpoints** needed for project and worker queries:

1. **`GET /projects`** - Search and list projects
2. **`GET /projects/{id}`** - Get project details
3. **`GET /projects/{id}/productivity`** - Get workers and timesheets ⭐
4. **`GET /projects/{id}/orders`** - Get project orders and billing

---

## ⚠️ CRITICAL: Productivity Endpoint Structure

### The Most Important Discovery

**Worker data is NOT in `data[]` - It's in `included[]`!**

The productivity endpoint uses JSON:API's included pattern:
- `data[]` contains **delivery records** (assignments)
- `included[]` contains **worker details** (names, IDs)
- You must **cross-reference** them using relationship IDs

### Visual Structure

```
Productivity Response
│
├─ data[] ← Delivery/assignment records
│   └─ relationships.dependsOn.data.id = "28" ← Worker ID (reference)
│   └─ attributes.regularTimesProduction = 12 ← Days worked
│
└─ included[] ← Related entities (workers, timesheets)
    └─ [where type="resource" and id="28"] ← Find worker here!
        └─ attributes.firstName = "Elodie"
        └─ attributes.lastName = "Leguay"
```

---

## 📊 Endpoint 1: Search Projects

### `GET /projects`

**Purpose**: Find projects by name, company, or other filters

**Real Response Structure**:
```json
{
  "meta": {
    "totals": {
      "rows": 3
    },
    "version": "9.0.5.3",
    "isLogged": true,
    "login": "dvinet@idemys.com"
  },
  "data": [
    {
      "id": "8",
      "type": "project",
      "attributes": {
        "reference": "Modernisation Ligne Production - Multi commande",
        "startDate": "2025-09-01",
        "endDate": "2025-12-31",
        "typeOf": 1,
        "mode": 1,
        "turnoverSimulatedExcludingTax": 106196,
        "marginSimulatedExcludingTax": 16200,
        "profitabilitySimulated": 15.25,
        "canReadProject": true,
        "creationDate": "2025-09-24T15:08:14+0200",
        "updateDate": "2025-09-24T15:10:20+0200"
      },
      "relationships": {
        "mainManager": {
          "data": {"id": "2", "type": "resource"}
        },
        "company": {
          "data": {"id": "5", "type": "company"}
        },
        "agency": {
          "data": {"id": "1", "type": "agency"}
        },
        "contact": {
          "data": {"id": "5", "type": "contact"}
        }
      }
    }
  ],
  "included": [
    {
      "id": "2",
      "type": "resource",
      "attributes": {
        "firstName": "Dimitri",
        "lastName": "VINET"
      }
    }
  ]
}
```

### Key Fields

| Field Path | Type | Example | Notes |
|------------|------|---------|-------|
| **Project Identification** ||||
| `data[].id` | string | `"8"` | ⚠️ **String**, not int! |
| `data[].attributes.reference` | string | `"Modernisation..."` | **Project name/title** |
| **Dates** ||||
| `data[].attributes.startDate` | string | `"2025-09-01"` | ISO format (YYYY-MM-DD) |
| `data[].attributes.endDate` | string | `"2025-12-31"` | ISO format (YYYY-MM-DD) |
| `data[].attributes.creationDate` | string | `"2025-09-24T15:08:14+0200"` | ISO datetime |
| **Financial** ||||
| `data[].attributes.turnoverSimulatedExcludingTax` | int | `106196` | Revenue forecast (cents) |
| `data[].attributes.marginSimulatedExcludingTax` | int | `16200` | Margin forecast (cents) |
| `data[].attributes.profitabilitySimulated` | float | `15.25` | Profitability % |
| **Relationships** ||||
| `data[].relationships.company.data.id` | string | `"5"` | Client company ID |
| `data[].relationships.mainManager.data.id` | string | `"2"` | Project manager ID |
| `data[].relationships.agency.data.id` | string | `"1"` | Agency ID |
| `data[].relationships.contact.data.id` | string | `"5"` | Client contact ID |

### Important Notes

1. ⚠️ **Project IDs are strings**: `"8"`, not `8`
2. ⚠️ **No `title` field**: Use `attributes.reference` for project name
3. ✅ **Related entities** in `included[]`: Managers, companies, etc.
4. ✅ **Financial amounts** in smallest unit (cents): `106196` = 1061.96€

### Query Example

**User Query**: *"Find project Modernisation"*

**API Call**: `GET /projects?keywords=modernisation`

**Parse**:
```python
projects = response["data"]
for project in projects:
    project_id = project["id"]                    # "8"
    project_name = project["attributes"]["reference"]  # "Modernisation..."
```

---

## 📊 Endpoint 2: Project Profile

### `GET /projects/{id}`

**Purpose**: Get detailed information about a specific project

**Real Response Structure**:
```json
{
  "meta": {
    "version": "9.0.5.3",
    "isLogged": true
  },
  "data": {
    "id": "8",
    "type": "project",
    "attributes": {
      "reference": "Modernisation Ligne Production - Multi commande",
      "typeOf": 1,
      "mode": 1,
      "startDate": "2025-09-01",
      "creationDate": "2025-09-24T15:08:14+0200",
      "updateDate": "2025-09-24T15:10:20+0200",
      "isProjectManager": null,
      "currencyAgency": null,
      "currency": null,
      "exchangeRate": 1,
      "exchangeRateAgency": 1,
      "workUnitRate": 1,
      "deliverySuggestFilters": []
    },
    "relationships": {
      "agency": {"data": {"id": "1", "type": "agency"}},
      "mainManager": {"data": {"id": "2", "type": "resource"}},
      "company": {"data": {"id": "5", "type": "company"}},
      "opportunity": {"data": {"id": "4", "type": "opportunity"}}
    }
  },
  "included": [
    {
      "id": "1",
      "type": "agency",
      "attributes": {
        "name": "IDEMYS - SANDBOX"
      }
    }
  ]
}
```

### Key Fields

| Field Path | Type | Example | Notes |
|------------|------|---------|-------|
| **Project Info** ||||
| `data.id` | string | `"8"` | Note: Single object, not array |
| `data.attributes.reference` | string | `"Modernisation..."` | Project name |
| `data.attributes.typeOf` | int | `1` | Project type |
| `data.attributes.mode` | int | `1` | Project mode |
| **Dates** ||||
| `data.attributes.startDate` | string | `"2025-09-01"` | Start date |
| `data.attributes.creationDate` | string | `"2025-09-24T15:08:14+0200"` | Created timestamp |
| `data.attributes.updateDate` | string | `"2025-09-24T15:10:20+0200"` | Last updated |
| **Settings** ||||
| `data.attributes.exchangeRate` | int | `1` | Currency exchange rate |
| `data.attributes.workUnitRate` | int | `1` | Work unit conversion |
| **Relationships** ||||
| `data.relationships.company.data.id` | string | `"5"` | Client company |
| `data.relationships.mainManager.data.id` | string | `"2"` | Project manager |
| `data.relationships.opportunity.data.id` | string | `"4"` | Related opportunity |

### Differences from Search

- Returns **single object** in `data`, not array
- More detailed attributes
- No financial summaries (turnover, margin)
- Includes `workUnitRate`, `exchangeRate`

---

## ⭐ Endpoint 3: Project Productivity (CRITICAL)

### `GET /projects/{id}/productivity`

**Purpose**: Get workers, timesheets, and actual work done on a project

**This is THE endpoint for**: *"Who works on project X?"* queries

### Real Response Structure

```json
{
  "meta": {
    "totals": {
      "rows": 2,
      "turnoverProductionExcludingTax": 22292,
      "costsProductionExcludingTax": 18892,
      "marginProductionExcludingTax": 3400,
      "profitabilityProduction": 15.25
    }
  },
  "data": [
    {
      "id": "18",
      "type": "delivery",
      "attributes": {
        "title": "",
        "startDate": "2025-09-15",
        "endDate": "2025-12-31",
        "numberOfDaysInvoicedOrQuantity": 76,
        "regularTimesProduction": 12,
        "regularTimesProductionInWorkUnits": 12,
        "turnoverProductionExcludingTax": 7860,
        "costsProductionExcludingTax": 6660
      },
      "relationships": {
        "dependsOn": {
          "data": {
            "id": "28",
            "type": "resource"
          }
        },
        "timesReports": {
          "data": [
            {
              "id": "5",
              "type": "timesreport"
            }
          ]
        },
        "project": {
          "data": {
            "id": "8",
            "type": "project"
          }
        }
      }
    },
    {
      "id": "19",
      "type": "delivery",
      "attributes": {
        "regularTimesProduction": 22,
        "turnoverProductionExcludingTax": 14432,
        "costsProductionExcludingTax": 12232
      },
      "relationships": {
        "dependsOn": {
          "data": {
            "id": "29",
            "type": "resource"
          }
        },
        "timesReports": {
          "data": [{"id": "4", "type": "timesreport"}]
        }
      }
    }
  ],
  "included": [
    {
      "id": "28",
      "type": "resource",
      "attributes": {
        "firstName": "Elodie",
        "lastName": "Leguay",
        "canReadResource": true
      },
      "relationships": {
        "timesReports": {
          "data": [{"id": "5", "type": "timesreport"}]
        }
      }
    },
    {
      "id": "29",
      "type": "resource",
      "attributes": {
        "firstName": "Didier",
        "lastName": "Geig",
        "canReadResource": true
      }
    },
    {
      "id": "5",
      "type": "timesreport",
      "attributes": {
        "term": "2025-09"
      }
    },
    {
      "id": "4",
      "type": "timesreport",
      "attributes": {
        "term": "2025-09"
      }
    }
  ]
}
```

### Key Fields - Worker Information Path

| What You Need | Where to Find It | Type | Example |
|---------------|------------------|------|---------|
| **Worker ID** | `data[].relationships.dependsOn.data.id` | string | `"28"` |
| **Worker First Name** | `included[id=28].attributes.firstName` | string | `"Elodie"` |
| **Worker Last Name** | `included[id=28].attributes.lastName` | string | `"Leguay"` |
| **Days Worked** | `data[].attributes.regularTimesProduction` | int | `12` (entire order period) |
| **Timesheet ID** | `data[].relationships.timesReports.data[0].id` | string | `"5"` |
| **Cost** | `data[].attributes.costsProductionExcludingTax` | int | `6660` (entire period) |
| **Revenue** | `data[].attributes.turnoverProductionExcludingTax` | int | `7860` (entire period) |

### Parsing Logic - Step by Step

**User Query**: *"Give me names and ids for workers on project 8"*

**Step 1**: Call API
```python
response = await get_project_productivity(project_id=8)
```

**Step 2**: Build lookup map from `included[]`
```python
included_map = {item["id"]: item for item in response["included"]}
```

**Step 3**: Process each delivery in `data[]`
```python
workers = []
for delivery in response["data"]:
    # Get worker ID from relationship
    worker_id = delivery["relationships"]["dependsOn"]["data"]["id"]

    # Lookup worker details in included
    worker = included_map[worker_id]

    # Extract data
    workers.append({
        "id": worker_id,
        "firstName": worker["attributes"]["firstName"],
        "lastName": worker["attributes"]["lastName"],
        "daysWorked": delivery["attributes"]["regularTimesProduction"],
        "timesheetId": delivery["relationships"]["timesReports"]["data"][0]["id"],
        "cost": delivery["attributes"]["costsProductionExcludingTax"]
    })
```

**Step 4**: Format response
```python
# Result:
# [
#   {
#     "id": "28",
#     "firstName": "Elodie",
#     "lastName": "Leguay",
#     "daysWorked": 12,
#     "timesheetId": "5",
#     "cost": 6660
#   },
#   {
#     "id": "29",
#     "firstName": "Didier",
#     "lastName": "Geig",
#     "daysWorked": 22,
#     "timesheetId": "4",
#     "cost": 12232
#   }
# ]
```

### Critical Notes

1. ⚠️ **Worker details NOT in `data[]`**: Must lookup in `included[]`
2. ⚠️ **Cross-reference required**: Use `dependsOn.data.id` to find worker
3. ⚠️ **Values are cumulative**: Days, costs, and turnover are for the entire order period, not current month
4. ✅ **Multiple workers**: One delivery record per worker assignment
5. ✅ **Timesheet linking**: Each delivery links to timesheet(s)

---

## 📊 Endpoint 4: Project Orders

### `GET /projects/{id}/orders`

**Purpose**: Get orders, billing, and invoicing information for a project

**Real Response Structure**:
```json
{
  "meta": {
    "totals": {
      "rows": 2,
      "turnoverOrderedExcludingTax": 106196,
      "turnoverInvoicedExcludingTax": 22292,
      "deltaInvoicedExcludingTax": -83904,
      "marginSignedExcludingTax": 16200,
      "profitabilityOrdered": 82.21
    }
  },
  "data": [
    {
      "id": "11",
      "type": "order",
      "attributes": {
        "date": "2025-09-24",
        "startDate": "2025-09-15",
        "endDate": "2025-12-31",
        "number": "CMD2",
        "reference": "BM1000000000011",
        "customerAgreement": null,
        "turnoverInvoicedExcludingTax": 7860,
        "turnoverOrderedExcludingTax": 49780,
        "deltaInvoicedExcludingTax": -41920,
        "state": 1,
        "canReadOrder": true,
        "canWriteOrder": true
      }
    },
    {
      "id": "7",
      "type": "order",
      "attributes": {
        "date": "2025-09-24",
        "startDate": "2025-09-01",
        "endDate": "2025-12-31",
        "number": "CMD",
        "reference": "BM1000000000007",
        "turnoverInvoicedExcludingTax": 14432,
        "turnoverOrderedExcludingTax": 56416,
        "deltaInvoicedExcludingTax": -41984,
        "state": 1
      }
    }
  ]
}
```

### Key Fields

| Field Path | Type | Example | Notes |
|------------|------|---------|-------|
| **Order Identification** ||||
| `data[].id` | string | `"11"` | Order ID |
| `data[].attributes.number` | string | `"CMD2"` | Order number |
| `data[].attributes.reference` | string | `"BM1000000000011"` | BoondManager reference |
| **Dates** ||||
| `data[].attributes.date` | string | `"2025-09-24"` | Order date |
| `data[].attributes.startDate` | string | `"2025-09-15"` | Start date |
| `data[].attributes.endDate` | string | `"2025-12-31"` | End date |
| **Financial** ||||
| `data[].attributes.turnoverOrderedExcludingTax` | int | `49780` | Total ordered (cents, entire period) |
| `data[].attributes.turnoverInvoicedExcludingTax` | int | `7860` | Already invoiced (cents, entire period) |
| `data[].attributes.deltaInvoicedExcludingTax` | int | `-41920` | Remaining to invoice (cents, entire period) |
| **Status** ||||
| `data[].attributes.state` | int | `1` | Order state |
| `data[].attributes.customerAgreement` | bool/null | `null` | Customer approval |

### Important Notes

1. ✅ **Multiple orders per project**: Array of order records
2. ✅ **Financial tracking**: See ordered vs invoiced vs remaining
3. ✅ **Delta calculation**: Negative delta = still to invoice
4. ⚠️ **Amounts in cents**: `49780` = 497.80€
5. ⚠️ **Values are cumulative**: All amounts represent entire order period (startDate to endDate)

### Query Example

**User Query**: *"What are the orders for project 8?"*

**Parse**:
```python
orders = response["data"]
for order in orders:
    order_number = order["attributes"]["number"]
    total = order["attributes"]["turnoverOrderedExcludingTax"]
    invoiced = order["attributes"]["turnoverInvoicedExcludingTax"]
    remaining = order["attributes"]["deltaInvoicedExcludingTax"]

    print(f"Order {order_number}: {total/100:.2f}€ total, {invoiced/100:.2f}€ invoiced, {abs(remaining)/100:.2f}€ remaining")
```

---

## 🎯 Data Type Reference

### Consistent Patterns Across All Endpoints

| Type | Format | Example | Notes |
|------|--------|---------|-------|
| **IDs** | string | `"8"`, `"28"` | Always strings, never integers |
| **Dates** | string (ISO) | `"2025-09-01"` | Format: YYYY-MM-DD |
| **DateTimes** | string (ISO+TZ) | `"2025-09-24T15:08:14+0200"` | With timezone offset |
| **Amounts** | integer | `7860`, `106196` | In smallest unit (cents) |
| **Percentages** | float | `15.25`, `82.21` | As decimal (15.25 = 15.25%) |
| **Booleans** | bool/null | `true`, `false`, `null` | Can be null |

### JSON:API Pattern

All endpoints follow **JSON:API specification**:

```json
{
  "meta": {
    // Metadata: totals, pagination, version
  },
  "data": {
    // or []
    // Primary data (single object or array)
  },
  "included": [
    // Related entities (sideloaded)
  ]
}
```

**Relationship Structure**:
```json
{
  "relationships": {
    "resourceName": {
      "data": {
        "id": "...",
        "type": "..."
      }
    }
  }
}
```

---

## 🔑 Quick Reference Table

### When to Use Which Endpoint

| User Query | Endpoint | Key Fields |
|------------|----------|------------|
| "Find project Alpha" | `GET /projects?keywords=alpha` | `data[].id`, `data[].attributes.reference` |
| "Get details for project 8" | `GET /projects/8` | `data.attributes.*` |
| "Who works on project 8?" | `GET /projects/8/productivity` | `included[type=resource].attributes.{firstName, lastName}` |
| "What are the orders for project 8?" | `GET /projects/8/orders` | `data[].attributes.{number, turnover*}` |

### Common Parsing Patterns

**Get Project ID by Name**:
```python
response = search_projects(keywords="alpha")
project_id = response["data"][0]["id"]
```

**Get Workers from Productivity**:
```python
response = get_project_productivity(project_id=8)
included_map = {item["id"]: item for item in response["included"]}

for delivery in response["data"]:
    worker_id = delivery["relationships"]["dependsOn"]["data"]["id"]
    worker = included_map[worker_id]
    print(f"{worker['attributes']['firstName']} {worker['attributes']['lastName']}")
```

**Get Financial Summary from Orders**:
```python
response = get_project_orders(project_id=8)
total_ordered = sum(o["attributes"]["turnoverOrderedExcludingTax"] for o in response["data"])
total_invoiced = sum(o["attributes"]["turnoverInvoicedExcludingTax"] for o in response["data"])
```

---

## ✅ Tool Documentation Updates Needed

### Priority Updates

1. **`get_project_productivity`** - Add `included[]` parsing example
2. **`search_projects`** - Document string IDs and `reference` field
3. **`get_project_by_id`** - Note single object response
4. **`get_project_orders`** - Document financial fields

### Agent Prompt Enhancement

Add to agent system prompt:
```
When parsing productivity responses:
1. Worker names are in included[], NOT data[]
2. Get worker ID from data[].relationships.dependsOn.data.id
3. Lookup worker in included[] by matching id
4. Days worked: data[].attributes.regularTimesProduction
```

---

**Status**: ✅ Documentation complete for 4 core endpoints
**Next**: Update tool docstrings with accurate field paths
