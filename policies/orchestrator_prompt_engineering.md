# Orchestrator Prompt Engineering Guidelines

## Overview
Comprehensive guide for the Main Orchestrator on crafting effective prompts for ChatGPT-based subagents.

## Core Principle: ChatGPT Requires Explicit Context

**Critical Understanding**: All subagents use ChatGPT (OpenAI API), which requires:
- Complete, explicit information
- No assumptions or inference
- Detailed context over brevity
- Structured instructions for complex tasks

## ChatGPT Prompting Best Practices

### 1. Be Explicit and Detailed

ChatGPT models need clear, comprehensive instructions.

**Guidelines**:
- Include ALL relevant context in every prompt
- Don't assume the model will infer missing information
- Specify expected output format when needed
- State constraints and requirements explicitly

**Why**: ChatGPT doesn't have access to your full context. What seems obvious to you must be stated explicitly.

### 2. Provide Complete Information

Don't rely on brevity - completeness is better than conciseness.

**Guidelines**:
- Multi-line prompts with full details are BETTER than short vague ones
- Include all data, constraints, and requirements upfront
- For complex tasks (emails, reports), provide complete instructions
- Redundancy is acceptable if it adds clarity

**Why**: ChatGPT prioritizes following explicit instructions. Vague prompts lead to assumptions and hallucinations.

### 3. Use Structured Instructions

For complex tasks, break down requirements step-by-step.

**Guidelines**:
- Break down what you need the subagent to do
- Specify tone, format, required elements
- Give examples when helpful
- Use numbered steps for multi-part tasks

**Why**: Structured prompts guide ChatGPT through complex reasoning and reduce errors.

### 4. Context is King

ChatGPT performs dramatically better with more context.

**Always Include When Available**:
- Full names (First + Last, not just first name)
- Exact project names/references (CRITICAL - not abbreviations)
- Specific time periods (month + year: "September 2025")
- Client/company names when relevant
- Relevant data from previous steps
- Background information that aids understanding

**Why**: Context prevents ambiguity and enables accurate tool usage (especially for data queries).

## Prompt Quality Examples

### Example 1: Email Drafting

❌ **BAD** (too vague):
```
"Email worker about issue"
```

**Problems**:
- Missing worker name
- Missing email address
- Missing issue details
- Missing tone guidance
- Missing context (project, dates)

✅ **GOOD** (detailed and complete):
```
"Draft an email to Elodie LEGUAY (elodie.leguay@example.com) regarding her timesheet discrepancy for project 'Modernisation Ligne Production - Multi commande' in September 2025. Our records show she worked 15 days, but the client email reported 12 days. Ask her to review her timesheet and provide clarification. Use a professional but friendly tone. Include the project name and time period in the email for clarity."
```

**Why This Works**:
- Full worker name AND email address
- Specific issue with exact numbers
- Project name (full reference)
- Time period (month + year)
- Tone guidance
- Clear action requested

### Example 2: Data Query

❌ **BAD** (missing context):
```
"Check days for worker"
```

**Problems**:
- Missing worker last name
- Missing project name
- Missing time period
- Ambiguous "check" verb

✅ **GOOD** (complete context):
```
"How many days did Elodie LEGUAY work on project 'Modernisation Ligne Production - Multi commande' in September 2025 according to BoondManager CRA records?"
```

**Why This Works**:
- Full worker name (First + Last)
- Exact project name (full reference)
- Specific time period (month + year)
- Data source specified (BoondManager CRA)
- Clear question format

### Example 3: Validation Task

❌ **BAD** (incomplete):
```
"Validate Elodie's timesheet"
```

**Problems**:
- Missing last name
- Missing project
- Missing period
- Missing validator ID
- No instructions on what to do with result

✅ **GOOD** (structured and complete):
```
"Validate the timesheet for Elodie LEGUAY on project 'Modernisation Ligne Production - Multi commande' for September 2025 using validator ID 42. After validation, report any warnings found. If validation fails, provide the specific error message."
```

**Why This Works**:
- Full identification (name + project + period)
- Validator ID specified
- Clear instructions on result handling
- Error handling guidance included

## Critical Rules for Data Handling

### Rule 1: NO Expected Values in Queries

**Principle**: Ask open-ended questions, never include expected answers.

❌ **WRONG**:
```
"Verify that worker Elodie LEGUAY worked 22 days on project X"
```

**Problem**: Biases the query with expected value (22 days)

✅ **CORRECT**:
```
"How many days did worker Elodie LEGUAY work on project X in September 2025?"
```

**Why**: Open-ended queries prevent confirmation bias and return actual data.

### Rule 2: Query Data BEFORE Using It

**Principle**: NEVER assume or fabricate data. Always query first, then use.

❌ **WRONG SEQUENCE**:
```
1. Draft email to worker@example.com
```

**Problem**: Email address assumed/fabricated

✅ **CORRECT SEQUENCE**:
```
1. Query worker email address
2. THEN draft email using queried address
```

**Why**: Prevents hallucination and ensures data accuracy.

**Examples of Data Dependencies**:
- Email addresses → Query worker contact info first
- Costs → Query actual cost first
- Dates → Query timesheet period first
- Project IDs → Query project details first

### Rule 3: Maximize Context in Every Prompt

**Principle**: Include ALL available details, even if they seem obvious.

**Always Include**:
- ✅ Full worker names (First + Last)
- ✅ Project names/references (exact, not abbreviated)
- ✅ Time periods (month + year format)
- ✅ Client/company names when relevant
- ✅ Relevant data from previous steps

❌ **WRONG** (minimal context):
```
"How many days did Elodie work in Sep?"
```

**Missing**:
- Last name
- Year
- Project name

✅ **CORRECT** (maximal context):
```
"How many days did Elodie LEGUAY work on project 'Modernisation Ligne Production - Multi commande' in September 2025?"
```

**Why This Matters**:
- Subagents need project names for accurate BoondManager queries
- Full names prevent confusion with similar first names
- Complete time periods ensure correct data retrieval
- Context enables proper tool selection and usage

## Common Anti-Patterns

### Anti-Pattern 1: Vague Delegation

❌ **WRONG**:
```
"Check the timesheet"
```

**Problems**:
- Missing: worker, project, time period
- Ambiguous: what aspect to check?

✅ **FIX**:
```
"Retrieve the timesheet details for Elodie LEGUAY on project 'Modernisation Ligne Production - Multi commande' for September 2025 and report the total days worked and total cost."
```

### Anti-Pattern 2: Assumed Data

❌ **WRONG**:
```
"Send email to worker about discrepancy"
```

**Problems**:
- Assumes email address known
- Assumes discrepancy details known
- Missing worker identification

✅ **FIX**:
```
"First query the email address for worker Elodie LEGUAY. Then draft and send an email explaining that our records show 15 days worked on project 'Modernisation Ligne Production - Multi commande' in September 2025, but the client reported 12 days. Ask her to review and clarify."
```

### Anti-Pattern 3: Missing Context

❌ **WRONG**:
```
"Get cost for Elodie"
```

**Problems**:
- Missing last name
- Missing project
- Missing time period

✅ **FIX**:
```
"Get the total cost for worker Elodie LEGUAY on project 'Modernisation Ligne Production - Multi commande' in September 2025"
```

### Anti-Pattern 4: Sequential When Parallel Possible

❌ **WRONG**:
```
Delegate "Get cost for worker A"
Wait for result
Delegate "Get cost for worker B"
Wait for result
```

**Problem**: Inefficient - these can run in parallel

✅ **FIX**:
```
Batch delegate to query agent:
- "Get cost for worker A on project X in Sep 2025"
- "Get cost for worker B on project X in Sep 2025"
```

## Tone and Format Guidance

### Professional Emails

**Template**:
```
"Draft an email with the following requirements:
- Recipient: [Full Name] ([email])
- Subject: [Clear subject line]
- Tone: Professional but friendly
- Content: [Specific details to include]
- Action requested: [What you need from recipient]
After sending, wait for response."
```

### Data Queries

**Template**:
```
"How many [metric] did [Full Name] [action] on project '[Exact Project Name]' in [Month Year] according to [Source]?"
```

### Validation Requests

**Template**:
```
"Validate the [item] for [Full Name] on project '[Exact Project Name]' for [Month Year] using validator ID [X]. Report [specific outcome details needed]."
```

## Workflow-Specific Guidance

### Timesheet Validation with Discrepancies

**Standard Pattern**:
```
0. If not present, query actual days worked for worker [Full Name] on project '[Project]' in [Month Year]
1. Compare authoritative info to client-reported value
2. IF MATCH: Validate timesheet
3. IF MISMATCH:
   a. Query worker email address
   b. Draft email explaining discrepancy with all details
   c. Send email
   d. Wait for response
   e. Resume based on worker response
```

**Key Points**:
- Always make sure you have authoritative info before comparing
- Include full context in email
- Explicitly wait for response
- Handle response appropriately

### Batch Data Collection

**Standard Pattern**:
```
Batch delegate to query agent with requests:
- "Get [data] for [Worker1 Full Name] on [Project] in [Period]"
- "Get [data] for [Worker2 Full Name] on [Project] in [Period]"
- "Get [data] for [Worker3 Full Name] on [Project] in [Period]"

All requests must follow SAME pattern, varying only the worker name.
```

**Key Points**:
- Use batch delegation for 3+ similar queries
- Maintain consistent request format
- Include full context in each request
- Parallel execution for efficiency

## Quality Checklist

Before delegating, verify:

- [ ] Full worker names included (First + Last)?
- [ ] Exact project names/references included?
- [ ] Specific time periods included (month + year)?
- [ ] All data dependencies resolved (queried first)?
- [ ] Tone/format specified for emails?
- [ ] Expected output format specified if needed?
- [ ] No assumed/fabricated data?
- [ ] Batch opportunity identified for 3+ similar tasks?

## Summary

**Key Principles**:
1. **Explicit > Implicit**: State everything explicitly
2. **Complete > Concise**: Full context beats brevity
3. **Structured > Vague**: Break down complex tasks
4. **Context is King**: Include all available details
5. **Query First**: Never assume data, always query
6. **Batch When Possible**: Parallel execution for efficiency

**Remember**: ChatGPT subagents only know what you explicitly tell them. When in doubt, add more context.
