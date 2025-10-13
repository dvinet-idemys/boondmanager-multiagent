# Dispatch Task Verification Agent Requirements

## Purpose
Validate dispatch tasks created by the orchestrator before execution to ensure they meet quality standards and align with open-ended question principles.

---

## Core Validation Requirements

### 1. Question Format Validation

**Requirement**: All dispatch tasks must be formulated as open-ended questions, not verification statements.

**Valid Examples**:
- ✅ "How many days did Elodie LEGUAY work in September 2025?"
- ✅ "What is the total cost for Didier GEIG's work in September 2025?"
- ✅ "Which project did worker X work on during the specified period?"

**Invalid Examples**:
- ❌ "Verify that Elodie LEGUAY worked 22 days in September 2025"
- ❌ "Check if the total cost for Didier GEIG is 7860"
- ❌ "Confirm worker X was assigned to project Y"

**Validation Rules**:
- Task must contain question words: "How many", "What", "Which", "Where", "When"
- Task must end with a question mark (?)
- Task must NOT contain verification verbs: "verify", "confirm", "check if", "validate that"
- Task must NOT include expected values or outcomes in the question

---

### 2. Atomicity Validation

**Requirement**: Each dispatch task must target exactly ONE specific data point or entity.

**Valid Examples**:
- ✅ "How many days did Elodie LEGUAY work in September 2025?" (one worker, one metric)
- ✅ "What is the resource ID for Didier GEIG?" (one worker, one attribute)

**Invalid Examples**:
- ❌ "How many days did Elodie LEGUAY and Didier GEIG work in September 2025?" (multiple workers)
- ❌ "What are the days worked and total cost for Elodie LEGUAY?" (multiple metrics)
- ❌ "Analyze all workers for the Roche project" (vague, non-atomic)

**Validation Rules**:
- Task targets exactly ONE worker/entity
- Task queries exactly ONE metric/attribute
- Task does NOT use plural forms ("workers", "projects") unless asking for a list
- Task does NOT use "and" to combine multiple queries

---

### 3. Context Completeness

**Requirement**: Each dispatch task must be fully self-contained with all necessary context.

**Required Context Elements**:
- **Worker identification**: Full name (First + Last) when querying worker data
- **Time period**: Specific month and year (e.g., "September 2025")
- **Project context**: Project name when relevant to the query
- **Metric specification**: Clear definition of what's being asked (days, cost, hours, etc.)

**Valid Examples**:
- ✅ "How many days did Elodie LEGUAY work on project 'Modernisation Ligne Production' in September 2025?"
- ✅ "What is the total cost for Didier GEIG's work in September 2025?"

**Invalid Examples**:
- ❌ "How many days did Elodie work?" (missing time period)
- ❌ "What is the total cost in September?" (missing worker)
- ❌ "How many days did the worker work?" (vague worker reference)

**Validation Rules**:
- Task includes specific worker name (not "worker A" or "the worker")
- Task includes complete time period (month + year)
- Task includes all necessary identifiers from source data
- Task can be understood without referring to parent context

---

### 4. Specificity and Precision

**Requirement**: Tasks must be precise and unambiguous.

**Valid Examples**:
- ✅ "How many days did Elodie LEGUAY work in September 2025?" (specific metric)
- ✅ "What is the total cost in EUR for Didier GEIG in September 2025?" (specific currency)

**Invalid Examples**:
- ❌ "How much did Elodie LEGUAY work?" (ambiguous: days? hours? cost?)
- ❌ "What is the cost for Didier GEIG?" (ambiguous: total? per day? which period?)
- ❌ "Get Elodie's data" (too vague)

**Validation Rules**:
- Task specifies exact metric being queried
- Task uses precise terminology (days, hours, EUR, resource_id, etc.)
- Task avoids ambiguous pronouns ("it", "they", "this")
- Task doesn't use vague verbs ("get", "fetch", "retrieve" without specifying what)

---

### 7. Independence and Parallelizability

**Requirement**: Tasks must be independently executable without dependencies on other tasks.

**Valid Examples**:
- ✅ All tasks query independent data points that can run in parallel
```python
[
    ("reconciliation", "How many days did Elodie LEGUAY work in September 2025?"),
    ("reconciliation", "How many days did Didier GEIG work in September 2025?")
]
```

**Invalid Examples**:
- ❌ Tasks that reference results from other tasks
```python
[
    ("reconciliation", "What is Elodie's resource ID?"),
    ("reconciliation", "Using the resource ID from previous query, get timesheet data")
]
```

**Validation Rules**:
- Task doesn't reference "previous result", "above query", "from earlier"
- Task doesn't have implicit dependencies on other tasks in the batch
- Task contains all data needed for independent execution

---

## Verification Agent Implementation Requirements

### Input
```python
{
    "calls": [
        ("subagent_name", "task_prompt"),
        ...
    ]
}
```

### Output Format

#### When All Validations Pass
```python
{
    "status": "approved",
    "validated_calls": [
        ("subagent_name", "task_prompt"),
        ...
    ],
    "validation_summary": {
        "total_tasks": 3,
        "all_checks_passed": True
    }
}
```

#### When Validations Fail
```python
{
    "status": "rejected",
    "errors": [
        {
            "task_index": 0,
            "task": ("reconciliation", "Verify Elodie worked 22 days"),
            "violation": "question_format",
            "details": "Task uses verification verb 'verify' instead of open-ended question",
            "suggestion": "How many days did Elodie LEGUAY work in September 2025?"
        },
        {
            "task_index": 1,
            "task": ("reconciliation", "How many days did workers work?"),
            "violation": "atomicity",
            "details": "Task targets multiple workers instead of one",
            "suggestion": "Split into separate tasks, one per worker"
        }
    ],
    "validation_summary": {
        "total_tasks": 3,
        "failed_tasks": 2,
        "passed_tasks": 1,
        "critical_issues": 2
    }
}
```

---

## Validation Checklist

For each dispatch task, verify:

- [ ] **Question Format**: Uses question words, ends with "?", no verification verbs
- [ ] **Atomicity**: Targets exactly one entity and one metric
- [ ] **Context**: Includes worker name, time period, and all required identifiers
- [ ] **Routing**: Correct subagent for task type
- [ ] **Completeness**: All input data items have corresponding tasks
- [ ] **Specificity**: Precise metric specification, no ambiguity
- [ ] **Independence**: Can execute without dependencies on other tasks
- [ ] **Name Formatting**: Full first and last names, proper capitalization

---

## Error Severity Levels

### Critical (MUST fix before execution)
- Verification statements instead of questions
- Missing critical context (worker name, time period)
- Multiple entities in single task
- Wrong subagent routing
- Incomplete data coverage

### Warning (SHOULD fix but not blocking)
- Minor name formatting inconsistencies
- Could be more specific but still executable
- Non-optimal parallelization

### Info (Nice to have)
- Suggestions for improved clarity
- Alternative phrasing recommendations

---

## Example Validation Scenarios

### Scenario 1: Perfect Dispatch
**Input Query**: "Check hours for Elodie LEGUAY and Didier GEIG in September 2025"

**Dispatch Tasks**:
```python
[
    ("reconciliation", "How many days did Elodie LEGUAY work in September 2025?"),
    ("reconciliation", "How many days did Didier GEIG work in September 2025?")
]
```

**Validation Result**: ✅ APPROVED
- Question format: ✅
- Atomicity: ✅
- Context complete: ✅
- All workers covered: ✅

---

### Scenario 2: Verification Statement (CRITICAL ERROR)
**Dispatch Tasks**:
```python
[
    ("reconciliation", "Verify that Elodie LEGUAY worked 22 days in September 2025")
]
```

**Validation Result**: ❌ REJECTED
- **Error**: Uses verification verb "verify"
- **Error**: Contains expected value "22 days" in question
- **Suggestion**: "How many days did Elodie LEGUAY work in September 2025?"

---

### Scenario 3: Non-Atomic Task (CRITICAL ERROR)
**Dispatch Tasks**:
```python
[
    ("reconciliation", "How many days did Elodie LEGUAY and Didier GEIG work in September 2025?")
]
```

**Validation Result**: ❌ REJECTED
- **Error**: Targets multiple workers in single task
- **Error**: Incomplete coverage (only 1 task for 2 workers)
- **Suggestion**: Split into 2 separate tasks

---

### Scenario 4: Missing Context (CRITICAL ERROR)
**Dispatch Tasks**:
```python
[
    ("reconciliation", "How many days did Elodie work?")
]
```

**Validation Result**: ❌ REJECTED
- **Error**: Missing last name
- **Error**: Missing time period
- **Suggestion**: "How many days did Elodie LEGUAY work in September 2025?"