# Delegation Best Practices

## Overview
Guidelines for the Main Orchestrator on effective task delegation to specialized subagents.

## Core Principles

### 1. Explicit Over Implicit
**Always provide complete context** - Subagents are ChatGPT models that need comprehensive information.

✅ **GOOD**: "How many days did Elodie LEGUAY work on project 'Modernisation Ligne Production - Multi commande' in September 2025?"

❌ **BAD**: "How many days did Elodie work?"

### 2. Batch Similar Operations
When you have multiple similar tasks, use batch delegation for parallel execution.

✅ **GOOD**: Batch delegate 3 cost queries to query agent
❌ **BAD**: Make 3 sequential individual delegations

### 3. Data Dependencies
**CRITICAL**: Always query data BEFORE using it in subsequent operations.

**Correct Sequence**:
1. Query worker email address
2. THEN draft email using queried address

**Incorrect Sequence**:
1. Draft email assuming email address ❌

## Subagent Capabilities

### Query Agent
**Purpose**: Coordinate data retrieval from BoondManager API

**Delegates to**:
- resource_agent: Worker/consultant lookups
- project_agent: Project and delivery queries
- timesheet_agent: CRA/timesheet operations

**Best Use Cases**:
- "Get total cost for worker X on project Y in month Z"
- "How many days did worker X work in period Y?"
- "Find all workers assigned to project X"

**Prompt Requirements**:
- Include full worker names (First + Last)
- Include exact project names/references
- Specify time periods (month + year)
- Ask open-ended questions (don't include expected values)

**Example**:
```
Batch delegation to query agent:
- "Get total cost for Elodie LEGUAY on project 'Modernisation Ligne Production - Multi commande' in September 2025"
- "Get total cost for Didier GEIG on project 'Modernisation Ligne Production - Multi commande' in September 2025"
```

### Validation Agent
**Purpose**: Execute timesheet validation operations

**Best Use Cases**:
- Validate a specific timesheet by ID
- Check validation warnings
- Execute validation after discrepancy resolution

**Prompt Requirements**:
- Provide timesheet ID (query first if unknown)
- Include validator ID if required
- Specify what validation checks to perform

**Example**:
```
"Validate timesheet ID 12345 using validator ID 42 and report any warnings"
```

### Emailing Agent
**Purpose**: Handle all email operations (read, draft, send, wait for response)

**Best Use Cases**:
- Send discrepancy notifications to workers
- Wait for worker responses (human-in-the-loop)
- Draft professional emails with specific context

**Prompt Requirements**:
- Provide complete email context (recipient, subject, body details)
- Specify tone (professional, friendly, formal)
- Include all relevant data (names, dates, numbers)
- Explicitly request "wait for response" if needed

**Example**:
```
"Draft and send an email to Elodie LEGUAY regarding her timesheet discrepancy for project 'Modernisation Ligne Production - Multi commande' in September 2025. Our records show 15 days, but the client reported 12 days. Ask her to review and clarify. Use a professional but friendly tone. After sending, wait for her response."
```

## Delegation Patterns

### Pattern 1: Sequential Dependency Chain
When later tasks depend on earlier results.

```
Step 1: Query worker email → Get result
Step 2: Draft email using actual email address from Step 1
Step 3: Send email
Step 4: Wait for response
```

### Pattern 2: Parallel Batch Processing
When tasks are independent and similar.

```
Parallel Batch:
- Query cost for worker A
- Query cost for worker B
- Query cost for worker C

All execute simultaneously → aggregate results
```

### Pattern 3: Conditional Workflow
When next steps depend on validation results.

```
Step 1: Compare client data vs BoondManager data
Step 2a: If match → Validate timesheet
Step 2b: If mismatch → Send email to worker → Wait → Resume
```

## Prompt Engineering for Subagents

### Context Completeness Checklist
Before delegating, ensure prompt includes:
- [ ] Full names (not just first names)
- [ ] Exact project names/references
- [ ] Specific time periods (month + year)
- [ ] All relevant data values
- [ ] Expected output format (if specific)
- [ ] Tone guidance (for emails)

### ChatGPT Optimization Techniques

#### 1. Structured Instructions
For complex tasks, break down requirements:
```
"Draft an email with the following requirements:
- Recipient: [worker name and email]
- Subject: Timesheet discrepancy
- Include: project name, time period, discrepancy details
- Tone: professional but friendly
- Action requested: review and clarify
After sending, wait for response."
```

#### 2. Explicit Data Inclusion
Don't assume subagent will infer - state explicitly:
```
❌ "Email the worker about the issue"
✅ "Email Elodie LEGUAY (email: elodie.leguay@example.com) about her timesheet showing 15 days in BoondManager vs 12 days in client report for project 'Modernisation Ligne Production - Multi commande' in September 2025"
```

#### 3. Example-Driven Prompts
When output format matters, provide examples:
```
"Query days worked and return in this format:
Worker: [Full Name]
Days: [Number]
Period: [Month Year]"
```

## Anti-Patterns to Avoid

### ❌ Vague Delegation
```
"Check the timesheet"
```
**Problem**: Missing worker, project, time period

### ❌ Assumed Data
```
"Send email to worker about discrepancy"
```
**Problem**: Missing email address, worker name, discrepancy details

### ❌ Missing Context
```
"Get cost for Elodie in Sep"
```
**Problem**: Missing last name, year, project

### ❌ Sequential When Parallel Possible
```
Delegate "Get cost for worker A"
Wait for result
Delegate "Get cost for worker B"
Wait for result
```
**Problem**: Should batch both in parallel

### ❌ Including Expected Values
```
"Verify that worker X worked 22 days"
```
**Problem**: Biases the query, should ask open-ended

## Error Recovery

### When Subagent Returns Error
1. Analyze error message
2. Check if prompt had missing context
3. Re-delegate with complete information
4. If persistent, escalate to human

### When Subagent Returns Unexpected Format
1. Verify your prompt specified format
2. Re-delegate with explicit format requirements
3. Include example output

### When Subagent Gets Stuck
1. Check for data dependencies
2. Break down into smaller subtasks
3. Provide intermediate data explicitly

## Performance Optimization

### Batch vs Individual Decision Matrix

| Scenario | Use Batch | Use Individual |
|----------|-----------|----------------|
| 3+ similar queries | ✅ | ❌ |
| Different subagents needed | ❌ | ✅ |
| Tasks have dependencies | ❌ | ✅ |
| Same operation, different data | ✅ | ❌ |

### Delegation Efficiency Tips
1. **Group by subagent**: Batch requests to same subagent
2. **Minimize round trips**: Get all needed data upfront
3. **Parallel where possible**: Independent tasks → batch
4. **Sequential where necessary**: Dependencies → individual

## Quality Assurance

### Pre-Delegation Checklist
- [ ] All required context included?
- [ ] Data dependencies resolved?
- [ ] Appropriate subagent selected?
- [ ] Batch opportunity identified?
- [ ] Expected output format specified?

### Post-Delegation Review
- [ ] Result matches expected format?
- [ ] All required data present?
- [ ] Error handling needed?
- [ ] Next steps clear?

## Human-in-the-Loop Guidelines

### When to Trigger HITL
- Email response needed from worker
- Ambiguous data requiring judgment
- High-risk operations (validation failures)
- System errors requiring intervention

### HITL Best Practices
1. Provide clear context to human
2. Specify exact decision needed
3. Include all relevant data
4. Wait explicitly for response
5. Resume with human input incorporated
