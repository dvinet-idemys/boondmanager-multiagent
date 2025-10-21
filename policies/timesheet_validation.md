# Timesheet Validation Policy

## Overview
This policy defines the standard process for validating consultant timesheets against client emails.

## Validation Process

### Step 1: Query Phase
1. Extract worker names and project references from client email
2. For each worker mentioned:
   - Query BoondManager for their actual days worked
   - Query BoondManager for their total cost
   - Ensure you include the full project name in all queries

### Step 2: Comparison Phase
1. Compare client-reported days vs BoondManager days
2. Compare client-reported costs vs BoondManager costs
3. Flag discrepancies for any mismatches

### Step 3: Discrepancy Handling

#### When Days Match
- Proceed directly to timesheet validation
- Use the validation agent with the timesheet ID
- Report validation warnings if any exist

#### When Days Don't Match
**MANDATORY EMAIL WORKFLOW:**
1. Draft email to worker explaining discrepancy
2. Include:
   - Worker name
   - Project name (full reference)
   - Client-reported days vs BoondManager days
   - Time period (month + year)
   - Request for clarification
3. Send email via emailing agent
4. **CRITICAL**: Instruct emailing agent to wait for response
5. Resume workflow based on worker response

### Step 4: Validation Execution
Once discrepancies are resolved:
1. Retrieve timesheet ID for the worker + project + period
2. Call validation tool with timesheet ID
3. Report validation outcome

## Email Template Guidelines

### Discrepancy Email Structure
```
Subject: Timesheet Discrepancy - [Project Name] - [Month Year]

Dear [Worker First Name],

We have identified a discrepancy in your timesheet for [Project Name] during [Month Year].

Our Records (BoondManager): [X] days
Client Report: [Y] days

Could you please review your timesheet and clarify this difference?

Best regards,
[System/Manager Name]
```

### Tone Requirements
- Professional but friendly
- Clear and specific
- Include all relevant context
- Avoid accusatory language

## Data Dependencies

### Required Information Before Queries
- Worker full name (First + Last)
- Project name (exact reference from email)
- Time period (month + year format)
- Client reported values (days, cost)

### Query Order
1. **First**: Get project details if not in email
2. **Second**: Get worker assignment to project
3. **Third**: Get timesheet details (days + cost)
4. **Fourth**: Execute comparison logic

## Error Handling

### Missing Data
- If project not found: Escalate to human
- If worker not found: Verify name spelling, query by partial match
- If timesheet not found: Check time period accuracy

### API Failures
- Retry up to 3 times with exponential backoff
- Log all API errors
- Escalate persistent failures to human

### Email Failures
- Retry email send once
- If still fails, log and escalate to human
- Never proceed with validation if email notification fails

## Human-in-the-Loop Triggers

### Automatic Escalation
- Worker email bounce-back
- Worker response indicates system error
- Discrepancy > 5 days difference
- Multiple failed API attempts

### Resume Conditions
- Worker confirms BoondManager data is correct
- Worker provides explanation and corrected data
- Manager provides override authorization

## Validation States

### Valid Timesheet
- Days match exactly
- Cost matches exactly (within 1% tolerance)
- No validation warnings from BoondManager

### Warning Timesheet
- Days match
- Cost matches
- BoondManager returns validation warnings (review required)

### Invalid Timesheet
- Days mismatch
- Cost mismatch
- Cannot resolve via email workflow

## Reporting Requirements

### Successful Validation
Report format:
```
Worker: [Name]
Project: [Project Name]
Period: [Month Year]
Status: VALIDATED
Days: [X]
Cost: [Y]
```

### Discrepancy Report
Report format:
```
Worker: [Name]
Project: [Project Name]
Period: [Month Year]
Status: DISCREPANCY DETECTED
BoondManager Days: [X]
Client Reported Days: [Y]
Difference: [Z] days
Action Taken: Email sent, awaiting response
```

## Best Practices

### Query Optimization
- Batch similar queries when possible
- Include full context in every query
- Use exact project names, not abbreviations

### Prompt Engineering
- Provide complete information to subagents
- Include tone guidance for emails
- Specify expected output formats

### Error Prevention
- Always query data before using it
- Never assume email addresses
- Verify project names before querying
- Include time periods in all queries

## Compliance Notes

### Data Privacy
- Only share timesheet data with authorized recipients
- Use worker's registered email address only
- Log all data access for audit trail

### Audit Trail
- Log all queries with timestamps
- Record all email communications
- Track human intervention points
- Store validation decisions
