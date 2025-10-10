# BoondManager Invoicing API - Comprehensive Documentation

**Research Date:** 2025-10-09
**API Documentation Source:** https://doc.boondmanager.com/api-externe/
**API Version:** 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core Invoice Endpoints](#core-invoice-endpoints)
4. [Invoice Management Endpoints](#invoice-management-endpoints)
5. [Related Endpoints](#related-endpoints)
6. [Invoice Workflow](#invoice-workflow)
7. [Common Query Parameters](#common-query-parameters)
8. [Error Handling](#error-handling)

---

## Overview

The BoondManager API provides a comprehensive set of endpoints for managing the complete invoice lifecycle, from creation and search to payment processing and document generation. The invoicing process integrates with projects, orders, deliveries, and payment management.

### Base URL Structure
```
https://{apiServer}/api/{apiVersion}/
```

**Default values:**
- `apiServer`: `ui.boondmanager.com`
- `apiVersion`: `1.0`

---

## Authentication

### Basic Authentication

All API requests require HTTP Basic Authentication.

**Authorization Header Format:**
```
Authorization: Basic {base64_encoded_credentials}
```

**Credentials Format:**
```
username:password → Base64 encode → Authorization header
```

**Example:**
- Username: `test@domain.tld`
- Password: `test`
- Header: `Authorization: Basic dGVzdEBkb21haW4udGxkOnRlc3Q=`

**Important Notes:**
- API access must be enabled in BoondManager settings:
  - Admin interface: `dashboard > API settings`
  - User interface: `settings > security > API access`
- Alternative authentication schemes available:
  - `x-Jwt-App`
  - `x-Jwt-Client`

---

## Core Invoice Endpoints

### 1. Search Invoices - `GET /invoices`

Search and retrieve invoices with extensive filtering capabilities.

**Endpoint:** `GET /api/invoices`

**Type:** Search (searchable, sortable, paginable)

**Description:** Search invoices with support for filtering by amount, dates, states, projects, and more. Supports CSV export.

#### Key Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `keywords` | string | Search by invoice ID (`FACT**ID**`), order (`BDC**ID**`), project (`PRJ**ID**`), contact (`CCON**ID**`), company (`CSOC**ID**`) |
| `states` | integer[] | Filter by invoice state IDs (see dictionary) |
| `closed` | boolean | `true` = only closed invoices, `false` = only open invoices |
| `creditNote` | boolean | `true` = only credit notes, `false` = only invoices |
| `period` | string | Date filter type: `created`, `updated`, `expectedPayment`, `performedPayment`, `period` |
| `startDate` | string | Start date (format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`) |
| `endDate` | string | End date (format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`) |
| `periodDynamic` | string | Predefined periods: `today`, `thisWeek`, `thisMonth`, `lastMonth`, `thisYear`, etc. |
| `amount` | number | Filter by exact amount |
| `amountMin` | number | Minimum amount |
| `amountMax` | number | Maximum amount |
| `amountColumn` | string | Amount field to filter: `totalExcludingTax`, `totalIncludingTax`, `totalPayableIncludingTax` |
| `amountType` | string | `equal` or `between` |
| `amountCurrency` | integer | Currency ID |
| `paymentMethods` | integer[] | Payment method IDs |
| `projectTypes` | integer[] | Project type IDs |
| `flags` | integer[] | Filter by attached flag IDs |
| `page` | number | Page number (default: 1, min: 1) |
| `maxResults` | number | Results per page (default: 30, range: 1-500) |
| `order` | string | Sort order: `asc` or `desc` (default: `asc`) |
| `sort` | string[] | Sort columns (see sortable columns below) |
| `columns` | string[] | Select specific columns to return |

#### Sortable Columns
- `turnoverInvoicedIncludingTax`
- `date`
- `reference`
- `turnoverInvoicedExcludingTax`
- `expectedPaymentDate`
- `state`
- `order.number`
- `order.project.reference`
- `order.project.company.name`
- `order.mainManager.lastName`
- `closed`
- `startDate`
- `endDate`
- `intermediaryCompany.name`

#### Returnable Columns
- `date`, `reference`, `project`, `order`, `customer`, `state`
- `expectedPaymentDate`, `performedPaymentDate`
- `turnoverInvoicedExcludingTax`, `turnoverInvoicedIncludingTax`
- `totalPayableIncludingTax`
- `mainManager`, `creationDate`, `updateDate`
- `startDate`, `endDate`, `billingIntermediary`

#### Perimeter Filtering

| Parameter | Description |
|-----------|-------------|
| `perimeterAgencies` | integer[] - Filter by agency IDs |
| `perimeterBusinessUnits` | integer[] - Filter by business unit IDs |
| `perimeterPoles` | integer[] - Filter by pole IDs |
| `perimeterManagers` | integer[] - Filter by manager IDs |
| `perimeterDynamic` | string - Dynamic filters: `data`, `agencies`, `poles`, `businessUnits`, `managers` |
| `narrowPerimeter` | boolean - `false` = OR join, `true` = AND join (default: OR) |

#### CSV Export

Add `.csv` to the URL to export results:
```
GET /api/invoices.csv?keywords=FACT123
```

**CSV Parameters:**
- `encoding`: `UTF-8`, `ISO-8859-15`, `WINDOWS-1250`, `MAC-OS-ROMAN`
- `extractType`: `detailed` or `notDetailed` (default)
- `exportToDownloadCenter`: Export to download center with options:
  - `documentsAndAttachments`
  - `documentsOnly`
  - `attachmentsOnly`
  - `cii` (Cross Industry Invoice format)

#### Response Codes
- **200**: Success - returns invoice list
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **422**: Validation Error
- **500**: Server Error
- **503**: Service Unavailable

---

### 2. Create Invoice - `POST /invoices`

Create a new invoice in the system.

**Endpoint:** `POST /api/invoices`

**Type:** Search

**Description:** Create new invoices. Request body should contain invoice details.

**Content-Type:** `application/json`

---

## Invoice Management Endpoints

### 3. Get Invoice Cart Data - `GET /invoices/cart`

**Endpoint:** `GET /api/invoices/cart`

**Type:** Search

**Description:** Get new invoice data from cart definition. Used to prepare invoice creation based on cart contents.

---

### 4. Get Default Invoice Information - `GET /invoices/default`

**Endpoint:** `GET /api/invoices/default`

**Type:** Profile

**Description:** Retrieve default information data for creating an empty invoice. Provides template data for new invoices.

---

### 5. Get Invoice Profile - `GET /invoices/{id}`

**Endpoint:** `GET /api/invoices/{id}`

**Type:** Profile

**Description:** Retrieve complete profile information for a specific invoice.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

---

### 6. Delete Invoice - `DELETE /invoices/{id}`

**Endpoint:** `DELETE /api/invoices/{id}`

**Type:** Profile

**Description:** Delete a specific invoice from the system.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

---

### 7. Get Invoice Rights - `GET /invoices/{id}/rights`

**Endpoint:** `GET /api/invoices/{id}/rights`

**Type:** Rights

**Description:** Retrieve user permissions and rights for a specific invoice. Determines what operations the current user can perform.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

---

### 8. Get Invoice Information - `GET /invoices/{id}/information`

**Endpoint:** `GET /api/invoices/{id}/information`

**Type:** Profile

**Description:** Retrieve detailed information data for a specific invoice.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

---

### 9. Update Invoice Information - `PUT /invoices/{id}/information`

**Endpoint:** `PUT /api/invoices/{id}/information`

**Type:** Profile

**Description:** Update invoice information data.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

**Content-Type:** `application/json`

---

### 10. Get Invoice Attached Flags - `GET /invoices/{id}/attached-flags`

**Endpoint:** `GET /api/invoices/{id}/attached-flags`

**Type:** Profile

**Description:** Retrieve flags attached to a specific invoice. Flags are used for categorization and filtering.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

---

### 11. Get Invoice Actions - `GET /invoices/{id}/actions`

**Endpoint:** `GET /api/invoices/{id}/actions`

**Type:** Profile

**Description:** Retrieve available actions and action history for a specific invoice.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

---

### 12. Download Invoice Document - `GET /invoices/{id}/download`

**Endpoint:** `GET /api/invoices/{id}/download`

**Type:** Download

**Description:** Download the formatted invoice file (PDF or other configured format).

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

**Response:** Binary file download

---

### 13. Get Invoice Billable Items - `GET /invoices/{id}/billable-items`

**Endpoint:** `GET /api/invoices/{id}/billable-items`

**Type:** Profile

**Description:** Retrieve all billable items associated with an invoice. Shows line items, products, and services.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

---

### 14. Send Invoice by Email - `POST /invoices/{id}/send`

**Endpoint:** `POST /api/invoices/{id}/send`

**Type:** Base

**Description:** Send invoice document by email to designated recipients.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

**Content-Type:** `application/json`

**Request Body:** Should include email recipients and optional message.

---

### 15. Get Invoice Tasks - `GET /invoices/{id}/tasks`

**Endpoint:** `GET /api/invoices/{id}/tasks`

**Type:** Profile

**Description:** Retrieve tasks associated with a specific invoice.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

---

### 16. Adjust Invoice - `PUT /invoices/{id}/adjust`

**Endpoint:** `PUT /api/invoices/{id}/adjust`

**Type:** Profile

**Description:** Adjust invoice amounts, items, or other modifiable fields.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

**Content-Type:** `application/json`

---

### 17. Check Invoice Properties - `GET /invoices/{id}/check`

**Endpoint:** `GET /api/invoices/{id}/check`

**Type:** Base

**Description:** Check invoice properties and states, including e-invoicing compliance status.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

---

### 18. Get Invoice Preview - `GET /invoices/{id}/preview`

**Endpoint:** `GET /api/invoices/{id}/preview`

**Type:** Profile

**Description:** Get invoice document preview without downloading.

**Path Parameters:**
- `id` (integer, required): Invoice unique identifier

---

## Related Endpoints

### E-Invoicing

#### Get E-Invoicing Schemes - `GET /e-invoicing/schemes`

**Endpoint:** `GET /api/e-invoicing/schemes`

**Type:** Profile

**Description:** Retrieve available e-invoicing schemes and configurations for electronic invoice submission.

---

### Invoicing Connections

#### Search Invoicing Connectors - `GET /invoicing-connections`

**Endpoint:** `GET /api/invoicing-connections`

**Type:** Search

**Description:** Search for configured invoicing connector integrations with accounting systems.

#### Create Invoicing Connection - `POST /invoicing-connections`

**Endpoint:** `POST /api/invoicing-connections`

**Type:** Search

**Description:** Create new invoicing connector integration.

---

### Payments

#### Search Payments - `GET /payments`

**Endpoint:** `GET /api/payments`

**Type:** Search

**Description:** Search payment records associated with invoices.

**Key Features:**
- Filter payments by invoice, date, method, amount
- Track payment status and history
- Associate payments with specific invoices

#### Create Payment - `POST /payments`

**Endpoint:** `POST /api/payments`

**Type:** Search

**Description:** Record a new payment against one or more invoices.

---

### Orders

#### Search Orders - `GET /orders`

**Endpoint:** `GET /api/orders`

**Type:** Search

**Description:** Search orders that can be billed. Orders are the source documents for invoice creation.

#### Create Order - `POST /orders`

**Endpoint:** `POST /api/orders`

**Type:** Search

**Description:** Create new order that can later be invoiced.

---

### Deliveries and Groupments

#### Create Deliveries - `POST /deliveries`

**Endpoint:** `POST /api/deliveries`

**Type:** Search

**Description:** Create delivery records that can be invoiced.

#### Create Groupments - `POST /groupments`

**Endpoint:** `POST /api/groupments`

**Type:** Search

**Description:** Create groupment records for bundling multiple items for invoicing.

#### Search Deliveries & Groupments - `GET /deliveries-groupments`

**Endpoint:** `GET /api/deliveries-groupments`

**Type:** Search

**Description:** Search both deliveries and groupments together.

---

### Billing Balance Endpoints

#### Deliveries/Purchases Balance - `GET /billing-deliveries-purchases-balance`

**Endpoint:** `GET /api/billing-deliveries-purchases-balance`

**Type:** Search

**Description:** Search deliveries or purchases with a billing balance. Shows what remains to be invoiced.

#### Monthly Billing Balance - `GET /billing-monthly-balance`

**Endpoint:** `GET /api/billing-monthly-balance`

**Type:** Search

**Description:** Search orders with a monthly billing balance.

#### Project Billing Balance - `GET /billing-projects-balance`

**Endpoint:** `GET /api/billing-projects-balance`

**Type:** Search

**Description:** Search projects with a billing balance. Shows unbilled project work.

#### Schedule Billing Balance - `GET /billing-schedules-balance`

**Endpoint:** `GET /api/billing-schedules-balance`

**Type:** Search

**Description:** Search schedules with a billing balance. Tracks scheduled billing milestones.

---

### Supporting Entities

#### Projects - `GET /projects`

**Endpoint:** `GET /api/projects`

**Description:** Projects are the primary entity that gets invoiced. Search projects to find invoiceable work.

#### Companies - `GET /companies`

**Endpoint:** `GET /api/companies`

**Description:** Customer companies that receive invoices. Required for invoice creation.

#### Contacts - `GET /contacts`

**Endpoint:** `GET /api/contacts`

**Description:** Contact persons within companies for invoice delivery and communication.

---

## Invoice Workflow

### Standard Invoicing Process

```mermaid
graph TD
    A[Create Project] --> B[Create Order]
    B --> C[Perform Work/Deliveries]
    C --> D[Create Deliveries/Groupments]
    D --> E[Check Billing Balance]
    E --> F{Ready to Invoice?}
    F -->|Yes| G[Get Default Invoice Data]
    G --> H[Create Invoice Draft]
    H --> I[Add Billable Items]
    I --> J[Adjust Invoice if Needed]
    J --> K[Finalize Invoice]
    K --> L[Download Invoice Document]
    L --> M[Send Invoice by Email]
    M --> N[Track Payment]
    N --> O[Record Payment]
    O --> P{Fully Paid?}
    P -->|No| N
    P -->|Yes| Q[Close Invoice]
```

### Detailed Workflow Steps

#### 1. Pre-Invoice Stage
- **Check billing balances** using balance endpoints
- Identify unbilled work from projects, deliveries, or orders
- Verify customer information (companies, contacts)

#### 2. Invoice Preparation
- **Get cart data**: `GET /invoices/cart`
- **Get default template**: `GET /invoices/default`
- Review billable items and amounts

#### 3. Invoice Creation
- **Create invoice**: `POST /invoices`
- System assigns invoice ID and reference number
- Initial state set based on configuration

#### 4. Invoice Management
- **Update information**: `PUT /invoices/{id}/information`
- **Adjust amounts/items**: `PUT /invoices/{id}/adjust`
- **Add flags**: Attach categorization flags
- **Add tasks**: Track follow-up actions

#### 5. Invoice Validation
- **Check properties**: `GET /invoices/{id}/check`
- Verify e-invoicing compliance if required
- Validate all required fields

#### 6. Invoice Distribution
- **Download document**: `GET /invoices/{id}/download`
- **Preview**: `GET /invoices/{id}/preview`
- **Send by email**: `POST /invoices/{id}/send`
- **Export to download center** for batch processing

#### 7. Payment Processing
- **Track payment status** using invoice state
- **Record payments**: `POST /payments`
- **Update payment dates** in invoice information
- Monitor via `expectedPaymentDate` and `performedPaymentDate`

#### 8. Invoice Closing
- Mark invoice as closed when fully paid
- Archive or export for accounting
- Generate credit notes if needed (using `creditNote` flag)

---

## Common Query Parameters

### Pagination

All search endpoints support pagination:

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `page` | number | 1 | ≥ 1 | Current page number |
| `maxResults` | number | 30 | 1-500 | Results per page |

### Sorting

Most search endpoints support sorting:

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `order` | string | `asc`, `desc` | Sort order (default: `asc`) |
| `sort` | string[] | varies by endpoint | Column name(s) to sort by |

### Date Filtering

Standard date parameters:

| Parameter | Format | Example | Description |
|-----------|--------|---------|-------------|
| `startDate` | `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS` | `2025-01-01` | Period start |
| `endDate` | `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS` | `2025-12-31` | Period end |
| `period` | string | `created`, `updated` | Date field to filter on |

### Dynamic Period Filters

Pre-defined period shortcuts:

**Current Periods:**
- `today`, `thisWeek`, `thisMonth`, `thisTrimester`, `thisSemester`, `thisYear`, `thisFiscalYear`

**Past Periods:**
- `yesterday`, `lastWeek`, `lastMonth`, `lastTrimester`, `lastSemester`, `lastYear`, `lastFiscalYear`

**Future Periods:**
- `tomorrow`, `nextWeek`, `nextMonth`, `nextTrimester`, `nextSemester`, `nextYear`, `nextFiscalYear`

**Special:**
- `untilToday` - From beginning until today
- `lastCustomPeriod` - Custom duration before now (requires `periodDynamicParameters`)
- `nextCustomPeriod` - Custom duration after now (requires `periodDynamicParameters`)

**Custom Period Parameters:**
```
periodDynamicParameters=3,months
```
Format: `{duration},{unit}` where unit is `days`, `weeks`, `months`, `trimesters`, `semesters`, `years`

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 401 | Unauthorized | Invalid or missing authentication |
| 403 | Forbidden | Authenticated but insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 422 | Unprocessable Entity | Validation error - check request body |
| 500 | Internal Server Error | Server-side error occurred |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

Error responses typically include:
- HTTP status code
- Error message describing the issue
- Validation details (for 422 errors)

### Best Practices

1. **Always handle authentication errors** (401) - check credentials and API access settings
2. **Validate input before sending** to avoid 422 errors
3. **Implement retry logic** for 503 errors with exponential backoff
4. **Check permissions** if receiving 403 errors
5. **Log 500 errors** and contact support if persistent

---

## Dictionary References

Several parameters reference dictionary values that should be retrieved via:

| Dictionary Endpoint | Parameter Usage |
|---------------------|-----------------|
| `/api/rest/application/dictionary/setting.currency` | `amountCurrency` |
| `/api/rest/application/dictionary/setting.paymentMethod` | `paymentMethods` |
| `/api/rest/application/dictionary/setting.typeOf.project` | `projectTypes` |
| `/api/rest/application/dictionary/setting.state.invoice` | `states` |

Use dictionary endpoints to get valid ID values for filtering and creation.

---

## Integration Examples

### Example 1: Search Recent Invoices

```http
GET /api/invoices?periodDynamic=thisMonth&maxResults=50&order=desc&sort=date
Authorization: Basic {credentials}
```

### Example 2: Find Unpaid Invoices

```http
GET /api/invoices?closed=false&period=expectedPayment&startDate=2025-01-01&endDate=2025-12-31
Authorization: Basic {credentials}
```

### Example 3: Export Invoices to CSV

```http
GET /api/invoices.csv?periodDynamic=lastMonth&encoding=UTF-8&extractType=detailed
Authorization: Basic {credentials}
```

### Example 4: Get Invoice Details

```http
GET /api/invoices/12345
Authorization: Basic {credentials}
```

### Example 5: Send Invoice by Email

```http
POST /api/invoices/12345/send
Authorization: Basic {credentials}
Content-Type: application/json

{
  "recipients": ["customer@example.com"],
  "subject": "Your Invoice #12345",
  "message": "Please find attached your invoice."
}
```

---

## Additional Resources

- **API Documentation:** https://doc.boondmanager.com/api-externe/
- **Database Schema:** Available at `/bddboondmanager/` paths in documentation
- **Error Reference:** See "Errors 422" section in main documentation
- **How-to Guides:** See "How to" section in main documentation

---

## Notes and Considerations

### Performance
- Use `maxResults` parameter to control response size
- Leverage pagination for large datasets
- Use specific `columns` parameter to reduce payload size
- Consider CSV export for bulk data extraction

### Data Consistency
- Invoice states are managed by the system
- Some fields may be read-only depending on invoice state
- Check invoice rights before attempting updates
- Validate against business rules using `/check` endpoint

### E-Invoicing
- Check e-invoicing requirements for your jurisdiction
- Use `/e-invoicing/schemes` to get compliance information
- Validate invoices before submission
- Export in CII format if required

### Security
- Store credentials securely
- Use HTTPS for all API calls
- Enable API access only for authorized users
- Regularly rotate authentication credentials
- Monitor API usage for anomalies

---

**Document Version:** 1.0
**Last Updated:** 2025-10-09
**Research Method:** Direct API documentation exploration via Playwright browser automation
