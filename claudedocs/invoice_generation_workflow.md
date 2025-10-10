# Invoice Generation Workflow - Step-by-Step Guide

**Scenario:** Generate an invoice for a client based on days worked by a worker and the total monthly cost.

**Input Data:**
- Client information
- Worker identifier
- Days worked in the period
- Total cost calculated for the month

---

## Prerequisites

Before starting, ensure you have:
- ✅ Valid API credentials with invoice creation permissions
- ✅ Client company exists in BoondManager
- ✅ Project/Order exists for the work performed
- ✅ Worker resource is registered in the system

---

## Step-by-Step Invoice Generation Process

### Step 1: Verify Client Exists

**Endpoint:** `GET /api/companies`

**Purpose:** Confirm the client company exists and retrieve its ID.

**Request:**
```http
GET /api/companies?keywords=CSOC{clientName}
Authorization: Basic {credentials}
```

**Action:**
- Search by company name or identifier
- Note the `id` field from the response (e.g., `companyId: 12345`)
- If client doesn't exist, create it first using `POST /companies`

**What you need:** `companyId`

---

### Step 2: Find or Verify the Project

**Endpoint:** `GET /api/projects`

**Purpose:** Locate the project associated with this work.

**Request:**
```http
GET /api/projects?keywords=PRJ{projectReference}&companies={companyId}
Authorization: Basic {credentials}
```

**Alternative - Search Orders:**
```http
GET /api/orders?keywords=BDC{orderReference}&companies={companyId}
Authorization: Basic {credentials}
```

**Action:**
- Search for the project or order related to the client
- Note the project/order `id` (e.g., `projectId: 67890` or `orderId: 54321`)
- Verify the project is active and billable

**What you need:** `projectId` or `orderId`

---

### Step 3: Check Billing Balance (Optional but Recommended)

**Endpoint:** `GET /api/billing-projects-balance`

**Purpose:** Verify unbilled work exists for this project.

**Request:**
```http
GET /api/billing-projects-balance?projects={projectId}
Authorization: Basic {credentials}
```

**Action:**
- Review the billing balance to ensure there's unbilled work
- Confirm the amounts match your calculated total
- This helps avoid duplicate invoicing

**What you verify:** Unbilled amount and work items

---

### Step 4: Get Default Invoice Template

**Endpoint:** `GET /api/invoices/default`

**Purpose:** Retrieve the default invoice structure and required fields.

**Request:**
```http
GET /api/invoices/default
Authorization: Basic {credentials}
```

**Action:**
- Review the default invoice structure
- Note required fields (currency, payment terms, etc.)
- Identify any mandatory custom fields

**What you learn:** Required invoice fields and structure

---

### Step 5: Prepare Invoice Data

**Data Structure Preparation:**

Based on your input data, prepare the invoice payload:

```json
{
  "information": {
    "order": {
      "id": 54321
    },
    "project": {
      "id": 67890
    },
    "company": {
      "id": 12345
    },
    "date": "2025-10-31",
    "reference": "INV-2025-10-001",
    "startDate": "2025-10-01",
    "endDate": "2025-10-31",
    "expectedPaymentDate": "2025-11-30",
    "paymentMethod": {
      "id": 1
    },
    "currency": {
      "id": 1
    }
  },
  "billableItems": [
    {
      "description": "Consulting services - Worker Name",
      "quantity": 20,
      "unit": "days",
      "unitPriceExcludingTax": 500,
      "totalExcludingTax": 10000,
      "vatRate": 20,
      "totalIncludingTax": 12000
    }
  ]
}
```

**Field Mapping:**
- `quantity`: Days worked (from your input: 20 days)
- `unitPriceExcludingTax`: Cost per day (total cost / days worked)
- `totalExcludingTax`: Total cost for the month (from your input)
- `totalIncludingTax`: Total including VAT/tax

---

### Step 6: Create the Invoice

**Endpoint:** `POST /api/invoices`

**Purpose:** Create the invoice in the system.

**Request:**
```http
POST /api/invoices
Authorization: Basic {credentials}
Content-Type: application/json

{
  "information": {
    "order": {"id": 54321},
    "project": {"id": 67890},
    "company": {"id": 12345},
    "date": "2025-10-31",
    "startDate": "2025-10-01",
    "endDate": "2025-10-31",
    "expectedPaymentDate": "2025-11-30",
    "paymentMethod": {"id": 1},
    "currency": {"id": 1}
  },
  "billableItems": [
    {
      "description": "Consulting services - [Worker Name]",
      "quantity": 20,
      "unit": "days",
      "unitPriceExcludingTax": 500,
      "totalExcludingTax": 10000,
      "vatRate": 20,
      "totalIncludingTax": 12000
    }
  ]
}
```

**Action:**
- Submit the invoice creation request
- Note the returned `invoiceId` from the response (e.g., `invoiceId: 98765`)
- Verify the response status is 200 or 201

**What you get:** New `invoiceId`

---

### Step 7: Verify Invoice Details

**Endpoint:** `GET /api/invoices/{invoiceId}`

**Purpose:** Confirm the invoice was created correctly.

**Request:**
```http
GET /api/invoices/98765
Authorization: Basic {credentials}
```

**Action:**
- Review all invoice fields
- Verify amounts are correct
- Check invoice state/status
- Confirm billable items are accurate

**What you verify:** Invoice accuracy and completeness

---

### Step 8: Get Billable Items Details (Optional)

**Endpoint:** `GET /api/invoices/{invoiceId}/billable-items`

**Purpose:** Review detailed billable items breakdown.

**Request:**
```http
GET /api/invoices/98765/billable-items
Authorization: Basic {credentials}
```

**Action:**
- Verify line items match your input
- Check calculations (quantity × unit price)
- Confirm tax calculations

**What you verify:** Line item accuracy

---

### Step 9: Adjust Invoice if Needed (Optional)

**Endpoint:** `PUT /api/invoices/{invoiceId}/adjust`

**Purpose:** Make corrections to amounts or items if needed.

**Request:**
```http
PUT /api/invoices/98765/adjust
Authorization: Basic {credentials}
Content-Type: application/json

{
  "billableItems": [
    {
      "id": 123,
      "quantity": 22,
      "totalExcludingTax": 11000,
      "totalIncludingTax": 13200
    }
  ]
}
```

**Action:**
- Adjust quantities, amounts, or descriptions
- Update tax calculations if needed
- Re-verify totals

**When to use:** Corrections needed after initial creation

---

### Step 10: Update Invoice Information (Optional)

**Endpoint:** `PUT /api/invoices/{invoiceId}/information`

**Purpose:** Update invoice metadata (dates, references, etc.).

**Request:**
```http
PUT /api/invoices/98765/information
Authorization: Basic {credentials}
Content-Type: application/json

{
  "reference": "INV-2025-10-001-REVISED",
  "expectedPaymentDate": "2025-12-15",
  "notes": "Invoice for October 2025 consulting services"
}
```

**Action:**
- Update payment dates if needed
- Add notes or comments
- Change references if required

**When to use:** Metadata updates needed

---

### Step 11: Check Invoice Compliance (E-Invoicing)

**Endpoint:** `GET /api/invoices/{invoiceId}/check`

**Purpose:** Validate invoice meets compliance requirements.

**Request:**
```http
GET /api/invoices/98765/check
Authorization: Basic {credentials}
```

**Action:**
- Verify e-invoicing compliance (if required)
- Check for validation errors
- Ensure all required fields are present

**What you verify:** Compliance and validation status

---

### Step 12: Preview Invoice Document

**Endpoint:** `GET /api/invoices/{invoiceId}/preview`

**Purpose:** Review the formatted invoice before sending.

**Request:**
```http
GET /api/invoices/98765/preview
Authorization: Basic {credentials}
```

**Action:**
- Review the PDF/document preview
- Verify formatting and layout
- Check all information is displayed correctly

**What you see:** Visual invoice preview

---

### Step 13: Download Invoice Document

**Endpoint:** `GET /api/invoices/{invoiceId}/download`

**Purpose:** Download the finalized invoice document.

**Request:**
```http
GET /api/invoices/98765/download
Authorization: Basic {credentials}
```

**Action:**
- Download the invoice PDF
- Save to local system or document management
- Archive for records

**What you get:** Invoice PDF file

---

### Step 14: Send Invoice to Client

**Endpoint:** `POST /api/invoices/{invoiceId}/send`

**Purpose:** Email the invoice to the client.

**Request:**
```http
POST /api/invoices/98765/send
Authorization: Basic {credentials}
Content-Type: application/json

{
  "recipients": [
    "client.contact@company.com",
    "accounting@company.com"
  ],
  "subject": "Invoice #INV-2025-10-001 for October Services",
  "message": "Dear Client,\n\nPlease find attached invoice #INV-2025-10-001 for consulting services provided during October 2025.\n\nTotal Amount: €12,000 (including VAT)\nDue Date: November 30, 2025\n\nPayment instructions are included in the invoice.\n\nBest regards"
}
```

**Action:**
- Specify recipient email addresses
- Customize subject line
- Add personalized message
- System will attach the invoice PDF

**What happens:** Invoice is emailed to client

---

### Step 15: Track Payment (Future)

**When payment is received:**

#### Record Payment
**Endpoint:** `POST /api/payments`

**Request:**
```http
POST /api/payments
Authorization: Basic {credentials}
Content-Type: application/json

{
  "invoice": {"id": 98765},
  "amount": 12000,
  "date": "2025-11-25",
  "paymentMethod": {"id": 1},
  "reference": "BANK-TRANSFER-123456"
}
```

#### Update Invoice Payment Date
**Endpoint:** `PUT /api/invoices/{invoiceId}/information`

**Request:**
```http
PUT /api/invoices/98765/information
Authorization: Basic {credentials}
Content-Type: application/json

{
  "performedPaymentDate": "2025-11-25"
}
```

**Action:**
- Record payment details
- Update invoice status
- Mark as fully paid if complete

---

## Quick Reference Workflow

```
1. GET /companies → Find client (companyId)
2. GET /projects or /orders → Find project (projectId/orderId)
3. GET /billing-projects-balance → Verify unbilled work (optional)
4. GET /invoices/default → Get template structure
5. Prepare invoice JSON with your data
6. POST /invoices → Create invoice (returns invoiceId)
7. GET /invoices/{id} → Verify invoice
8. PUT /invoices/{id}/adjust → Adjust if needed (optional)
9. GET /invoices/{id}/check → Validate compliance
10. GET /invoices/{id}/preview → Review document
11. GET /invoices/{id}/download → Download PDF
12. POST /invoices/{id}/send → Email to client
13. POST /payments → Record payment when received (future)
```

---

## Data Mapping Guide

### Your Input → API Fields

| Your Data | API Field | Example Value |
|-----------|-----------|---------------|
| Client name | `company.id` | Retrieved from Step 1 |
| Worker name | `billableItems[].description` | "Consulting - John Doe" |
| Days worked | `billableItems[].quantity` | 20 |
| Unit | `billableItems[].unit` | "days" |
| Total monthly cost | `billableItems[].totalExcludingTax` | 10000 |
| Cost per day | `billableItems[].unitPriceExcludingTax` | totalCost / daysWorked |
| Invoice date | `information.date` | "2025-10-31" |
| Period start | `information.startDate` | "2025-10-01" |
| Period end | `information.endDate` | "2025-10-31" |
| Payment due date | `information.expectedPaymentDate` | "2025-11-30" |

---

## Common Issues and Solutions

### Issue 1: Company Not Found
**Solution:** Create the company first using `POST /api/companies`

### Issue 2: No Active Project
**Solution:** Create a project using `POST /api/projects` or link to existing order

### Issue 3: Invoice Creation Fails (422 Error)
**Solutions:**
- Verify all required fields are present
- Check dictionary values (currency, payment method IDs)
- Ensure project/order is in correct state
- Validate date formats

### Issue 4: VAT/Tax Calculation Issues
**Solution:**
- Get tax rates from `/api/rest/application/dictionary`
- Calculate: `totalIncludingTax = totalExcludingTax * (1 + vatRate/100)`

### Issue 5: E-Invoicing Validation Fails
**Solution:**
- Check `/api/e-invoicing/schemes` for requirements
- Use `/api/invoices/{id}/check` to identify missing fields
- Ensure compliance with local regulations

---

## Required Dictionary Values

Before creating invoices, retrieve these dictionary values:

### Currency IDs
```http
GET /api/rest/application/dictionary/setting.currency
```

### Payment Method IDs
```http
GET /api/rest/application/dictionary/setting.paymentMethod
```

### Invoice State IDs
```http
GET /api/rest/application/dictionary/setting.state.invoice
```

### VAT Rates
```http
GET /api/rest/application/dictionary/setting.vat
```

---

## Example: Complete Invoice Creation Script

```bash
#!/bin/bash

# Configuration
API_BASE="https://ui.boondmanager.com/api/1.0"
AUTH="Basic dGVzdEBkb21haW4udGxkOnRlc3Q="

# Input data
CLIENT_NAME="Acme Corporation"
WORKER_NAME="John Doe"
DAYS_WORKED=20
TOTAL_COST=10000
INVOICE_MONTH="2025-10"

# Step 1: Find client
COMPANY_ID=$(curl -s -H "Authorization: $AUTH" \
  "$API_BASE/companies?keywords=$CLIENT_NAME" | jq -r '.data[0].id')

echo "Client ID: $COMPANY_ID"

# Step 2: Find project (assuming you have project reference)
PROJECT_ID=$(curl -s -H "Authorization: $AUTH" \
  "$API_BASE/projects?companies=$COMPANY_ID&maxResults=1" | jq -r '.data[0].id')

echo "Project ID: $PROJECT_ID"

# Step 3: Create invoice
INVOICE_DATA='{
  "information": {
    "company": {"id": '$COMPANY_ID'},
    "project": {"id": '$PROJECT_ID'},
    "date": "'$INVOICE_MONTH'-31",
    "startDate": "'$INVOICE_MONTH'-01",
    "endDate": "'$INVOICE_MONTH'-31",
    "paymentMethod": {"id": 1},
    "currency": {"id": 1}
  },
  "billableItems": [{
    "description": "Consulting services - '$WORKER_NAME'",
    "quantity": '$DAYS_WORKED',
    "unit": "days",
    "unitPriceExcludingTax": '$(($TOTAL_COST / $DAYS_WORKED))',
    "totalExcludingTax": '$TOTAL_COST',
    "vatRate": 20,
    "totalIncludingTax": '$(($TOTAL_COST * 120 / 100))'
  }]
}'

INVOICE_ID=$(curl -s -X POST \
  -H "Authorization: $AUTH" \
  -H "Content-Type: application/json" \
  -d "$INVOICE_DATA" \
  "$API_BASE/invoices" | jq -r '.id')

echo "Invoice created: $INVOICE_ID"

# Step 4: Download invoice
curl -H "Authorization: $AUTH" \
  -o "invoice_${INVOICE_ID}.pdf" \
  "$API_BASE/invoices/$INVOICE_ID/download"

echo "Invoice downloaded: invoice_${INVOICE_ID}.pdf"
```

---

## Best Practices

1. ✅ **Always verify client and project exist** before invoice creation
2. ✅ **Check billing balance** to avoid duplicate invoicing
3. ✅ **Validate calculations** (days × rate = total)
4. ✅ **Preview before sending** to catch errors
5. ✅ **Keep invoice references** for tracking and reconciliation
6. ✅ **Log all API calls** for audit trail
7. ✅ **Handle errors gracefully** with proper error messages
8. ✅ **Test with small amounts** before production use

---

## Security Considerations

- 🔒 Store API credentials securely (environment variables, vault)
- 🔒 Use HTTPS for all API calls
- 🔒 Validate input data before API submission
- 🔒 Log invoice creation events for audit
- 🔒 Implement rate limiting to avoid API abuse
- 🔒 Never expose invoice IDs publicly

---

**Document Version:** 1.0
**Last Updated:** 2025-10-09
**Related Documentation:** `boondmanager_invoicing_api_documentation.md`
