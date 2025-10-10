# Implementation Plan - Invoice Workflow MVP

## Executive Summary

**Timeline**: 2 weeks (10 working days)
**Deployment**: Single Python script, no infrastructure
**Dependencies**: 5 Python packages
**Complexity**: Stateless execution, in-memory only

This plan breaks down the MVP implementation into actionable tasks with clear dependencies, acceptance criteria, and risk mitigation strategies.

---

## Pre-Implementation Checklist

### Critical Information Needed (BEFORE Day 1)

| Item | Status | Owner | Action |
|------|--------|-------|--------|
| BoondManager API authentication method | ❓ Pending | Tech Lead | Confirm: API Key, OAuth 2.0, or JWT |
| BoondManager sandbox credentials | ❓ Pending | DevOps | Obtain test environment access |
| Contract/Rate lookup API endpoint | ❓ Pending | Tech Lead | Identify endpoint: `GET /clients/{id}/contracts` |
| Client identifier mapping logic | ❓ Pending | Business | Define: email domain → client_id mapping |
| Tax calculation rules | ❓ Pending | Business | Confirm: Fixed 20% or configurable? |
| Email server credentials | ❓ Pending | DevOps | IMAP/SMTP access for testing |

**⚠️ BLOCKER**: Cannot start implementation until authentication method is confirmed.

---

## Week 1: Foundation & Core Workflow

### Day 1: Project Setup & State Models

#### Tasks
1. **Project Structure Setup** (1 hour)
   ```
   boondmanager-multiagent/
   ├── src/
   │   ├── __init__.py
   │   ├── models/           # Pydantic state models
   │   ├── nodes/            # LangGraph nodes
   │   ├── integrations/     # BoondManager API, Email clients
   │   ├── templates/        # Jinja2 email templates
   │   └── workflow.py       # Main LangGraph workflow
   ├── tests/
   │   ├── unit/
   │   ├── integration/
   │   └── fixtures/
   ├── config/
   │   └── .env.example
   ├── requirements.txt
   └── main.py
   ```

2. **Install Dependencies** (30 min)
   ```bash
   pip install langgraph>=0.2 httpx>=0.27 pydantic>=2.0 jinja2>=3.1 python-dotenv>=1.0 pytest pytest-asyncio
   ```

3. **Create Pydantic State Models** (2 hours)
   - `src/models/state.py`:
     - `ConsultantActivity`
     - `Discrepancy`
     - `InvoiceWorkflowState`
   - Validation rules: Decimal for currency, date validation, required fields

4. **Environment Configuration** (1 hour)
   - Create `.env.example` with:
     ```
     BOOND_API_KEY=your_api_key_here
     BOOND_BASE_URL=https://api.boondmanager.com/api/v3
     SMTP_HOST=smtp.example.com
     SMTP_PORT=587
     SMTP_USER=billing@company.com
     SMTP_PASSWORD=password
     IMAP_HOST=imap.example.com
     IMAP_USER=billing@company.com
     IMAP_PASSWORD=password
     ```

**Acceptance Criteria:**
- ✅ Project structure created
- ✅ All dependencies installed
- ✅ State models pass Pydantic validation
- ✅ `.env.example` documented with all required variables

**Deliverable:** Runnable Python environment with state models

---

### Day 2: Email Parser Node

#### Tasks
1. **Email Parser Implementation** (3 hours)
   - `src/nodes/extract_email.py`:
     - Parse email body using regex patterns
     - Extract consultant names (format: "FirstName LastName: X days")
     - Extract billing period from subject line
     - Extract client email from sender
   - Regex patterns:
     ```python
     CONSULTANT_PATTERN = r"([A-Z][a-z]+ [A-Z][a-z]+):\s*(\d+(?:\.\d+)?)\s*days?"
     PERIOD_PATTERN = r"(January|February|...|December)\s+(\d{4})"
     ```

2. **Email Client Setup** (2 hours)
   - `src/integrations/email_client.py`:
     - IMAP connection for receiving emails
     - Email fetching logic (unread emails only)
     - Email parsing (extract body, subject, sender)

3. **Unit Tests** (1 hour)
   - Test email parsing with various formats
   - Test edge cases (missing data, malformed emails)
   - Mock email fixtures

**Acceptance Criteria:**
- ✅ Parse sample email correctly
- ✅ Extract all consultant names + days
- ✅ Extract billing period
- ✅ Handle malformed emails gracefully
- ✅ Unit tests pass (>90% coverage)

**Deliverable:** Working email parser node with tests

---

### Day 3: BoondManager API Client

#### Tasks
1. **API Client Implementation** (4 hours)
   - `src/integrations/boond_client.py`:
     - Async HTTP client (httpx.AsyncClient)
     - Authentication header handling
     - Connection pooling setup
     - Methods:
       - `get_consultant_by_name(first_name, last_name)`
       - `get_cra_data(consultant_id, period_start, period_end)`
       - `update_cra_status(cra_id, status)`
       - `create_invoice(invoice_data)`

2. **Retry Policy** (1 hour)
   - Exponential backoff decorator
   - Error classification logic
   - Retry configuration (max 3 attempts, 2s/4s/8s delays)

3. **Integration Test Setup** (1 hour)
   - Mock BoondManager API responses
   - Sandbox environment connection test
   - API endpoint validation

**Acceptance Criteria:**
- ✅ All 4 API methods implemented
- ✅ Retry logic working (test with timeout simulation)
- ✅ Connection to BoondManager sandbox successful
- ✅ Error classification correct (transient vs validation vs critical)

**Deliverable:** Fully functional BoondManager API client

---

### Day 4: Reconciliation Node

#### Tasks
1. **Reconciliation Node Implementation** (4 hours)
   - `src/nodes/reconcile_cra.py`:
     - Iterate through consultants from email
     - Lookup each consultant in BoondManager
     - Fetch CRA data for billing period
     - Compare client-declared days vs CRA days
     - Build discrepancy list if mismatches found
     - Update state: `all_matched`, `discrepancies`

2. **CRA Invalidation Logic** (1 hour)
   - Call `update_cra_status(cra_id, "invalidated")` on mismatch
   - Log discrepancy details

3. **Unit Tests** (1 hour)
   - Test matching scenario (all consultants match)
   - Test mismatch scenario (discrepancies detected)
   - Test missing consultant scenario
   - Test missing CRA scenario

**Acceptance Criteria:**
- ✅ Correctly identifies matching consultants
- ✅ Detects discrepancies with 100% accuracy
- ✅ Invalidates CRAs on mismatch
- ✅ Updates state correctly (`all_matched`, `discrepancies`)
- ✅ Unit tests pass

**Deliverable:** Working reconciliation node with tests

---

### Day 5: Integration Test

#### Tasks
1. **End-to-End Integration Test** (3 hours)
   - Test: Email parsing → Consultant lookup → CRA fetch → Comparison
   - Use BoondManager sandbox
   - Test data:
     - Email with 3 consultants
     - 2 matching CRAs, 1 mismatch
   - Verify:
     - Discrepancy correctly detected
     - CRA invalidated in BoondManager
     - State updated correctly

2. **Bug Fixes** (2 hours)
   - Address any issues found during integration testing
   - Refine error handling

3. **Documentation** (1 hour)
   - Document API client usage
   - Document reconciliation logic
   - Add comments to complex code

**Acceptance Criteria:**
- ✅ Integration test passes with BoondManager sandbox
- ✅ All discrepancies detected correctly
- ✅ CRAs invalidated in external system
- ✅ No unhandled errors

**Deliverable:** Validated reconciliation workflow

---

## Week 2: Validation, Invoice Generation & Completion

### Day 6: Validation Node

#### Tasks
1. **Schema Validation** (1 hour)
   - `src/nodes/validate_data.py`:
     - Verify all required fields present
     - Check data types (days must be Decimal)
     - Ensure dates are valid

2. **Business Rules Validation** (2 hours)
   - Fetch client contract data
   - Verify contract is active
   - Check daily rates exist for each consultant
   - Verify billing period within contract dates

3. **Amount Validation** (2 hours)
   - Calculate totals: `days × daily_rate` per consultant
   - Sum all consultant totals
   - Calculate tax (configurable rate, default 20%)
   - Verify no rounding errors
   - Build line items for invoice

4. **Unit Tests** (1 hour)
   - Test valid data passes
   - Test invalid data fails (missing fields, wrong types)
   - Test business rule violations
   - Test amount calculation accuracy

**Acceptance Criteria:**
- ✅ Schema validation catches all invalid data
- ✅ Business rules enforced correctly
- ✅ Amount calculations accurate to 2 decimal places
- ✅ Tax calculation configurable
- ✅ Unit tests pass

**Deliverable:** Working validation node with tests

---

### Day 7: Invoice Generation Node

#### Tasks
1. **Invoice Creation Logic** (3 hours)
   - `src/nodes/generate_invoice.py`:
     - Build invoice payload from validated data
     - Call `create_invoice()` on BoondManager API
     - Handle response (extract invoice ID and reference)
     - Update state with invoice details

2. **CRA Validation Logic** (1 hour)
   - Iterate through consultants
   - Call `update_cra_status(cra_id, "validated")` for each
   - Log validation confirmations

3. **Error Handling** (1 hour)
   - Handle invoice creation failures
   - Rollback logic (if invoice fails, don't validate CRAs)
   - Clear error messages

4. **Unit Tests** (1 hour)
   - Test successful invoice creation
   - Test invoice creation failure
   - Test CRA validation
   - Test error handling

**Acceptance Criteria:**
- ✅ Invoice created successfully in BoondManager
- ✅ Invoice ID and reference captured
- ✅ All CRAs marked as validated
- ✅ Errors handled gracefully
- ✅ Unit tests pass

**Deliverable:** Working invoice generation node with tests

---

### Day 8: Email Notification System

#### Tasks
1. **Email Templates** (2 hours)
   - `src/templates/success_notification.html`:
     ```html
     Subject: Invoice {{ invoice_reference }} - {{ billing_period }}

     Dear Client,

     Your invoice for {{ billing_period }} has been generated.

     Invoice Details:
     - Reference: {{ invoice_reference }}
     - Total: €{{ total_incl_tax }} (incl. VAT)
     - Due Date: {{ due_date }}

     Consultant Breakdown:
     {% for item in line_items %}
     - {{ item.consultant }}: {{ item.days }} days @ €{{ item.rate }}/day = €{{ item.total }}
     {% endfor %}
     ```

   - `src/templates/discrepancy_notification.html`:
     ```html
     Subject: Timesheet Discrepancy - {{ billing_period }}

     Hi {{ consultant_name }},

     We found a discrepancy in your timesheet for {{ billing_period }}:
     - Client reported: {{ client_days }} days
     - Your CRA shows: {{ cra_days }} days
     - Difference: {{ difference }} days

     Please review and correct your timesheet.
     ```

2. **Notification Node** (2 hours)
   - `src/nodes/send_notifications.py`:
     - Render templates with Jinja2
     - Send emails via SMTP
     - Logic: Send success email if `status == "completed"`, discrepancy email if `status == "failed"`

3. **Email Client Enhancement** (1 hour)
   - SMTP connection and authentication
   - Email sending function
   - Attachment support (for invoice PDF - optional)

4. **Unit Tests** (1 hour)
   - Test template rendering
   - Test email sending (mock SMTP)
   - Test both success and discrepancy scenarios

**Acceptance Criteria:**
- ✅ Email templates render correctly
- ✅ Emails send successfully via SMTP
- ✅ Success emails sent on completion
- ✅ Discrepancy emails sent on mismatch
- ✅ Unit tests pass

**Deliverable:** Working email notification system

---

### Day 9: LangGraph Workflow Assembly

#### Tasks
1. **Workflow Graph Construction** (2 hours)
   - `src/workflow.py`:
     ```python
     from langgraph.graph import StateGraph, END

     builder = StateGraph(InvoiceWorkflowState)

     # Add nodes
     builder.add_node("extract_email", extract_email_node)
     builder.add_node("reconcile_cra", reconcile_cra_node)
     builder.add_node("validate_data", validate_data_node)
     builder.add_node("generate_invoice", generate_invoice_node)
     builder.add_node("send_notifications", send_notifications_node)

     # Define flow
     builder.set_entry_point("extract_email")
     builder.add_edge("extract_email", "reconcile_cra")

     # Conditional routing
     builder.add_conditional_edges(
         "reconcile_cra",
         lambda state: "validate" if state["all_matched"] else "notify",
         {"validate": "validate_data", "notify": "send_notifications"}
     )

     builder.add_edge("validate_data", "generate_invoice")
     builder.add_edge("generate_invoice", "send_notifications")
     builder.add_edge("send_notifications", END)

     # Compile WITHOUT checkpointer
     graph = builder.compile()
     ```

2. **Main Entry Point** (1 hour)
   - `main.py`:
     - Load environment variables
     - Fetch unread emails
     - For each email:
       - Parse email
       - Initialize state
       - Execute workflow: `graph.invoke(initial_state)`
       - Log results

3. **Retry Policy Configuration** (1 hour)
   - Add `RetryPolicy` to reconciliation and invoice generation nodes
   - Configure backoff parameters

4. **Integration Test** (2 hours)
   - End-to-end test: Email → Invoice
   - Test with matching data (success path)
   - Test with mismatching data (discrepancy path)
   - Verify state transitions

**Acceptance Criteria:**
- ✅ Workflow graph compiles successfully
- ✅ Conditional routing works correctly
- ✅ Retry policies applied to correct nodes
- ✅ End-to-end test passes for both success and discrepancy paths
- ✅ No unhandled errors

**Deliverable:** Complete working LangGraph workflow

---

### Day 10: Testing, Documentation & Deployment

#### Tasks
1. **Comprehensive Testing** (3 hours)
   - **Unit Tests**: Run all unit tests, ensure >90% coverage
   - **Integration Tests**:
     - Test with real BoondManager sandbox
     - Test email parsing variations
     - Test error scenarios (API timeout, auth failure, missing data)
   - **End-to-End Test**:
     - Process real client email
     - Verify invoice created
     - Verify CRAs updated
     - Verify emails sent

2. **Bug Fixes & Refinements** (2 hours)
   - Address any issues found during testing
   - Refine error messages
   - Improve logging

3. **Documentation** (1 hour)
   - **README.md**:
     - Installation instructions
     - Configuration guide
     - Usage examples
     - Troubleshooting
   - **API Documentation**:
     - Document all node functions
     - Document state schema
     - Document configuration options

4. **Deployment** (30 min)
   - Package application
   - Create deployment script
   - Document deployment steps

**Acceptance Criteria:**
- ✅ All tests pass (unit + integration + e2e)
- ✅ Test coverage >90%
- ✅ Documentation complete and clear
- ✅ Deployment successful
- ✅ MVP ready for production use

**Deliverable:** Production-ready MVP

---

## Testing Strategy

### Unit Tests (Per Node)
```python
# Example: tests/unit/test_reconcile_cra.py
@pytest.mark.asyncio
async def test_reconcile_matching_consultants():
    """Test reconciliation when all consultants match"""
    state = {
        "consultants": [
            {"name": "Jean Dupont", "days": Decimal("20")}
        ]
    }

    # Mock BoondManager responses
    with patch('src.integrations.boond_client.get_consultant_by_name') as mock_lookup:
        mock_lookup.return_value = {"id": "consultant-789"}

        with patch('src.integrations.boond_client.get_cra_data') as mock_cra:
            mock_cra.return_value = {"id": "cra-12345", "total_days": Decimal("20")}

            result = await reconcile_cra_node(state)

            assert result["all_matched"] == True
            assert len(result["discrepancies"]) == 0
```

### Integration Tests
```python
# tests/integration/test_boond_integration.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_reconciliation_flow():
    """Test complete flow against BoondManager sandbox"""
    # Requires BOOND_SANDBOX_API_KEY in environment
    # Test with real API calls
    pass
```

### End-to-End Tests
```python
# tests/e2e/test_workflow.py
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_workflow_success():
    """Test complete workflow from email to invoice"""
    # Parse real email
    # Execute workflow
    # Verify invoice created
    # Verify CRAs validated
    # Verify emails sent
    pass
```

---

## Risk Mitigation

### High Risk: Email Parsing Failures
**Mitigation:**
- Start with strict regex patterns
- Add validation for extracted data
- Log unparseable emails for manual review
- **Fallback**: Manual processing for complex emails

### High Risk: BoondManager API Downtime
**Mitigation:**
- Retry with exponential backoff (implemented)
- Email alert on critical failures
- **Fallback**: Queue emails for later retry (post-MVP)

### Medium Risk: Consultant Name Matching Ambiguity
**Mitigation:**
- Use exact first + last name matching
- Log when multiple consultants match
- **Fallback**: Manual disambiguation

### Medium Risk: Rate Limit Exceeded
**Mitigation:**
- Respect API rate limits (100 req/min)
- Add delay between API calls if needed
- **Fallback**: Process emails in smaller batches

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests pass (unit + integration + e2e)
- [ ] Code review completed
- [ ] Environment variables documented
- [ ] BoondManager production credentials obtained
- [ ] Email server production credentials obtained

### Deployment Steps
1. **Setup Production Environment**
   ```bash
   git clone <repository>
   cd boondmanager-multiagent
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp config/.env.example .env
   # Edit .env with production credentials
   ```

3. **Test Production Connectivity**
   ```bash
   python -c "from src.integrations.boond_client import BoondManagerClient; import asyncio; asyncio.run(BoondManagerClient().test_connection())"
   ```

4. **Run Application**
   ```bash
   python main.py
   ```

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Verify first invoice created successfully
- [ ] Verify emails sent correctly
- [ ] Document any issues encountered

---

## Success Metrics

### MVP Completion Criteria
- ✅ Process 1 client email end-to-end
- ✅ Detect discrepancies with 100% accuracy
- ✅ Generate valid invoice in BoondManager
- ✅ Response time <30 seconds
- ✅ Handle API errors gracefully
- ✅ Zero infrastructure setup required

### Performance Targets
- **Latency**: <30 seconds per workflow
- **Accuracy**: 100% discrepancy detection
- **Reliability**: Handle transient errors (retry 3x)
- **Simplicity**: Single Python script deployment

---

## Next Steps (Post-MVP)

### Stage 2: Add Persistence (Weeks 3-4)
- Implement PostgreSQL checkpointing
- Add Redis caching for API responses
- Enable workflow recovery and time travel

### Stage 3: Enhanced Reconciliation (Weeks 5-6)
- Parallel consultant processing
- Advanced discrepancy detection
- Pattern analysis

### Stage 4: Human-in-the-Loop (Weeks 7-8)
- Approval gates for high-value transactions
- Interactive discrepancy resolution

---

## Appendix A: File Structure

```
boondmanager-multiagent/
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── state.py                # Pydantic models
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── extract_email.py        # Email parser node
│   │   ├── reconcile_cra.py        # Reconciliation node
│   │   ├── validate_data.py        # Validation node
│   │   ├── generate_invoice.py     # Invoice generation node
│   │   └── send_notifications.py   # Notification node
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── boond_client.py         # BoondManager API client
│   │   └── email_client.py         # IMAP/SMTP client
│   ├── templates/
│   │   ├── success_notification.html
│   │   └── discrepancy_notification.html
│   └── workflow.py                 # LangGraph workflow
├── tests/
│   ├── unit/
│   │   ├── test_extract_email.py
│   │   ├── test_reconcile_cra.py
│   │   ├── test_validate_data.py
│   │   ├── test_generate_invoice.py
│   │   └── test_send_notifications.py
│   ├── integration/
│   │   └── test_boond_integration.py
│   ├── e2e/
│   │   └── test_workflow.py
│   └── fixtures/
│       ├── sample_emails.txt
│       └── mock_api_responses.json
├── config/
│   └── .env.example
├── docs/
│   ├── MVP_ARCHITECTURE.md
│   └── IMPLEMENTATION_PLAN.md
├── requirements.txt
├── main.py
└── README.md
```

---

## Appendix B: Dependencies

```txt
# requirements.txt
langgraph>=0.2.0
httpx>=0.27.0
pydantic>=2.0.0
jinja2>=3.1.0
python-dotenv>=1.0.0

# Development dependencies
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.0.0
```

---

## Appendix C: Environment Variables

```bash
# .env.example

# BoondManager API
BOOND_API_KEY=your_api_key_here
BOOND_BASE_URL=https://api.boondmanager.com/api/v3
BOOND_TIMEOUT=30

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=billing@company.com
SMTP_PASSWORD=your_password_here
SMTP_USE_TLS=true

IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=billing@company.com
IMAP_PASSWORD=your_password_here

# Application Configuration
TAX_RATE=0.20
DEFAULT_PAYMENT_TERMS_DAYS=30
LOG_LEVEL=INFO
```

---

## Conclusion

This implementation plan provides a **day-by-day roadmap** to build the MVP in **2 weeks**. Each day has:
- Clear tasks with time estimates
- Acceptance criteria for quality gates
- Specific deliverables

**Key Success Factors:**
1. Resolve pre-implementation blockers (authentication, API endpoints)
2. Follow the plan sequentially (dependencies matter)
3. Test continuously (unit tests from Day 1)
4. Keep it simple (no over-engineering)

**Ready to start?** Address the pre-implementation checklist, then begin Day 1.
