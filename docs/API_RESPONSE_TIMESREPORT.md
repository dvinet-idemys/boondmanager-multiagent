# Timesheet API Response Documentation

## Overview
This document describes the response structure for the `GET /api/timesreports/{id}` endpoint from the BoondManager API.

## Response Structure

### Top-Level Structure
```json
{
  "meta": {...},      // Metadata including warnings and validators
  "data": {...},      // Main timesheet data
  "included": [...]   // Related resources (resources, agencies, projects, etc.)
}
```

---

## Meta Object

Contains system metadata, warnings, and validator information.

### System Metadata
- **version** (string): BoondManager version
- **isLogged** (boolean): User authentication status
- **language** (string): User language (`fr`, `en`, `es`)

### Warnings Array
Validation warnings related to the timesheet. Each warning contains:

- **code** (string): Warning type identifier
  - `moreThanNumberOfWorkingDays`: Time entries exceed working days
  - `workplaceTimesMoreThanNumberOfWorkingDays`: Workplace times exceed expected
  - `workplaceTimesLessThanNumberOfWorkingDays`: Workplace times below expected
  - `atLeastOneAbsenceQuotaExceeded`: Absence quota limit reached
  - `wrongAbsences`: Invalid absence entries
  - `wrongMandatoryLeaves`: Mandatory leave violations
  - `noDeliveryOnProject`: Project missing delivery assignment
  - `projectDoesNotExist`: Referenced project not found
  - `deliveryDoesNotExist`: Referenced delivery not found
  - `outsideContractDates`: Time entries outside contract period
  - `outsideDeliveryDates`: Time entries outside delivery dates
  - `outsideDocumentDates`: Document date inconsistencies
  - `lessThanNumberOfWorkingDaysInsideContractDates`: Insufficient time within contract
  - `moreThanNumberOfWorkingDaysInsideContractDates`: Excess time within contract
  - `noSignedTimesheet`: Missing required signature
  - `workUnitRatesNotEqual`: Inconsistent work unit rates

- **detail** (string): Human-readable warning message
- **project** (object | null): Associated project reference
- **delivery** (object | null): Associated delivery reference
- **workUnitType** (object | null): Associated work unit type
- **projects** (array): Multiple projects related to the warning

### Validator Lists
Three arrays containing validators with permission levels:

- **expectedValidatorsAllowedForValidate**: Can approve timesheet
- **expectedValidatorsAllowedForUnvalidate**: Can revoke approval
- **expectedValidatorsAllowedForReject**: Can reject timesheet

Each validator object contains:
```json
{
  "id": "string",
  "firstName": "string",
  "lastName": "string"
}
```

---

## Data Object

Main timesheet information.

### Core Attributes

#### Identification
- **id** (string): Timesheet unique identifier (pattern: `^[1-9][0-9]*$`)
- **type** (string): Always `"timesreport"`

#### Timestamps
- **creationDate** (string): ISO 8601 timestamp with timezone
- **updateDate** (string): ISO 8601 timestamp with timezone
- **term** (string): Period covered (format: `YYYY-MM`)

#### Status & Configuration
- **state** (string): Timesheet status
  - `savedAndNoValidation`: Saved, not submitted
  - `waitingForValidation`: Awaiting approval
  - `validated`: Approved
  - `rejected`: Rejected
- **closed** (boolean): Whether timesheet is closed
- **workUnitRate** (number): Standard work rate
- **informationComments** (string): Additional comments (max 500 chars)

### Time Entry Collections

#### 1. Regular Times (`regularTimes`)
Standard working hours on projects/deliveries.

```json
{
  "id": "string",
  "startDate": "YYYY-MM-DD",
  "duration": number,
  "row": integer,
  "workUnitType": {
    "reference": integer,
    "activityType": "production" | "absence" | "internal" | "exceptionalTime" | "exceptionalCalendar",
    "name": "string"
  },
  "calendar": "string",
  "delivery": {...} | null,
  "batch": {...} | null,
  "project": {...} | null
}
```

**Key Fields:**
- **row**: Line identifier (≤0 for new lines)
- **activityType**: Categorizes the work type
- **delivery/batch/project**: Work assignment context

#### 2. Exceptional Times (`exceptionalTimes`)
Non-standard time entries spanning date ranges.

```json
{
  "id": "string",
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "duration": number,
  "recovering": boolean,
  "description": "string",
  "workUnitType": {...},
  "delivery": {...},
  "batch": {...} | null,
  "project": {...}
}
```

**Key Fields:**
- **recovering**: Whether time can be recovered/compensated
- **description**: Explanation of exceptional circumstances (max 1000 chars)
- **Date range**: Start and end dates for the exception period

#### 3. Absence Times (`absencesTimes`)
Time away from work.

```json
{
  "startDate": "YYYY-MM-DD",
  "duration": number,
  "workUnitType": {
    "reference": integer,
    "activityType": "absence",
    "name": "string"
  }
}
```

**Note:** No ID field—absences tracked by date/type combination.

#### 4. Planned Times (`plannedTimes`)
Future/scheduled work allocations.

```json
{
  "id": "string",
  "startDate": "YYYY-MM-DD",
  "duration": number,
  "row": integer,
  "workUnitType": {...},
  "delivery": {...} | null,
  "batch": {...} | null,
  "project": {...} | null
}
```

**Similar to regularTimes but represents planned/forecasted work.**

#### 5. Workplace Times (`workplaceTimes`)
Physical workplace location tracking.

```json
{
  "id": "string",
  "startDate": "YYYY-MM-DD",
  "duration": number,
  "row": integer,
  "workplaceType": {
    "reference": integer,
    "name": "string"
  }
}
```

### Relationships

Links to related resources (expanded in `included` array):

```json
{
  "resource": {...},           // Timesheet owner
  "createdBy": {...} | null,   // Creator
  "agency": {...},             // Associated agency
  "files": [...],              // Attached documents
  "expensesReport": {...} | null,  // Related expense report
  "orders": [...],             // Purchase orders
  "projects": [...],           // Projects involved
  "validations": [...],        // Validation history
  "validationWorkflow": [...], // Expected validators
  "signatures": [...]          // Digital signatures
}
```

---

## Included Array

Contains full details of related resources referenced in the main data object.

### Resource Types

#### 1. **resource** (Person/Employee)
```json
{
  "id": "string",
  "type": "resource",
  "attributes": {
    "firstName": "string",
    "lastName": "string",
    "function": "string",
    "allowExceptionalTimes": -1 | 0 | 1,
    "canRecoverExceptionalTimes": boolean,
    "workUnitTypesAllowed": [...],
    "workUnitRate": number | "notUsed",
    "workplacesDefaultWeek": [...]
  },
  "relationships": {
    "contracts": [...]
  }
}
```

#### 2. **agency** (Company/Department)
```json
{
  "id": "string",
  "type": "agency",
  "attributes": {
    "name": "string",
    "workUnitRate": number | "notUsed",
    "calendar": "string",
    "workplaceTypes": [...],
    "timesLegals": "string",
    "timesAlerts": [...]
  }
}
```

**timesAlerts**: Validation rules configuration
```json
{
  "alert": "moreThanNumberOfWorkingDays" | ...,
  "blocking": boolean
}
```

#### 3. **project** (Client Project)
```json
{
  "id": "string",
  "type": "project",
  "attributes": {
    "reference": "string",
    "mailValidatorSignature": "string",
    "isMonitorSignedTimesheets": boolean
  },
  "relationships": {
    "company": {...},
    "deliveries": [...],
    "batches": [...]
  }
}
```

#### 4. **delivery** (Project Phase/Mission)
```json
{
  "id": "string",
  "type": "delivery",
  "attributes": {
    "title": "string",
    "startDate": "YYYY-MM-DD",
    "endDate": "YYYY-MM-DD"
  }
}
```

#### 5. **batch** (Work Package)
```json
{
  "id": "string",
  "type": "batch",
  "attributes": {
    "title": "string"
  }
}
```

#### 6. **validation** (Approval Record)
```json
{
  "id": "string",
  "type": "validation",
  "attributes": {
    "date": "YYYY-MM-DD",
    "state": "waitingForValidation" | "validated" | "rejected",
    "reason": "string"
  },
  "relationships": {
    "realValidator": {...} | null,
    "expectedValidator": {...}
  }
}
```

#### 7. **signature** (Digital Signature)
```json
{
  "id": "string",
  "type": "signature",
  "attributes": {
    "state": "pending" | "validated",
    "creationDate": "ISO8601",
    "remindDate": "ISO8601",
    "date": "ISO8601",
    "lastName": "string",
    "firstName": "string",
    "function": "string",
    "token": "string",
    "mailValidatorSignature": "string"
  },
  "relationships": {
    "createdBy": {...} | null,
    "remindedBy": {...} | null
  }
}
```

#### 8. **document** (Attached File)
```json
{
  "id": "string",
  "type": "document",
  "attributes": {
    "name": "string",
    "category": "string"
  },
  "relationships": {
    "project": {...},
    "signature": {...}
  }
}
```

#### 9. **order** (Purchase Order)
```json
{
  "id": "string",
  "type": "order",
  "attributes": {
    "reference": "string",
    "number": "string"
  },
  "relationships": {
    "project": {...}
  }
}
```

#### 10. **contract** (Employment Contract)
```json
{
  "id": "string",
  "type": "contract",
  "attributes": {
    "startDate": "YYYY-MM-DD",
    "endDate": "YYYY-MM-DD" | "",
    "calendar": "string"
  },
  "relationships": {
    "agency": {...}
  }
}
```

#### 11. **company** (Client Company)
```json
{
  "id": "string",
  "type": "company",
  "attributes": {
    "name": "string"
  }
}
```

---

## Common Patterns

### Date Formats
- **Date only**: `YYYY-MM-DD` (e.g., `2025-01-15`)
- **Date with time**: `YYYY-MM-DDTHH:MM:SS±HHMM` (e.g., `2025-01-15T14:30:00+0100`)
- **Month/year**: `YYYY-MM` (e.g., `2025-01`)

### Nullable Relationships
Many relationships use `oneOf` pattern:
```json
{
  "oneOf": [
    {"data": null},           // No relationship
    {"id": "...", "type": "..."} // Linked resource
  ]
}
```

### ID Pattern
All numeric IDs: `^[1-9][0-9]*$` (positive integers as strings)

---

## Usage for Timesheet Agent

### Key Information to Extract

1. **Timesheet Status**
   - `data.attributes.state`: Current approval state
   - `meta.warnings`: Issues requiring attention
   - `data.attributes.closed`: Final/editable status

2. **Time Entries**
   - `data.attributes.regularTimes`: Primary work hours
   - `data.attributes.absencesTimes`: Time off
   - `data.attributes.exceptionalTimes`: Special circumstances
   - **Calculate total hours per project/delivery**

3. **Validation Workflow**
   - `meta.expectedValidatorsAllowedForValidate`: Who can approve
   - `data.relationships.validations`: Approval history
   - `data.relationships.validationWorkflow`: Expected approval chain

4. **Project Context**
   - Link time entries to projects via `included` array
   - Find project details: `included[type="project"]`
   - Resolve deliveries and batches

5. **Warnings & Compliance**
   - Check `meta.warnings` for validation issues
   - `meta.warnings[].code`: Specific rule violations
   - Block submission if critical warnings present

### Example Agent Logic Flow

```python
# 1. Parse timesheet response
timesheet_data = response['data']
warnings = response['meta']['warnings']
included = response['included']

# 2. Check validation status
if timesheet_data['attributes']['state'] == 'waitingForValidation':
    # Identify validators
    validators = response['meta']['expectedValidatorsAllowedForValidate']

# 3. Calculate total hours by project
project_hours = {}
for time_entry in timesheet_data['attributes']['regularTimes']:
    project_id = time_entry['project']['id']
    project_hours[project_id] = project_hours.get(project_id, 0) + time_entry['duration']

# 4. Check for blocking warnings
blocking_warnings = [w for w in warnings if w['code'] in BLOCKING_CODES]
if blocking_warnings:
    # Handle validation issues
    pass

# 5. Resolve project names from included array
projects = {p['id']: p for p in included if p['type'] == 'project'}
```

---

## Notes

- **Database references**: Schema includes `database` fields showing underlying table/column mappings
- **Uniqueness**: Many arrays specify `"uniqueItems": true` to prevent duplicates
- **Required fields**: Check schema `required` arrays for mandatory fields
- **Max lengths**: String fields have `maxLength` constraints for validation

---

## Related Endpoints

- `GET /api/timesreports` - List timesheets
- `POST /api/timesreports` - Create timesheet
- `PATCH /api/timesreports/{id}` - Update timesheet
- `DELETE /api/timesreports/{id}` - Delete timesheet
- `POST /api/timesreports/{id}/validate` - Submit for validation

---

## Version

This documentation corresponds to the BoondManager API schema:
- **Schema ID**: `schemas/timesReports/profile.json`
- **JSON Schema**: Draft 7
