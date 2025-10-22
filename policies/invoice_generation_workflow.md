# Invoice Generation Workflow

## Overview

This policy defines the complete workflow for generating, verifying, and managing invoices in the BoondManager multi-agent system. Invoice generation is a critical business operation that requires validated timesheet data, proper verification, and careful coordination between the Main Orchestrator and the Invoice Agent.

**Key Principle**: Invoice generation is never a single-step operation. It always involves preparation → generation → verification → reconciliation.

## When to Generate Invoices

### Prerequisites Checklist

Before initiating invoice generation, verify ALL of the following:

✅ **Timesheet Validation Complete**
- All consultant timesheets for the billing period are validated
- No pending discrepancies or unresolved issues
- Timesheet totals match client confirmation emails

✅ **Project Data Verified**
- Project ID is confirmed and active
- Billing period (month) is correctly specified
- Delivery and order relationships are established

✅ **Business Rules Satisfied**
- Billing period has closed (month has ended)
- Required approvals are in place
- No outstanding validation flags

✅ **Client Confirmation Received**
- Client has confirmed hours worked
- Any discrepancies have been resolved
- Email confirmation is documented

### Common Triggers

Invoice generation is typically triggered by:

1. **Monthly Billing Cycle**: End of month after timesheet validation
2. **Client Confirmation**: After receiving and validating client email confirmation
3. **Manual Request**: Explicit request from user after all prerequisites are met
4. **Automated Workflow**: As final step in timesheet validation workflow

## Complete Invoice Generation Workflow

### Phase 1: Preparation

**Step 1: Query and Verify Project Data**

```
MANDATORY QUERIES:
1. Confirm project existence and status
2. Verify billing period (month/year)
3. Identify all consultants/resources for the project
4. Get delivery and order IDs
5. Confirm company (client) ID
```

**Delegation Pattern**:
```
Delegate to Query Agent:
"For project '{project_name}' (ID: {project_id}), confirm:
1. Project is active and exists
2. All resources assigned for {month} {year}
3. Related delivery IDs and order IDs
4. Client company ID

Return structured data with all IDs needed for invoice generation."
```

**Step 2: Verify Timesheet Validation**

```
MANDATORY CHECKS:
1. All timesheets for the period are validated
2. No pending validation errors or warnings
3. Timesheet totals match client confirmation
4. Any discrepancies have been resolved
```

**Query Pattern**:
```
Delegate to Validation Agent:
"Verify that all timesheets for project '{project_name}'
(ID: {project_id}) in {month} {year} are validated and
have no pending issues."
```

### Phase 2: Invoice Generation

**Step 3: Generate Invoice**

Use the Invoice Agent with complete context:

**Delegation Pattern**:
```
Delegate to Invoice Agent:
"Generate invoices for project {project_id} ({project_name})
for billing period {month} {year}.

Context:
- Project ID: {project_id}
- Billing month: YYYY-MM format
- [Optional] Delivery ID: {delivery_id}
- [Optional] Resource ID: {resource_id}
- [Optional] Company ID: {company_id}

After generation, retrieve and verify all generated invoices."
```

**Critical Rules**:
- ⚠️ **NEVER** stop after calling generate_invoice tool
- ⚠️ **ALWAYS** follow with search_invoices to retrieve generated invoices
- ⚠️ **ALWAYS** provide detailed recap with invoice references and amounts
- Invoice Agent handles the verification workflow automatically

### Phase 3: Verification

**Step 4: Verify Generated Invoices**

The Invoice Agent automatically performs verification, but the orchestrator should:

```
MANDATORY VERIFICATION:
1. Confirm invoice count matches expected (1 invoice per delivery/order typically)
2. Verify invoice amounts match timesheet totals
3. Check invoice references are generated correctly
4. Confirm billing period dates are correct
5. Validate relationships (project, order, company) are correct
```

**Example Verification Pattern**:
```
Expected Output from Invoice Agent:
"Generated 2 invoices for project 6 (September 2025):
 • FACT-2025-005 (2025-09-30): 7 860€ (excl. tax)
   - Related to order 11, company 5
   - Covers period: 2025-09-01 to 2025-09-30
 • FACT-2025-006 (2025-09-30): 14 432€ (excl. tax)
   - Related to order 12, company 5
   - Covers period: 2025-09-01 to 2025-09-30
 Total invoiced: 22 292€"
```

**Step 5: Cross-Reference with Timesheet Data**

Compare generated invoice amounts with original timesheet data:

```
RECONCILIATION CHECKLIST:
□ Invoice total matches sum of validated timesheets
□ Each consultant's work is properly billed
□ Day counts align with timesheet records
□ Rates applied correctly (day rate × days worked)
□ Tax calculations are correct
```

### Phase 4: Reporting and Documentation

**Step 6: Generate Summary Report**

Provide comprehensive summary to user:

**Report Format**:
```
INVOICE GENERATION SUMMARY
==========================

Project: {project_name} (ID: {project_id})
Billing Period: {month} {year}
Client: {company_name} (ID: {company_id})

GENERATED INVOICES:
-------------------
1. Invoice {reference_1}
   - Date: {invoice_date}
   - Amount: {amount_excl_tax}€ (excl. tax)
   - Amount: {amount_incl_tax}€ (incl. tax)
   - Status: {state}
   - Order: {order_id}
   - Delivery: {delivery_id}

2. Invoice {reference_2}
   [...]

TOTALS:
-------
Total Invoiced (excl. tax): {total_excl}€
Total Invoiced (incl. tax): {total_incl}€
Invoice Count: {count}

VERIFICATION:
-------------
✅ Amounts match validated timesheets
✅ All consultants billed correctly
✅ Billing period correct
✅ Client relationships verified
```

## Delegation Best Practices

### When to Use Invoice Agent

**Use Invoice Agent for**:
- ✅ Generating new invoices
- ✅ Searching for existing invoices
- ✅ Retrieving invoice details and line items
- ✅ Calculating invoice totals and aggregations
- ✅ Verifying invoice data against expected amounts

**Use Query Agent for**:
- ✅ Looking up project details (before invoice generation)
- ✅ Getting timesheet data for comparison
- ✅ Retrieving consultant/resource information
- ✅ Verifying project-related data

**Use Validation Agent for**:
- ✅ Confirming timesheet validation status
- ✅ Checking for validation warnings/errors
- ✅ Ensuring all prerequisites are met

### Crafting Effective Prompts for Invoice Agent

**Principle**: Invoice Agent is a ChatGPT-based agent. Provide complete, explicit context.

✅ **CORRECT Delegation**:
```
"Generate invoices for project 8 ('Modernisation Ligne Production')
for September 2025 (billing period 2025-09).

After generation, retrieve all generated invoices for this project
and provide:
1. Invoice references and IDs
2. Invoice dates
3. Amounts (excl. tax and incl. tax)
4. Related order and delivery IDs
5. Total amount invoiced

Verify the generated invoices and provide a detailed summary."
```

❌ **INCORRECT Delegation**:
```
"Generate invoices for project 8 in September"
```

**Why incorrect**:
- Missing project name context
- Unclear billing period format (2025-09 vs "September")
- No verification instructions
- No required output format

### Common Invoice Agent Queries

**Pattern 1: Invoice Generation**
```
"Generate invoices for project {id} ('{name}') for {month} {year}.
After generation, verify and provide detailed recap with references,
amounts, and totals."
```

**Pattern 2: Invoice Search and Total**
```
"Find all invoices for company {id} ('{company_name}') and calculate
their total amount (excluding tax). List each invoice with reference,
date, and amount."
```

**Pattern 3: Invoice Details**
```
"Get detailed information for invoice {id} including all line items
with quantities, unit prices, and totals. Show tax breakdown."
```

**Pattern 4: Invoice Verification**
```
"Retrieve all invoices for project {id} in {month} {year} and verify:
1. Total amount matches {expected_amount}€
2. Invoice count is {expected_count}
3. All consultants are billed: {consultant_list}
Provide comparison table."
```

## Business Rules and Constraints

### Timing Requirements

**Invoice Generation Windows**:
- Invoices should be generated AFTER month-end
- Timesheets must be validated BEFORE invoice generation
- Client confirmation should be received and reconciled BEFORE generation

**Deadlines**:
- Invoices typically generated within first 5 business days of following month
- Rush invoices may be generated earlier with proper authorization

### Required Approvals

Before generating invoices, confirm:

1. **Timesheet Approval**: All timesheets validated and approved
2. **Manager Sign-off**: Project manager has approved billing
3. **Client Confirmation**: Client has confirmed hours and amounts (via email)
4. **Financial Approval**: Any special billing arrangements are documented

### Multiple Projects and Deliveries

**Scenario**: Client has multiple projects or deliveries

**Approach**:
1. Generate invoices for each project/delivery separately
2. Delegate to Invoice Agent with batch requests:

```
Delegate to Invoice Agent (batch):
"Generate invoices for the following projects in September 2025:
1. Project 8 ('Modernisation Ligne Production')
2. Project 12 ('Digital Transformation')
3. Project 15 ('Cloud Migration')

For each project:
- Generate invoices for billing period 2025-09
- Verify generated invoices
- Provide individual summaries

Then provide consolidated summary with total amount across all projects."
```

### Client-Specific Requirements

Some clients may have special invoicing rules:

**Examples**:
- **Consolidated Invoicing**: Multiple projects → single invoice
- **Split Billing**: Different cost centers → separate invoices
- **Monthly Caps**: Maximum billing amount per month
- **Milestone-Based**: Invoices tied to deliverables, not time

**Approach**: Query client-specific rules before generation

```
Recommended: Store client-specific invoicing rules in policy documents
or configuration, retrievable via `retrieve_policy("Client X invoicing rules")`
```

## Error Handling

### Common Errors and Solutions

#### Error: "Cannot generate invoice - timesheet validation pending"

**Cause**: Timesheets for the billing period are not validated

**Solution**:
1. Delegate to Validation Agent to check validation status
2. If validation incomplete, complete validation workflow first
3. Retry invoice generation after validation

**Recovery Pattern**:
```
Delegate to Validation Agent:
"Check validation status for all timesheets on project {id}
for {month} {year}. Report any pending validations."

→ If pending validations exist:
"Validate all pending timesheets for project {id} in {month} {year}."

→ After validation complete:
Retry invoice generation
```

#### Error: "Project ID not found"

**Cause**: Invalid or incorrect project ID

**Solution**:
1. Delegate to Query Agent to search for project by name
2. Verify correct project ID
3. Retry with correct ID

**Recovery Pattern**:
```
Delegate to Query Agent:
"Search for project with name '{project_name}' and return
its ID, status, and basic information."

→ Use returned project ID for invoice generation
```

#### Error: "No delivery or order found for project"

**Cause**: Project missing required billing relationships

**Solution**:
1. Query project structure to understand setup
2. Report to user that project configuration is incomplete
3. Escalate to human for project setup fix

**Escalation Pattern**:
```
"Cannot generate invoice for project {id}. The project is missing
required billing relationships (delivery or order).

This requires manual intervention to:
1. Create or link delivery in BoondManager
2. Create or link order for billing
3. Configure billing relationships

Please complete project setup before generating invoices."
```

#### Error: "Invoice generation returned success but no invoices found"

**Cause**: Generation succeeded but invoices not created due to missing data

**Solution**:
1. Check `canGenerateInvoices` field in generation response
2. Read `productionComments` for details on missing data
3. Report specific missing data to user
4. Escalate for data completion

**Diagnostic Pattern**:
```
After generate_invoice call, check response:

IF attributes.canGenerateInvoices == false:
  "Invoice generation blocked. Reason: {productionComments}

  Required actions:
  - {specific missing data from comments}

  Please complete the required data and retry."
```

#### Error: "Generated invoice amount doesn't match expected"

**Cause**: Mismatch between timesheet data and invoice amount

**Solution**:
1. Retrieve invoice details to see line items
2. Compare with timesheet data
3. Identify discrepancy source (rate, days, tax calculation)
4. Report discrepancy to user for review

**Analysis Pattern**:
```
Delegate to Invoice Agent:
"Get detailed information for invoice {id} including all line items.
Calculate total from line items."

Delegate to Query Agent:
"Get timesheet totals for project {id} in {month} {year}.
Calculate expected invoice amount."

Compare and report:
"DISCREPANCY DETECTED:
Invoice Amount: {invoice_amount}€
Expected (from timesheets): {expected_amount}€
Difference: {difference}€

Possible causes:
- Incorrect day rates applied
- Missing timesheet entries
- Tax calculation error
- Multiple invoices generated (check for others)

Recommended action: Manual review required."
```

### When to Escalate to Humans

Escalate in the following situations:

🚨 **Immediate Escalation Required**:
1. Generated invoice amount differs significantly from expected (>10% variance)
2. Invoice generation fails due to missing project configuration
3. Unable to verify generated invoices (not found in system)
4. Client-specific rules conflict with standard workflow
5. Multiple generation attempts fail with same error
6. Timesheet validation shows unresolvable discrepancies

⚠️ **Consider Escalation**:
1. First-time invoice generation for new client
2. Complex billing scenarios (multiple projects, split billing)
3. Invoice generation during non-standard periods
4. Special client requests or billing arrangements
5. Discrepancy between client confirmation and system data

✅ **No Escalation Needed**:
1. Standard monthly invoicing after validation complete
2. Retry after resolving data issues
3. Known issues with documented solutions
4. Minor formatting or reference issues

### Escalation Communication Pattern

When escalating, provide complete context:

```
🚨 ESCALATION REQUIRED: Invoice Generation Issue

Project: {project_name} (ID: {project_id})
Billing Period: {month} {year}
Client: {company_name}

ISSUE:
{clear description of the problem}

ATTEMPTED SOLUTIONS:
1. {action taken}
   Result: {outcome}
2. {action taken}
   Result: {outcome}

CURRENT STATE:
- Timesheets: {validation status}
- Generated Invoices: {count and status}
- Expected Amount: {amount}€
- Actual Amount: {amount}€

REQUIRED ACTION:
{specific action needed from human}

IMPACT:
{business impact - billing delay, client communication needed, etc.}
```

## Data Consistency Checks

### Pre-Generation Validation

Before generating invoices, verify data consistency:

**Checklist**:
```
□ Project exists and is active
□ Billing period is closed (month has ended)
□ All timesheet entries for period are present
□ Timesheet validation is complete (no pending validations)
□ Client confirmation received and reconciled
□ No conflicting invoices already exist for the period
□ Project has required relationships (delivery, order, company)
□ Consultant/resource assignments are correct
```

**Validation Query Pattern**:
```
Delegate to Query Agent:
"Perform pre-invoice validation for project {id} in {month} {year}:
1. Confirm project is active
2. List all resources with timesheet entries
3. Verify delivery and order relationships exist
4. Check for any existing invoices for this period

Return structured validation report."
```

### Post-Generation Verification

After generating invoices, verify consistency:

**Checklist**:
```
□ Invoice count matches expected (typically 1 per delivery/order)
□ Invoice dates are correct (usually last day of billing period)
□ Invoice amounts match timesheet totals
□ All consultants are represented in invoicing
□ Tax calculations are correct
□ Invoice relationships (project, order, company) are correct
□ Invoice state is appropriate (draft or validated)
```

**Verification Query Pattern**:
```
Delegate to Invoice Agent:
"Verify generated invoices for project {id}:
1. List all invoices with references, dates, amounts
2. Calculate total amount (excl. tax)
3. Count invoices
4. Verify relationships (project, order, company)
5. Check invoice states

Compare with expected:
- Expected total: {amount}€
- Expected count: {count}
- Expected consultants: {list}

Report any discrepancies."
```

## Integration with Other Workflows

### Timesheet Validation → Invoice Generation Flow

**Complete End-to-End Workflow**:

```
Phase 1: Receive Client Confirmation Email
└→ Delegate to Emailing Agent: Read email, extract worker hours

Phase 2: Query BoondManager Data
└→ Delegate to Query Agent: Get timesheet data for all workers

Phase 3: Validate Timesheets
├→ Compare email data with BoondManager data
├→ Delegate to Validation Agent: Validate when matching
└→ Delegate to Emailing Agent: Handle discrepancies when not matching

Phase 4: Generate Invoices (THIS POLICY)
├→ Verify prerequisites (timesheets validated)
├→ Delegate to Invoice Agent: Generate invoices
├→ Delegate to Invoice Agent: Verify generated invoices
└→ Report summary to user

Phase 5: Post-Invoice Actions
├→ Archive email confirmation
├→ Update project billing status
└→ Prepare invoice delivery to client (if applicable)
```

### Reference to Other Policies

- **For delegation guidance**: See `delegation_best_practices.md`
- **For error handling**: See `error_handling_protocols.md`
- **For timesheet validation**: See `timesheet_validation.md`
- **For prompt engineering**: See `orchestrator_prompt_engineering.md`

## Examples and Templates

### Example 1: Standard Monthly Invoice Generation

**User Request**: "Generate invoices for September 2025 for project Modernisation Ligne Production"

**Orchestrator Workflow**:

```
Step 1: Query Project Data
--------------------------
Delegate to Query Agent:
"Search for project named 'Modernisation Ligne Production' and return:
- Project ID
- Project status
- Company (client) ID and name
- Delivery IDs
- Order IDs
- List of assigned resources for September 2025"

Response received:
- Project ID: 8
- Status: Active
- Company: 5 (Roche Diagnostics)
- Delivery: 1
- Order: 11
- Resources: Elodie LEGUAY (ID: 28), Didier GEIG (ID: 32)

Step 2: Verify Timesheet Validation
------------------------------------
Delegate to Validation Agent:
"Confirm that timesheets for project 8 (Modernisation Ligne Production)
in September 2025 are fully validated with no pending issues."

Response received:
✅ All timesheets validated
✅ No pending validation warnings
✅ Total days: 34 (Elodie: 12j, Didier: 22j)
✅ Total amount: 22,292€

Step 3: Generate Invoices
--------------------------
Delegate to Invoice Agent:
"Generate invoices for project 8 (Modernisation Ligne Production)
for billing period 2025-09.

After generation, retrieve all generated invoices and verify:
- Invoice references and IDs
- Invoice amounts match expected 22,292€
- All consultants are billed (Elodie LEGUAY, Didier GEIG)
- Billing period dates are correct

Provide detailed summary with invoice details."

Step 4: Report to User
----------------------
"INVOICE GENERATION COMPLETE

Project: Modernisation Ligne Production (ID: 8)
Client: Roche Diagnostics (ID: 5)
Billing Period: September 2025

GENERATED INVOICES:
1. FACT-2025-042
   - Date: 2025-09-30
   - Amount: 7,860€ (excl. tax)
   - Amount: 9,432€ (incl. tax)
   - Consultant: Elodie LEGUAY (12 days)
   - Order: 11, Delivery: 1

2. FACT-2025-043
   - Date: 2025-09-30
   - Amount: 14,432€ (excl. tax)
   - Amount: 17,318€ (incl. tax)
   - Consultant: Didier GEIG (22 days)
   - Order: 11, Delivery: 1

TOTALS:
- Total Invoiced (excl. tax): 22,292€
- Total Invoiced (incl. tax): 26,750€
- Invoice Count: 2
- Total Days Billed: 34

VERIFICATION:
✅ Invoice amounts match validated timesheets
✅ All consultants billed correctly
✅ Billing period correct (2025-09-01 to 2025-09-30)
✅ Client relationships verified

Invoices are ready for review and delivery to client."
```

### Example 2: Invoice Generation with Discrepancy

**User Request**: "Generate invoices but client email shows different hours than BoondManager"

**Orchestrator Workflow**:

```
Step 1: Detect Discrepancy
--------------------------
Query Agent response:
- BoondManager: Elodie LEGUAY 15 days
Client Email:
- Elodie LEGUAY 12 days

Discrepancy detected: +3 days in BoondManager

Step 2: DO NOT Generate Invoice Yet
------------------------------------
⚠️ CRITICAL: Invoices should NEVER be generated when discrepancies exist

Action: Initiate discrepancy resolution workflow

Step 3: Resolve Discrepancy
----------------------------
Delegate to Emailing Agent:
"Draft email to Elodie LEGUAY about timesheet discrepancy:
- BoondManager shows 15 days
- Client confirmation shows 12 days
- Difference: 3 days

Request clarification and correction."

Send email and wait for response

Step 4: After Resolution
-------------------------
OPTION A: Worker confirms 12 days
→ Delegate to Validation Agent: Update timesheet to 12 days
→ Proceed with invoice generation

OPTION B: Worker confirms 15 days
→ Delegate to Emailing Agent: Contact client for confirmation
→ Wait for client to confirm revised hours
→ Proceed with invoice generation

Step 5: Generate Invoice (Only After Resolution)
-------------------------------------------------
[Follow standard invoice generation workflow]
```

### Example 3: Batch Invoice Generation (Multiple Projects)

**User Request**: "Generate invoices for all Roche projects in September 2025"

**Orchestrator Workflow**:

```
Step 1: Identify All Projects
------------------------------
Delegate to Query Agent:
"Find all active projects for company 5 (Roche Diagnostics)
that have timesheet activity in September 2025. Return project
IDs, names, and assigned resources."

Response received:
- Project 8: Modernisation Ligne Production (2 resources)
- Project 12: Digital Transformation (3 resources)
- Project 15: Cloud Migration (1 resource)

Step 2: Verify Prerequisites for All Projects
----------------------------------------------
For each project:
- Verify timesheets validated
- Verify no pending discrepancies
- Verify client confirmation received

Step 3: Generate Invoices (Batch Delegation)
---------------------------------------------
Delegate to Invoice Agent (batch request):
"Generate invoices for the following projects in September 2025:

1. Project 8 (Modernisation Ligne Production)
2. Project 12 (Digital Transformation)
3. Project 15 (Cloud Migration)

For each project:
- Generate invoices for billing period 2025-09
- Retrieve and verify generated invoices
- Provide individual summary

After processing all projects, provide consolidated summary
with total amount invoiced across all projects."

Step 4: Consolidated Report
----------------------------
"BATCH INVOICE GENERATION COMPLETE

Client: Roche Diagnostics (ID: 5)
Billing Period: September 2025
Projects Processed: 3

PROJECT SUMMARIES:
==================

Project 8: Modernisation Ligne Production
------------------------------------------
Invoices: 2 (FACT-2025-042, FACT-2025-043)
Subtotal: 22,292€ (excl. tax)
Resources: 2 consultants, 34 days

Project 12: Digital Transformation
-----------------------------------
Invoices: 3 (FACT-2025-044, FACT-2025-045, FACT-2025-046)
Subtotal: 38,400€ (excl. tax)
Resources: 3 consultants, 48 days

Project 15: Cloud Migration
----------------------------
Invoices: 1 (FACT-2025-047)
Subtotal: 12,800€ (excl. tax)
Resources: 1 consultant, 16 days

CONSOLIDATED TOTALS:
====================
Total Projects: 3
Total Invoices: 6
Total Amount (excl. tax): 73,492€
Total Amount (incl. tax): 88,190€
Total Days Billed: 98
Total Consultants: 6

All invoices generated successfully and verified."
```

## Quick Reference

### Pre-Generation Checklist

```
□ Timesheets validated
□ Client confirmation received
□ No discrepancies pending
□ Project data verified
□ Billing period closed
□ Required approvals in place
```

### Generation Command Template

```
Delegate to Invoice Agent:
"Generate invoices for project {id} ('{name}') for billing period {YYYY-MM}.
After generation, retrieve and verify all generated invoices.
Provide detailed summary with references, amounts, and totals."
```

### Verification Checklist

```
□ Invoice count correct
□ Amounts match timesheets
□ All consultants billed
□ Dates correct
□ Relationships verified
□ Tax calculations correct
```

### Escalation Criteria

```
🚨 ESCALATE if:
- Amount variance > 10%
- Generation fails repeatedly
- Missing project configuration
- Unable to verify invoices
- Unresolved discrepancies

⚠️ CONSIDER escalation if:
- First-time client
- Complex billing scenario
- Non-standard period
- Special client requirements
```

## Summary

Invoice generation is a **critical, multi-phase workflow** requiring:

1. **Preparation**: Verify prerequisites and query required data
2. **Generation**: Delegate to Invoice Agent with complete context
3. **Verification**: Confirm generated invoices match expectations
4. **Reporting**: Provide comprehensive summary to user

**Never skip verification steps** - invoice accuracy directly impacts client relationships and financial integrity.

**Always consult this policy** when invoice generation is requested or when issues arise during the invoicing workflow.

**Integration**: This policy works in conjunction with timesheet validation, delegation best practices, and error handling protocols to ensure reliable, accurate invoicing operations.
