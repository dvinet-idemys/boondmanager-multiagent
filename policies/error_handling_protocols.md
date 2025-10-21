# Error Handling Protocols

## Overview
Standard error handling and recovery procedures for the multi-agent invoice workflow system.

## Error Categories

### 1. API Errors (BoondManager)

#### Connection Errors
**Symptoms**: Timeout, connection refused, network unreachable

**Response**:
1. Retry with exponential backoff (3 attempts max)
2. Wait times: 1s, 2s, 4s
3. Log each attempt with timestamp
4. After 3 failures → escalate to human

**Example Recovery**:
```
Attempt 1: Failed (timeout) → Wait 1s
Attempt 2: Failed (timeout) → Wait 2s
Attempt 3: Failed (timeout) → Escalate
```

#### Authentication Errors
**Symptoms**: 401 Unauthorized, JWT token expired

**Response**:
1. Regenerate JWT token
2. Retry original request once
3. If still fails → check credentials configuration
4. Escalate to human if credentials invalid

#### Rate Limiting
**Symptoms**: 429 Too Many Requests

**Response**:
1. Extract retry-after header if present
2. Wait specified duration
3. Resume request
4. If no header, wait 60s before retry

#### 404 Not Found Errors
**Symptoms**: Resource ID not found, project doesn't exist

**Response**:
1. Verify input data (IDs, names, dates)
2. Try alternative query methods (name search vs ID lookup)
3. If confirmed missing → report to orchestrator with specific details
4. Orchestrator decides whether to escalate or adjust workflow

**Do NOT**: Silently fail or assume data doesn't exist without verification

### 2. Data Validation Errors

#### Missing Required Data
**Symptoms**: Email missing worker name, project name, or period

**Response**:
1. List specifically what data is missing
2. Attempt to infer from context if reasonable
3. If cannot infer → request clarification from source
4. If source is email → may need to ask human

**Example**:
```
Error: Missing project name in client email
Context: Email mentions "Elodie worked 12 days in September"
Recovery: Check if only one active project for Elodie in September
  - If yes → use that project
  - If multiple → escalate for clarification
```

#### Data Format Errors
**Symptoms**: Invalid date format, malformed cost values

**Response**:
1. Attempt standard format conversions
2. Log original value and converted value
3. If conversion uncertain → escalate

**Examples**:
- "Sep 2025" → "2025-09" ✅
- "12j" → 12 days ✅
- "7860" → 7860.00 currency ✅
- "22days" → 22 days ✅

#### Data Range Errors
**Symptoms**: Days worked > days in month, negative costs

**Response**:
1. Flag as data integrity issue
2. Report exact values found
3. Request human verification
4. Do NOT auto-correct without confirmation

### 3. LLM/Subagent Errors

#### Tool Call Errors
**Symptoms**: Subagent returns error, tool execution fails

**Response**:
1. Check if error is recoverable (e.g., missing parameter)
2. If missing data → provide complete context and retry
3. If subagent confused → rephrase delegation with more clarity
4. After 2 retries → escalate

**Common Causes**:
- Incomplete prompt (missing context)
- Ambiguous instructions
- Data dependency not resolved

#### Hallucination Detection
**Symptoms**: Subagent fabricates data, makes up email addresses

**Response**:
1. Verify all factual claims against source data
2. If suspicious → query BoondManager to confirm
3. Flag to orchestrator for review
4. Adjust prompts to emphasize "query first, never assume"

**Prevention**:
- Explicit "NEVER fabricate data" instructions
- Always query before using data
- Require subagents to cite sources

#### Infinite Loop Detection
**Symptoms**: Subagent keeps calling same tool repeatedly

**Response**:
1. Detect after 3 identical tool calls in sequence
2. Interrupt and analyze loop cause
3. Provide explicit exit condition or alternative approach
4. If stuck → escalate to human

### 4. Email Errors

#### Email Delivery Failures
**Symptoms**: SMTP error, bounce-back, invalid email

**Response**:
1. Verify email address format
2. Check if email exists in BoondManager
3. Try alternative contact method if available
4. Escalate to human if critical communication

**Do NOT**: Proceed with workflow if email notification failed

#### No Response Timeout
**Symptoms**: Worker doesn't respond to email within timeout period

**Response**:
1. Wait for configured timeout (default: 24-48 hours)
2. Send reminder email (one time only)
3. If still no response → escalate to manager
4. Manager decides whether to override or keep waiting

#### Worker Response Ambiguous
**Symptoms**: Worker email response unclear or contradictory

**Response**:
1. Parse response for key information
2. If cannot extract clear answer → send clarification request
3. Provide specific options for worker to choose
4. Escalate if still ambiguous after clarification attempt

### 5. Workflow State Errors

#### Checkpoint/Memory Errors
**Symptoms**: Lost conversation state, cannot resume

**Response**:
1. Log the error with thread_id
2. Attempt to reconstruct state from available messages
3. If critical data lost → escalate to human
4. Prevent data loss: checkpoint frequently

#### GraphInterrupt Handling Errors
**Symptoms**: Interrupt not caught, workflow hangs

**Response**:
1. Verify interrupt handling code is active
2. Check if error occurred before interrupt point
3. Manual resume if needed
4. Review code to prevent future occurrences

## Recovery Strategies

### Strategy 1: Retry with Backoff
**Use When**: Transient errors (network, rate limit)

```
def retry_with_backoff(operation, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return operation()
        except TransientError:
            if attempt < max_attempts - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait_time)
            else:
                escalate_to_human()
```

### Strategy 2: Alternative Approach
**Use When**: Primary method fails but alternatives exist

**Example**:
```
Primary: Query by resource ID → 404 error
Alternative: Query by full name → Success
```

### Strategy 3: Graceful Degradation
**Use When**: Non-critical feature fails

**Example**:
```
Failed: Retrieve worker photo → Skip photo, continue with text data
Failed: Get optional metadata → Continue with required data only
```

### Strategy 4: Human Escalation
**Use When**: Cannot auto-recover, requires judgment

**Escalation Info Required**:
- Exact error message
- What was attempted
- Current workflow state
- Data involved
- Suggested actions (if any)

## Error Logging Standards

### Log Levels

#### ERROR (Critical)
- API authentication failures
- Data corruption detected
- Unrecoverable workflow failures
- Security violations

#### WARNING (Important)
- Retry attempts
- Data validation issues
- Performance degradation
- Unusual patterns

#### INFO (Routine)
- Successful operations
- State transitions
- Tool call completions

### Log Format
```
[TIMESTAMP] [LEVEL] [COMPONENT] [THREAD_ID] Message
Context: {relevant data}
Action: {what was done}
Result: {outcome}
```

**Example**:
```
[2025-01-15 14:23:45] ERROR BoondClient thread_abc123 API call failed
Context: GET /resources/12345
Action: Retry attempt 2/3
Result: Timeout after 30s
```

## Escalation Procedures

### Automatic Escalation Triggers
1. **High-Value Discrepancy**: >5 days difference or >10% cost difference
2. **Repeated Failures**: 3+ failed attempts on same operation
3. **Security Issues**: Authentication failures, unauthorized access attempts
4. **Data Integrity**: Impossible values, corruption detected
5. **Critical Communication Failure**: Cannot reach worker via email

### Escalation Message Format
```
ESCALATION REQUIRED

Issue: [Brief description]
Severity: [High/Medium/Low]
Component: [Which agent/tool]
Thread ID: [For tracking]

Details:
[What happened]
[What was attempted]
[Current state]

Data Context:
[Relevant data that led to issue]

Recommended Actions:
1. [Option 1]
2. [Option 2]

Awaiting human decision...
```

### Human Decision Points
1. Override discrepancy and proceed
2. Contact worker via alternative method
3. Escalate to manager/client
4. Abort workflow
5. Provide missing/corrected data

## Preventive Measures

### Design Patterns for Error Prevention

#### 1. Fail-Fast Validation
Validate all inputs immediately before processing:
```
def validate_workflow_input(email_data):
    required = ['worker_name', 'project_name', 'period']
    for field in required:
        if field not in email_data:
            raise ValidationError(f"Missing required field: {field}")
```

#### 2. Defensive Prompting
Include error prevention in subagent prompts:
```
"IMPORTANT: If you cannot find the data, respond with 'DATA NOT FOUND: [specific item]'
rather than making assumptions or fabricating values."
```

#### 3. Idempotency
Design operations to be safely retryable:
```
# Email sending: Check if already sent before sending again
# Data queries: Safe to query multiple times
# Validation: Stateless, safe to re-validate
```

#### 4. Circuit Breaker
Stop attempting operation after threshold:
```
if failure_count > 3:
    circuit_open = True
    return "Service temporarily unavailable, escalating"
```

## Testing Error Scenarios

### Test Cases for Each Error Type
1. **API Timeout**: Mock slow API response
2. **Invalid Data**: Feed malformed email
3. **Missing Data**: Omit required fields
4. **LLM Confusion**: Ambiguous prompts
5. **Email Failure**: Invalid recipient
6. **State Loss**: Simulate checkpoint failure

### Error Recovery Verification
- Can system recover automatically?
- Is human escalation triggered appropriately?
- Are retries executed correctly?
- Is data preserved during errors?

## Monitoring and Alerts

### Metrics to Track
- Error rate by type
- Retry success rate
- Escalation frequency
- Mean time to recovery
- User impact (blocked workflows)

### Alert Thresholds
- Error rate >10%: WARNING
- Error rate >25%: CRITICAL
- Same error 5+ times: ALERT
- Escalation queue growing: ATTENTION
