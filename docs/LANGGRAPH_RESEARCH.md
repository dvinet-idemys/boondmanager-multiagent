# LangGraph State Management, Persistence, and Checkpointing Research
## Financial Workflows Implementation Guide

**Research Date:** October 2025
**LangGraph Version Context:** v0.2+ (v1.0 releasing October 2025)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [State Management](#state-management)
3. [Persistence & Checkpointing](#persistence--checkpointing)
4. [Error Handling & Recovery](#error-handling--recovery)
5. [Conditional Routing](#conditional-routing)
6. [Financial Workflow Patterns](#financial-workflow-patterns)
7. [Production Considerations](#production-considerations)
8. [Code Examples](#code-examples)
9. [Limitations & Best Practices](#limitations--best-practices)

---

## Executive Summary

LangGraph provides robust state management and persistence capabilities suitable for financial workflows requiring:
- **Full audit trail** through checkpoint history
- **Rollback capabilities** via time travel and state updates
- **Transaction-like semantics** through transactional supersteps
- **Error recovery** with automatic retry policies
- **Human-in-the-loop** approval workflows
- **Validation** at each step using Pydantic or custom validators

### Key Capabilities for Financial Operations

✅ **Ability to rollback on errors** - Time travel to previous checkpoints
✅ **Full audit trail** - Complete checkpoint history with metadata
✅ **Validation at each step** - Pydantic models, ValidationNode, custom validators
✅ **Retry failed operations** - Configurable retry policies
✅ **Clear error propagation** - Transactional supersteps with rollback

---

## State Management

### 1. State Schema Design Patterns

LangGraph supports three primary schema types:

#### **TypedDict (Recommended for Performance)**
```python
from typing import TypedDict, Annotated, NotRequired
from operator import add

class FinancialState(TypedDict):
    transaction_id: str
    amount: float
    status: str  # "pending", "validated", "approved", "rejected"
    validation_errors: Annotated[list[str], add]  # Accumulates errors
    audit_trail: Annotated[list[dict], add]  # Accumulates audit entries
    retry_count: NotRequired[int]  # Optional field
```

**Benefits:**
- Python stdlib, no dependencies
- Best performance
- Flexible development

**Use when:** Performance is critical and you don't need recursive validation

#### **Pydantic BaseModel (Recommended for Validation)**
```python
from pydantic import BaseModel, Field, field_validator
from typing import Annotated, Sequence
from decimal import Decimal
from operator import add

class Transaction(BaseModel):
    id: str
    amount: Decimal = Field(ge=0, description="Must be non-negative")
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    account_from: str
    account_to: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v > Decimal("1000000"):
            raise ValueError("Transaction exceeds maximum limit")
        return v

class FinancialState(BaseModel):
    transactions: Annotated[list[Transaction], add]
    total_amount: Decimal = Field(default=Decimal(0))
    status: str = "pending"
    error_count: int = 0
```

**Benefits:**
- Recursive data validation
- Field validators for complex business rules
- Type coercion and validation
- Clear error messages

**Use when:** Data validation is critical (financial operations, compliance)

**⚠️ Note:** Pydantic is less performant than TypedDict but essential for financial data integrity

#### **Dataclass (For Default Values)**
```python
from dataclasses import dataclass, field
from typing import Annotated
from operator import add

@dataclass
class FinancialState:
    transaction_id: str
    amount: float
    status: str = "pending"
    errors: Annotated[list[str], add] = field(default_factory=list)
    retry_count: int = 0
```

---

### 2. State Update Mechanisms

#### **Default Behavior (Overwrite)**
```python
class State(TypedDict):
    status: str  # Each update overwrites the previous value
```

#### **Custom Reducers**
```python
from typing import Annotated
from operator import add

def merge_validation_results(left: dict | None, right: dict | None) -> dict:
    """Merge validation results from multiple validators"""
    if not left:
        left = {}
    if not right:
        right = {}

    merged = left.copy()
    for key, value in right.items():
        if key in merged and isinstance(merged[key], list):
            merged[key].extend(value)
        else:
            merged[key] = value
    return merged

class State(TypedDict):
    # Simple concatenation
    errors: Annotated[list[str], add]

    # Custom merge logic
    validation_results: Annotated[dict, merge_validation_results]

    # Built-in message handling
    messages: Annotated[list, add_messages]
```

#### **add_messages Reducer (For Message Handling)**
```python
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from typing import Annotated

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

**Features:**
- Tracks message IDs
- Intelligent updates (modify existing messages by ID)
- Automatic deserialization

---

### 3. State Immutability

**Key Principle:** State in LangGraph is immutable - original data is never modified.

**Benefits:**
- **Race conditions impossible** - Multiple nodes can run in parallel safely
- **State history preserved** - Essential for audit trails
- **Deterministic results** - Same input always produces same output
- **Parallel execution** - Multiple nodes process simultaneously without conflicts

```python
# LangGraph automatically creates new immutable state
def node_function(state: State) -> dict:
    # Return updates, don't modify state directly
    return {
        "status": "validated",
        "errors": ["New error"]  # Reducer will merge with existing
    }
```

---

### 4. State Validation Approaches

#### **Using Pydantic ValidationNode**
```python
from pydantic import BaseModel, field_validator
from langgraph.prebuilt import ValidationNode
from langchain_core.messages import AIMessage

class TransactionApproval(BaseModel):
    transaction_id: str
    amount: float
    approved: bool

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v > 1000000:
            raise ValueError("Amount exceeds approval limit")
        return v

# Create validation node
validation_node = ValidationNode([TransactionApproval])

# Use in graph
builder.add_node("validate_transaction", validation_node)
```

#### **Custom Validation in Nodes**
```python
def validate_transaction(state: FinancialState) -> dict:
    """Custom validation logic"""
    errors = []

    # Business rule validation
    if state["amount"] > 100000 and state["approval_level"] < 3:
        errors.append("High-value transaction requires level 3 approval")

    # Compliance validation
    if state["country"] in SANCTIONED_COUNTRIES:
        errors.append(f"Transactions to {state['country']} are restricted")

    # Data integrity validation
    if state["amount"] != sum(item["amount"] for item in state["items"]):
        errors.append("Transaction amount doesn't match line items")

    if errors:
        return {
            "status": "validation_failed",
            "errors": errors,
            "error_count": state.get("error_count", 0) + 1
        }

    return {
        "status": "validated",
        "validation_timestamp": datetime.utcnow().isoformat()
    }
```

---

## Persistence & Checkpointing

### 1. Checkpointing Fundamentals

**Checkpoint:** A snapshot of graph state at a specific point in time (super-step)

**Thread:** A unique identifier tracking accumulated state across graph runs

**Super-step:** One full iteration of the graph (all nodes at a given step execute, then checkpoint is saved)

```python
from langgraph.checkpoint.memory import InMemorySaver

# Create checkpointer
checkpointer = InMemorySaver()

# Compile graph with checkpointing
graph = workflow.compile(checkpointer=checkpointer)

# Execute with thread ID
config = {"configurable": {"thread_id": "txn_12345"}}
result = graph.invoke({"amount": 1000}, config)
```

**Checkpoint Contents:**
- Configuration (thread_id, checkpoint_id)
- Metadata (source: "input"/"loop"/"update"/"fork")
- State channel values (all state data)
- Next nodes to execute
- Task information

---

### 2. Checkpointer Libraries

#### **InMemorySaver - Development Only**
```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

**Use case:** Testing, debugging, experimentation
**⚠️ Warning:** Data lost on restart - NOT for production

#### **SqliteSaver - Local Workflows**
```python
from langgraph.checkpoint.sqlite import SqliteSaver

# Installation: pip install langgraph-checkpoint-sqlite

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    # Setup schema (first time only)
    checkpointer.setup()

    graph = workflow.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread-1"}}
    result = graph.invoke(input_data, config)
```

**Use case:** Local development, small applications, file-based persistence
**Limitations:** Single-process, limited concurrency

#### **PostgresSaver - Production (Recommended)**
```python
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

# Installation: pip install langgraph-checkpoint-postgres

DB_URI = "postgresql://user:password@localhost:5432/langgraph"

# Create connection pool (recommended)
pool = ConnectionPool(
    conninfo=DB_URI,
    max_size=20,
    kwargs={"autocommit": True, "row_factory": dict_row}
)

# Use connection pool
with pool.connection() as conn:
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()  # First time only

    graph = workflow.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "txn_12345"}}
    result = graph.invoke(input_data, config)
```

**Benefits:**
- Optimized for production use (used in LangGraph Cloud)
- Connection pooling support (v1.0.4+)
- Full concurrency support
- High scalability
- ACID compliance

**⚠️ Best Practice:** Create a global connection pool and reuse connections across requests

#### **Comparison Table**

| Feature | InMemorySaver | SqliteSaver | PostgresSaver |
|---------|---------------|-------------|---------------|
| **Persistence** | None | File-based | Database |
| **Production Ready** | ❌ No | ⚠️ Limited | ✅ Yes |
| **Concurrency** | Single process | Limited | Full |
| **Scalability** | Low | Low | High |
| **ACID** | ❌ | ✅ | ✅ |
| **Setup Complexity** | None | Low | Medium |
| **Cost** | Free | Free | Database costs |
| **Use Case** | Dev/Test | Local apps | Production |

---

### 3. State History & Audit Trail

#### **Retrieving Checkpoint History**
```python
# Get state history (reverse chronological order)
config = {"configurable": {"thread_id": "txn_12345"}}
states = list(graph.get_state_history(config))

for state in states:
    print(f"Checkpoint ID: {state.config['configurable']['checkpoint_id']}")
    print(f"Next nodes: {state.next}")
    print(f"State values: {state.values}")
    print(f"Metadata: {state.metadata}")
    print("---")
```

#### **Building Audit Trail**
```python
def build_audit_trail(thread_id: str) -> list[dict]:
    """Build complete audit trail for a transaction"""
    config = {"configurable": {"thread_id": thread_id}}
    states = list(graph.get_state_history(config))

    audit_trail = []
    for state in reversed(states):  # Chronological order
        audit_entry = {
            "checkpoint_id": state.config["configurable"]["checkpoint_id"],
            "timestamp": state.metadata.get("timestamp"),
            "source": state.metadata.get("source"),  # input/loop/update/fork
            "status": state.values.get("status"),
            "amount": state.values.get("amount"),
            "errors": state.values.get("errors", []),
            "next_step": state.next
        }
        audit_trail.append(audit_entry)

    return audit_trail

# Generate audit report
audit_trail = build_audit_trail("txn_12345")
```

**Checkpoint Metadata Sources:**
- `"input"` - Checkpoint from invoke/stream/batch call
- `"loop"` - Checkpoint from inside pregel loop (normal execution)
- `"update"` - Checkpoint from manual state update
- `"fork"` - Checkpoint copied from another checkpoint

---

### 4. Time Travel & Rollback

#### **Basic Time Travel Pattern**
```python
# 1. Get state history
config = {"configurable": {"thread_id": "txn_12345"}}
states = list(graph.get_state_history(config))

# 2. Select a checkpoint (e.g., before error occurred)
selected_state = states[2]  # Third most recent

# 3. Resume from that checkpoint
result = graph.invoke(None, selected_state.config)
```

#### **Rollback with State Modification**
```python
# 1. Find checkpoint before error
states = list(graph.get_state_history(config))
checkpoint_before_error = states[1]

# 2. Update state at that checkpoint
new_config = graph.update_state(
    checkpoint_before_error.config,
    values={
        "amount": 5000,  # Correct the amount
        "status": "pending",  # Reset status
        "errors": []  # Clear errors
    }
)

# 3. Resume execution from corrected state
result = graph.invoke(None, new_config)
```

#### **Fork Execution Path**
```python
# Create alternative execution path
config = {"configurable": {"thread_id": "txn_12345"}}
states = list(graph.get_state_history(config))

# Fork from specific checkpoint
checkpoint_to_fork = states[3]
forked_config = graph.update_state(
    checkpoint_to_fork.config,
    values={"approval_method": "manual"}  # Try different approach
)

# New checkpoint_id created for forked path
print(f"Original: {checkpoint_to_fork.config['configurable']['checkpoint_id']}")
print(f"Forked: {forked_config['configurable']['checkpoint_id']}")

# Execute forked path
result = graph.invoke(None, forked_config)
```

#### **Complete Rollback Example for Financial Workflow**
```python
def rollback_transaction(thread_id: str, reason: str) -> dict:
    """Rollback transaction to last stable state"""
    config = {"configurable": {"thread_id": thread_id}}
    states = list(graph.get_state_history(config))

    # Find last stable checkpoint
    stable_checkpoint = None
    for state in states:
        if state.values.get("status") in ["validated", "approved"]:
            stable_checkpoint = state
            break

    if not stable_checkpoint:
        raise ValueError("No stable checkpoint found")

    # Update state with rollback info
    rollback_config = graph.update_state(
        stable_checkpoint.config,
        values={
            "status": "rolled_back",
            "rollback_reason": reason,
            "rollback_timestamp": datetime.utcnow().isoformat(),
            "errors": [f"Rolled back: {reason}"]
        }
    )

    return {
        "thread_id": thread_id,
        "rolled_back_to": stable_checkpoint.config["configurable"]["checkpoint_id"],
        "new_checkpoint": rollback_config["checkpoint_id"],
        "reason": reason
    }
```

---

## Error Handling & Recovery

### 1. Transactional Supersteps

**Key Concept:** LangGraph executes nodes in "supersteps" with transaction-like semantics.

**Behavior:**
- All nodes in a superstep execute in parallel
- If ANY node raises an exception, the ENTIRE superstep rolls back
- However, when using checkpointer: successful node results are saved as pending writes
- When resuming, successfully completed nodes don't re-execute

```python
# Superstep 1: validate_amount, validate_account
# If validate_account fails, validate_amount results are saved but not applied
# When resumed, only validate_account re-executes
```

**This provides:**
- Automatic rollback on errors
- No partial state updates
- Efficient retry (only failed nodes re-execute)

---

### 2. Retry Policies

#### **Default Retry Policy**
```python
from langgraph.types import RetryPolicy

# Default behavior: retry on most exceptions
# Excludes: KeyboardInterrupt, SystemExit, certain framework exceptions
builder.add_node("process_payment", process_payment_node)
```

#### **Custom Retry Policy**
```python
import sqlite3
from langgraph.types import RetryPolicy

# Retry only on specific exceptions
retry_policy = RetryPolicy(
    retry_on=sqlite3.OperationalError,  # Single exception
    max_attempts=3,
    initial_interval=1.0,  # seconds
    backoff_factor=2.0,  # exponential backoff
    max_interval=60.0
)

builder.add_node(
    "database_operation",
    database_node,
    retry_policy=retry_policy
)
```

#### **Multiple Exception Types**
```python
from requests.exceptions import RequestException, Timeout
from langgraph.types import RetryPolicy

retry_policy = RetryPolicy(
    retry_on=(RequestException, Timeout, ConnectionError),
    max_attempts=5
)

builder.add_node(
    "external_api_call",
    api_node,
    retry_policy=retry_policy
)
```

#### **Financial Transaction Retry Example**
```python
class TransientError(Exception):
    """Temporary error that can be retried"""
    pass

class PermanentError(Exception):
    """Permanent error that should not be retried"""
    pass

def process_transaction(state: FinancialState) -> dict:
    """Process financial transaction with error handling"""
    try:
        # Attempt transaction
        result = external_payment_gateway.process(
            amount=state["amount"],
            account=state["account"]
        )

        return {
            "status": "completed",
            "transaction_ref": result["ref"]
        }

    except ExternalAPITimeout:
        # Transient error - will retry
        raise TransientError("Payment gateway timeout") from None

    except InsufficientFunds:
        # Permanent error - should not retry
        raise PermanentError("Insufficient funds") from None

# Configure retry only for transient errors
retry_policy = RetryPolicy(
    retry_on=TransientError,
    max_attempts=3,
    initial_interval=2.0,
    backoff_factor=2.0
)

builder.add_node(
    "process_transaction",
    process_transaction,
    retry_policy=retry_policy
)
```

**⚠️ Important:** If all retry attempts fail, graph execution stops immediately.

---

### 3. Error Detection Patterns

#### **Error State Tracking**
```python
class FinancialState(TypedDict):
    status: str
    error_count: int
    last_error: NotRequired[str]
    error_history: Annotated[list[dict], add]

def handle_error(state: FinancialState, error: Exception) -> dict:
    """Track error in state"""
    return {
        "status": "error",
        "error_count": state.get("error_count", 0) + 1,
        "last_error": str(error),
        "error_history": [{
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "checkpoint_id": state.get("checkpoint_id")
        }]
    }
```

#### **Node-Level Error Handling**
```python
def validate_transaction_with_error_handling(state: FinancialState) -> dict:
    """Validate transaction with explicit error handling"""
    try:
        # Validation logic
        if state["amount"] <= 0:
            raise ValueError("Amount must be positive")

        if state["amount"] > 1000000:
            raise ValueError("Amount exceeds maximum limit")

        # External validation
        result = compliance_api.validate(state["account"])
        if not result.valid:
            raise ValueError(f"Compliance check failed: {result.reason}")

        return {
            "status": "validated",
            "validation_timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        # Business logic error - log and update state
        return {
            "status": "validation_failed",
            "errors": [str(e)],
            "error_count": state.get("error_count", 0) + 1
        }

    except Exception as e:
        # Unexpected error - let retry policy handle it
        raise
```

---

### 4. Recovery Strategies

#### **Graceful Degradation**
```python
def process_with_fallback(state: FinancialState) -> dict:
    """Try primary method, fall back to secondary"""
    try:
        # Primary processing method
        result = primary_payment_processor.process(state)
        return {"status": "completed", "processor": "primary"}

    except PrimaryProcessorError:
        # Fall back to secondary processor
        try:
            result = secondary_payment_processor.process(state)
            return {"status": "completed", "processor": "secondary"}
        except Exception as e:
            return {
                "status": "failed",
                "errors": [f"All processors failed: {str(e)}"]
            }
```

#### **Circuit Breaker Pattern (Custom Implementation)**
```python
from datetime import datetime, timedelta
from typing import Optional

class CircuitBreaker:
    """Circuit breaker for external service calls"""
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"

            raise

# Usage in node
payment_circuit = CircuitBreaker(failure_threshold=3, timeout=60)

def process_payment(state: FinancialState) -> dict:
    try:
        result = payment_circuit.call(
            external_payment_api.process,
            state["amount"],
            state["account"]
        )
        return {"status": "completed", "result": result}
    except Exception as e:
        return {
            "status": "circuit_open",
            "errors": [f"Payment service unavailable: {str(e)}"]
        }
```

---

## Conditional Routing

### 1. Conditional Edges

#### **Basic Conditional Routing**
```python
from typing import Literal

def route_by_status(state: FinancialState) -> Literal["approve", "reject", "review"]:
    """Route based on transaction status"""
    if state["status"] == "validated":
        if state["amount"] < 10000:
            return "approve"
        else:
            return "review"
    return "reject"

# Add conditional edge
builder.add_conditional_edges(
    "validate",  # Source node
    route_by_status,  # Routing function
    {
        "approve": "approve_node",
        "reject": "reject_node",
        "review": "human_review_node"
    }
)
```

#### **Multi-Path Routing**
```python
from typing import Sequence

def route_validation_checks(state: FinancialState) -> Sequence[str]:
    """Route to multiple validation nodes in parallel"""
    checks = []

    if state["amount"] > 1000:
        checks.append("fraud_check")

    if state["country"] in HIGH_RISK_COUNTRIES:
        checks.append("compliance_check")

    if state["customer_type"] == "new":
        checks.append("identity_verification")

    # All checks run in parallel
    return checks

builder.add_conditional_edges(
    "initial_validation",
    route_validation_checks,
    ["fraud_check", "compliance_check", "identity_verification", "finalize"]
)
```

#### **Loop Handling**
```python
def route_with_retry(state: FinancialState) -> Literal["retry", "fail", "succeed"]:
    """Implement retry logic with conditional routing"""
    if state["status"] == "success":
        return "succeed"

    if state.get("error_count", 0) >= 3:
        return "fail"

    return "retry"

builder.add_conditional_edges(
    "process_transaction",
    route_with_retry,
    {
        "retry": "process_transaction",  # Loop back
        "fail": "handle_failure",
        "succeed": END
    }
)
```

---

### 2. Command Pattern for Dynamic Routing

#### **Basic Command Usage**
```python
from langgraph.types import Command

def process_with_routing(state: FinancialState) -> Command:
    """Combine state updates with routing decision"""

    # Validate transaction
    if state["amount"] > 100000:
        return Command(
            update={"status": "requires_approval", "approval_level": 3},
            goto="high_value_approval"
        )
    else:
        return Command(
            update={"status": "approved"},
            goto="process_payment"
        )
```

#### **Subgraph Navigation**
```python
def route_to_parent_graph(state: FinancialState) -> Command:
    """Navigate from subgraph to parent graph"""
    return Command(
        update={"validation_complete": True},
        goto="parent_node",
        graph=Command.PARENT  # Navigate to parent graph
    )
```

#### **Command with Error Handling**
```python
def validate_and_route(state: FinancialState) -> Command:
    """Validation with dynamic routing"""
    errors = []

    # Perform validations
    if state["amount"] <= 0:
        errors.append("Amount must be positive")

    if not state.get("account"):
        errors.append("Account is required")

    if errors:
        return Command(
            update={
                "status": "validation_failed",
                "errors": errors,
                "error_count": state.get("error_count", 0) + 1
            },
            goto="handle_validation_error"
        )

    return Command(
        update={"status": "validated"},
        goto="process_transaction"
    )
```

---

### 3. Branch/Merge Patterns

#### **Parallel Validation with Merge**
```python
def parallel_validation_router(state: FinancialState) -> list[str]:
    """Route to parallel validations"""
    return ["validate_amount", "validate_account", "check_fraud"]

def merge_validations(state: FinancialState) -> dict:
    """Merge results from parallel validations"""
    all_errors = state.get("errors", [])

    if all_errors:
        return {
            "status": "validation_failed",
            "error_count": len(all_errors)
        }

    return {
        "status": "validated",
        "validation_complete": True
    }

# Build graph
builder.add_node("start", start_node)
builder.add_conditional_edges("start", parallel_validation_router)
builder.add_node("validate_amount", validate_amount_node)
builder.add_node("validate_account", validate_account_node)
builder.add_node("check_fraud", check_fraud_node)
builder.add_node("merge", merge_validations)

# All validations converge to merge
builder.add_edge("validate_amount", "merge")
builder.add_edge("validate_account", "merge")
builder.add_edge("check_fraud", "merge")
```

---

## Financial Workflow Patterns

### 1. Human-in-the-Loop Approval

#### **Dynamic Interrupt for Approval**
```python
from langgraph.types import interrupt, Command

def request_approval(state: FinancialState) -> Command:
    """Request human approval for high-value transaction"""

    if state["amount"] > 50000:
        # Interrupt for human review
        decision = interrupt({
            "question": "Approve this high-value transaction?",
            "transaction_id": state["transaction_id"],
            "amount": state["amount"],
            "account": state["account"],
            "risk_score": state.get("risk_score", 0)
        })

        if decision == "approve":
            return Command(
                update={
                    "status": "approved",
                    "approved_by": decision.get("user"),
                    "approved_at": datetime.utcnow().isoformat()
                },
                goto="process_payment"
            )
        else:
            return Command(
                update={
                    "status": "rejected",
                    "rejected_by": decision.get("user"),
                    "rejection_reason": decision.get("reason")
                },
                goto="handle_rejection"
            )

    # Auto-approve small transactions
    return Command(
        update={"status": "auto_approved"},
        goto="process_payment"
    )
```

#### **Review and Edit Pattern**
```python
def review_transaction_details(state: FinancialState) -> dict:
    """Allow human to review and edit transaction"""

    result = interrupt({
        "task": "Review transaction details and make corrections if needed",
        "current_details": {
            "amount": state["amount"],
            "account": state["account"],
            "description": state.get("description", "")
        }
    })

    return {
        "amount": result.get("amount", state["amount"]),
        "account": result.get("account", state["account"]),
        "description": result.get("description", state.get("description")),
        "reviewed_by": result.get("user"),
        "reviewed_at": datetime.utcnow().isoformat()
    }
```

#### **Executing Human-in-the-Loop Workflow**
```python
from langgraph.checkpoint.postgres import PostgresSaver

# Build graph with checkpointer
checkpointer = PostgresSaver.from_conn_string(DB_URI)
graph = workflow.compile(checkpointer=checkpointer)

# Initial execution
config = {"configurable": {"thread_id": "txn_12345"}}
try:
    result = graph.invoke({"amount": 75000, "account": "ACC_001"}, config)
except GraphInterrupt:
    # Expected - workflow is waiting for approval
    pass

# Get current state
state = graph.get_state(config)
print(f"Status: {state.values['status']}")
print(f"Waiting for: {state.next}")

# Human provides approval
result = graph.invoke(
    Command(resume="approve"),  # Resume with approval
    config
)
```

**⚠️ Important:**
- Interrupts require checkpointer
- Must specify thread_id
- Entire node re-executes when resuming
- Use `Command(resume=value)` to provide input

---

### 2. Multi-Stage Validation Pipeline

```python
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, END

class ValidationState(TypedDict):
    transaction_id: str
    amount: float
    account: str
    country: str

    # Validation results
    amount_valid: bool
    account_valid: bool
    fraud_check_passed: bool
    compliance_check_passed: bool

    # Error tracking
    errors: Annotated[list[str], add]
    validation_stage: str

def validate_amount(state: ValidationState) -> dict:
    """Stage 1: Amount validation"""
    if state["amount"] <= 0:
        return {
            "amount_valid": False,
            "errors": ["Amount must be positive"]
        }
    if state["amount"] > 1000000:
        return {
            "amount_valid": False,
            "errors": ["Amount exceeds maximum limit"]
        }
    return {"amount_valid": True, "validation_stage": "amount_validated"}

def validate_account(state: ValidationState) -> dict:
    """Stage 2: Account validation"""
    if not state["account"].startswith("ACC_"):
        return {
            "account_valid": False,
            "errors": ["Invalid account format"]
        }
    # Check account exists
    if not account_exists(state["account"]):
        return {
            "account_valid": False,
            "errors": ["Account not found"]
        }
    return {"account_valid": True, "validation_stage": "account_validated"}

def check_fraud(state: ValidationState) -> dict:
    """Stage 3: Fraud detection"""
    risk_score = fraud_detection_service.calculate_risk(
        amount=state["amount"],
        account=state["account"]
    )

    if risk_score > 0.7:
        return {
            "fraud_check_passed": False,
            "errors": [f"High fraud risk detected: {risk_score}"]
        }
    return {"fraud_check_passed": True, "validation_stage": "fraud_check_complete"}

def check_compliance(state: ValidationState) -> dict:
    """Stage 4: Compliance check"""
    if state["country"] in SANCTIONED_COUNTRIES:
        return {
            "compliance_check_passed": False,
            "errors": [f"Transactions to {state['country']} are restricted"]
        }
    return {"compliance_check_passed": True, "validation_stage": "compliance_complete"}

def route_validation(state: ValidationState) -> str:
    """Route based on validation results"""
    if state.get("errors"):
        return "failed"

    # Check which stage we're at
    if not state.get("amount_valid"):
        return "validate_amount"
    if not state.get("account_valid"):
        return "validate_account"
    if not state.get("fraud_check_passed"):
        return "check_fraud"
    if not state.get("compliance_check_passed"):
        return "check_compliance"

    return "approved"

# Build validation pipeline
builder = StateGraph(ValidationState)
builder.add_node("validate_amount", validate_amount)
builder.add_node("validate_account", validate_account)
builder.add_node("check_fraud", check_fraud)
builder.add_node("check_compliance", check_compliance)
builder.add_node("finalize", lambda s: {"validation_stage": "complete"})

# Sequential validation flow
builder.set_entry_point("validate_amount")
builder.add_conditional_edges(
    "validate_amount",
    lambda s: "failed" if s.get("errors") else "next",
    {"failed": END, "next": "validate_account"}
)
builder.add_conditional_edges(
    "validate_account",
    lambda s: "failed" if s.get("errors") else "next",
    {"failed": END, "next": "check_fraud"}
)
builder.add_conditional_edges(
    "check_fraud",
    lambda s: "failed" if s.get("errors") else "next",
    {"failed": END, "next": "check_compliance"}
)
builder.add_conditional_edges(
    "check_compliance",
    lambda s: "failed" if s.get("errors") else "next",
    {"failed": END, "next": "finalize"}
)
builder.add_edge("finalize", END)

# Compile with checkpointing
validation_graph = builder.compile(checkpointer=checkpointer)
```

---

### 3. Complete Financial Transaction Workflow

```python
from typing import TypedDict, Annotated, Literal
from operator import add
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from langgraph.graph import StateGraph, END
from langgraph.types import Command, interrupt
from langgraph.checkpoint.postgres import PostgresSaver

# Pydantic models for validation
class Transaction(BaseModel):
    id: str
    amount: Decimal = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    account_from: str
    account_to: str
    description: str = ""

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v > Decimal("1000000"):
            raise ValueError("Transaction exceeds maximum limit")
        return v

# State schema
class TransactionState(TypedDict):
    # Transaction details
    transaction: Transaction

    # Status tracking
    status: Literal[
        "pending", "validating", "validated",
        "awaiting_approval", "approved", "rejected",
        "processing", "completed", "failed", "rolled_back"
    ]

    # Validation results
    validation_errors: Annotated[list[str], add]
    risk_score: float

    # Approval tracking
    approval_required: bool
    approved_by: str | None
    approval_timestamp: str | None

    # Error handling
    error_count: int
    last_error: str | None

    # Audit trail
    audit_log: Annotated[list[dict], add]

def start_transaction(state: TransactionState) -> dict:
    """Initialize transaction"""
    return {
        "status": "pending",
        "audit_log": [{
            "timestamp": datetime.utcnow().isoformat(),
            "event": "transaction_initiated",
            "details": {"transaction_id": state["transaction"].id}
        }]
    }

def validate_transaction(state: TransactionState) -> dict:
    """Comprehensive validation"""
    errors = []

    try:
        # Pydantic validation happens automatically
        txn = state["transaction"]

        # Business rule validation
        if txn.account_from == txn.account_to:
            errors.append("Source and destination accounts must be different")

        # Check account balances
        balance = get_account_balance(txn.account_from)
        if balance < txn.amount:
            errors.append(f"Insufficient funds: {balance} < {txn.amount}")

        if errors:
            return {
                "status": "failed",
                "validation_errors": errors,
                "audit_log": [{
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "validation_failed",
                    "errors": errors
                }]
            }

        return {
            "status": "validated",
            "audit_log": [{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "validation_passed"
            }]
        }

    except Exception as e:
        return {
            "status": "failed",
            "validation_errors": [str(e)],
            "last_error": str(e),
            "error_count": state.get("error_count", 0) + 1
        }

def check_fraud(state: TransactionState) -> dict:
    """Fraud detection"""
    txn = state["transaction"]

    risk_score = fraud_detection_api.calculate_risk(
        amount=float(txn.amount),
        account_from=txn.account_from,
        account_to=txn.account_to
    )

    return {
        "risk_score": risk_score,
        "approval_required": risk_score > 0.5 or txn.amount > 50000,
        "audit_log": [{
            "timestamp": datetime.utcnow().isoformat(),
            "event": "fraud_check_complete",
            "risk_score": risk_score
        }]
    }

def request_approval(state: TransactionState) -> Command:
    """Human approval for high-risk transactions"""
    if not state.get("approval_required", False):
        return Command(
            update={"status": "approved"},
            goto="process_payment"
        )

    # Request human approval
    decision = interrupt({
        "question": "Approve this transaction?",
        "transaction_id": state["transaction"].id,
        "amount": float(state["transaction"].amount),
        "risk_score": state.get("risk_score", 0),
        "details": state["transaction"].dict()
    })

    if decision["action"] == "approve":
        return Command(
            update={
                "status": "approved",
                "approved_by": decision["user"],
                "approval_timestamp": datetime.utcnow().isoformat(),
                "audit_log": [{
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "transaction_approved",
                    "approved_by": decision["user"]
                }]
            },
            goto="process_payment"
        )
    else:
        return Command(
            update={
                "status": "rejected",
                "audit_log": [{
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "transaction_rejected",
                    "rejected_by": decision["user"],
                    "reason": decision.get("reason", "")
                }]
            },
            goto=END
        )

def process_payment(state: TransactionState) -> dict:
    """Execute payment"""
    try:
        txn = state["transaction"]

        result = payment_gateway.process(
            amount=float(txn.amount),
            account_from=txn.account_from,
            account_to=txn.account_to,
            description=txn.description
        )

        return {
            "status": "completed",
            "audit_log": [{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "payment_processed",
                "payment_ref": result["reference"]
            }]
        }

    except Exception as e:
        return {
            "status": "failed",
            "last_error": str(e),
            "error_count": state.get("error_count", 0) + 1,
            "audit_log": [{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "payment_failed",
                "error": str(e)
            }]
        }

def handle_error(state: TransactionState) -> dict:
    """Error recovery"""
    if state.get("error_count", 0) < 3:
        # Retry
        return {
            "status": "pending",
            "audit_log": [{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "retry_attempted",
                "attempt": state["error_count"]
            }]
        }
    else:
        # Give up
        return {
            "status": "failed",
            "audit_log": [{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "transaction_failed_permanently",
                "error": state.get("last_error")
            }]
        }

# Build graph
builder = StateGraph(TransactionState)

# Add nodes
builder.add_node("start", start_transaction)
builder.add_node("validate", validate_transaction)
builder.add_node("fraud_check", check_fraud)
builder.add_node("approval", request_approval)
builder.add_node("process", process_payment)
builder.add_node("error_handler", handle_error)

# Define flow
builder.set_entry_point("start")
builder.add_edge("start", "validate")

# Validation routing
builder.add_conditional_edges(
    "validate",
    lambda s: "passed" if s["status"] == "validated" else "failed",
    {"passed": "fraud_check", "failed": "error_handler"}
)

builder.add_edge("fraud_check", "approval")
# approval node uses Command for routing

# Error handling with retry
builder.add_conditional_edges(
    "error_handler",
    lambda s: "retry" if s["status"] == "pending" else "end",
    {"retry": "validate", "end": END}
)

# Process result routing
builder.add_conditional_edges(
    "process",
    lambda s: "completed" if s["status"] == "completed" else "error",
    {"completed": END, "error": "error_handler"}
)

# Compile with PostgreSQL checkpointer
DB_URI = "postgresql://user:password@localhost:5432/transactions"
checkpointer = PostgresSaver.from_conn_string(DB_URI)
transaction_graph = builder.compile(checkpointer=checkpointer)
```

**Usage:**
```python
# Execute transaction
from decimal import Decimal

transaction = Transaction(
    id="TXN_001",
    amount=Decimal("75000.00"),
    currency="USD",
    account_from="ACC_12345",
    account_to="ACC_67890",
    description="Large payment"
)

config = {"configurable": {"thread_id": "TXN_001"}}

try:
    result = transaction_graph.invoke(
        {"transaction": transaction, "error_count": 0},
        config
    )
except GraphInterrupt:
    # Waiting for approval
    print("Transaction requires approval")

    # Get current state
    state = transaction_graph.get_state(config)
    print(f"Risk score: {state.values['risk_score']}")

    # Provide approval
    result = transaction_graph.invoke(
        Command(resume={"action": "approve", "user": "manager_01"}),
        config
    )

# View audit trail
final_state = transaction_graph.get_state(config)
for entry in final_state.values["audit_log"]:
    print(f"{entry['timestamp']}: {entry['event']}")
```

---

## Production Considerations

### 1. Database Setup for PostgreSQL Checkpointer

```python
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

# Production configuration
DB_CONFIG = {
    "host": "postgres.example.com",
    "port": 5432,
    "dbname": "langgraph_prod",
    "user": "langgraph_user",
    "password": os.environ["POSTGRES_PASSWORD"],
    "sslmode": "require"
}

DB_URI = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}?sslmode={DB_CONFIG['sslmode']}"

# Create connection pool (reuse across requests)
pool = ConnectionPool(
    conninfo=DB_URI,
    min_size=5,
    max_size=20,
    timeout=30,
    max_idle=300,  # 5 minutes
    kwargs={
        "autocommit": True,
        "row_factory": dict_row
    }
)

# Initialize database schema (run once)
with pool.connection() as conn:
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()

# Use in application
def get_checkpointer():
    """Get checkpointer with pooled connection"""
    conn = pool.getconn()
    return PostgresSaver(conn)

# FastAPI example
from fastapi import FastAPI, Depends

app = FastAPI()

@app.post("/transaction")
async def create_transaction(
    transaction_data: dict,
    checkpointer: PostgresSaver = Depends(get_checkpointer)
):
    graph = workflow.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": transaction_data["id"]}}
    result = graph.invoke(transaction_data, config)
    return result
```

---

### 2. Error Recovery in Production

```python
def execute_with_recovery(
    graph,
    input_data: dict,
    thread_id: str,
    max_retries: int = 3
) -> dict:
    """Execute graph with automatic recovery"""
    config = {"configurable": {"thread_id": thread_id}}

    for attempt in range(max_retries):
        try:
            result = graph.invoke(input_data, config)
            return result

        except GraphRecursionError:
            # Graph hit recursion limit
            logger.error(f"Recursion limit hit for {thread_id}")
            raise

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")

            if attempt < max_retries - 1:
                # Get last checkpoint and retry
                state = graph.get_state(config)
                logger.info(f"Retrying from checkpoint: {state.config['configurable']['checkpoint_id']}")

                # Optional: Update state before retry
                graph.update_state(config, {"error_count": state.values.get("error_count", 0) + 1})

                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                # Final attempt failed - rollback
                logger.error(f"All retries exhausted for {thread_id}")
                rollback_transaction(graph, thread_id, str(e))
                raise

def rollback_transaction(graph, thread_id: str, reason: str):
    """Rollback to last stable state"""
    config = {"configurable": {"thread_id": thread_id}}
    states = list(graph.get_state_history(config))

    # Find last stable checkpoint
    for state in states:
        if state.values.get("status") in ["validated", "approved"]:
            graph.update_state(
                state.config,
                {
                    "status": "rolled_back",
                    "rollback_reason": reason,
                    "rollback_timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Rolled back {thread_id} to checkpoint {state.config['configurable']['checkpoint_id']}")
            return

    logger.warning(f"No stable checkpoint found for {thread_id}")
```

---

### 3. Monitoring and Observability

```python
import logging
from datetime import datetime

# Structured logging
logger = logging.getLogger("langgraph.financial")

def add_monitoring(graph, thread_id: str):
    """Add monitoring to graph execution"""

    def log_checkpoint(checkpoint):
        logger.info(
            "checkpoint_created",
            extra={
                "thread_id": thread_id,
                "checkpoint_id": checkpoint["checkpoint_id"],
                "status": checkpoint.get("status"),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # Stream with monitoring
    config = {"configurable": {"thread_id": thread_id}}

    for event in graph.stream(input_data, config, stream_mode="values"):
        # Log each state transition
        logger.info(
            "state_transition",
            extra={
                "thread_id": thread_id,
                "status": event.get("status"),
                "errors": event.get("errors", [])
            }
        )

        # Send metrics
        metrics.increment("langgraph.state_transitions")

        if event.get("errors"):
            metrics.increment("langgraph.validation_errors")

# Audit trail export
def export_audit_trail(graph, thread_id: str, format: str = "json") -> str:
    """Export complete audit trail"""
    config = {"configurable": {"thread_id": thread_id}}
    states = list(graph.get_state_history(config))

    audit_trail = []
    for state in reversed(states):
        audit_trail.append({
            "checkpoint_id": state.config["configurable"]["checkpoint_id"],
            "timestamp": state.metadata.get("timestamp"),
            "status": state.values.get("status"),
            "errors": state.values.get("errors", []),
            "audit_log": state.values.get("audit_log", [])
        })

    if format == "json":
        return json.dumps(audit_trail, indent=2)
    elif format == "csv":
        # Convert to CSV
        pass

    return audit_trail
```

---

### 4. Performance Optimization

```python
# Use connection pooling
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    conninfo=DB_URI,
    min_size=5,
    max_size=20,
    kwargs={"autocommit": True}
)

# Batch operations
def process_batch(transactions: list[dict]):
    """Process multiple transactions efficiently"""
    results = []

    with pool.connection() as conn:
        checkpointer = PostgresSaver(conn)
        graph = workflow.compile(checkpointer=checkpointer)

        for txn in transactions:
            config = {"configurable": {"thread_id": txn["id"]}}
            result = graph.invoke(txn, config)
            results.append(result)

    return results

# Stream mode for real-time updates
def process_with_streaming(input_data: dict, thread_id: str):
    """Stream state updates for real-time monitoring"""
    config = {"configurable": {"thread_id": thread_id}}

    for event in graph.stream(input_data, config, stream_mode="updates"):
        # Process each state update as it happens
        yield {
            "thread_id": thread_id,
            "update": event,
            "timestamp": datetime.utcnow().isoformat()
        }
```

---

## Code Examples

### Complete Working Example: Financial Transaction Pipeline

```python
#!/usr/bin/env python3
"""
Complete LangGraph Financial Transaction Pipeline
Demonstrates: State management, validation, checkpointing, error handling,
human-in-the-loop approval, and audit trail
"""

from typing import TypedDict, Annotated, Literal
from operator import add
from decimal import Decimal
from datetime import datetime
import uuid

from pydantic import BaseModel, Field, field_validator
from langgraph.graph import StateGraph, END
from langgraph.types import Command, interrupt
from langgraph.checkpoint.sqlite import SqliteSaver

# --- Pydantic Models for Validation ---

class Transaction(BaseModel):
    """Transaction data model with validation"""
    id: str = Field(default_factory=lambda: f"TXN_{uuid.uuid4().hex[:8]}")
    amount: Decimal = Field(ge=0, description="Transaction amount (non-negative)")
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    account_from: str = Field(pattern=r"^ACC_\d+$")
    account_to: str = Field(pattern=r"^ACC_\d+$")
    description: str = Field(default="", max_length=200)

    @field_validator("amount")
    @classmethod
    def validate_amount_limit(cls, v):
        if v > Decimal("1000000"):
            raise ValueError("Transaction exceeds maximum limit of 1,000,000")
        return v

    @field_validator("account_to")
    @classmethod
    def validate_different_accounts(cls, v, info):
        if "account_from" in info.data and v == info.data["account_from"]:
            raise ValueError("Source and destination accounts must be different")
        return v

# --- State Schema ---

class TransactionState(TypedDict):
    """Complete transaction state"""
    # Core transaction
    transaction: Transaction

    # Status tracking
    status: Literal[
        "pending", "validating", "validated",
        "checking_fraud", "awaiting_approval",
        "approved", "rejected",
        "processing", "completed", "failed"
    ]

    # Validation
    validation_errors: Annotated[list[str], add]
    risk_score: float

    # Approval
    approval_required: bool
    approved_by: str | None

    # Error handling
    error_count: int

    # Audit trail
    audit_log: Annotated[list[dict], add]

# --- Mock Services ---

class MockAccountService:
    """Mock account balance checker"""
    @staticmethod
    def get_balance(account: str) -> Decimal:
        # Simulate account balances
        balances = {
            "ACC_12345": Decimal("100000"),
            "ACC_67890": Decimal("50000"),
            "ACC_11111": Decimal("1000")
        }
        return balances.get(account, Decimal("10000"))

class MockFraudService:
    """Mock fraud detection"""
    @staticmethod
    def calculate_risk(amount: float, account_from: str, account_to: str) -> float:
        # Simple risk calculation
        if amount > 50000:
            return 0.6
        if amount > 10000:
            return 0.3
        return 0.1

class MockPaymentGateway:
    """Mock payment processor"""
    @staticmethod
    def process(amount: float, account_from: str, account_to: str) -> dict:
        return {
            "reference": f"PAY_{uuid.uuid4().hex[:8]}",
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        }

# --- Node Functions ---

def initialize_transaction(state: TransactionState) -> dict:
    """Initialize transaction processing"""
    return {
        "status": "pending",
        "error_count": 0,
        "validation_errors": [],
        "audit_log": [{
            "timestamp": datetime.utcnow().isoformat(),
            "event": "transaction_initiated",
            "transaction_id": state["transaction"].id
        }]
    }

def validate_transaction(state: TransactionState) -> dict:
    """Validate transaction business rules"""
    txn = state["transaction"]
    errors = []

    try:
        # Check account balance
        balance = MockAccountService.get_balance(txn.account_from)
        if balance < txn.amount:
            errors.append(f"Insufficient funds: balance={balance}, required={txn.amount}")

        if errors:
            return {
                "status": "failed",
                "validation_errors": errors,
                "audit_log": [{
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "validation_failed",
                    "errors": errors
                }]
            }

        return {
            "status": "validated",
            "audit_log": [{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "validation_passed"
            }]
        }

    except Exception as e:
        return {
            "status": "failed",
            "validation_errors": [f"Validation error: {str(e)}"],
            "error_count": state.get("error_count", 0) + 1
        }

def check_fraud(state: TransactionState) -> dict:
    """Perform fraud detection"""
    txn = state["transaction"]

    risk_score = MockFraudService.calculate_risk(
        amount=float(txn.amount),
        account_from=txn.account_from,
        account_to=txn.account_to
    )

    # High-value or high-risk transactions require approval
    requires_approval = risk_score > 0.5 or txn.amount > Decimal("50000")

    return {
        "status": "checking_fraud",
        "risk_score": risk_score,
        "approval_required": requires_approval,
        "audit_log": [{
            "timestamp": datetime.utcnow().isoformat(),
            "event": "fraud_check_complete",
            "risk_score": risk_score,
            "requires_approval": requires_approval
        }]
    }

def request_approval(state: TransactionState) -> Command:
    """Request human approval if needed"""
    if not state.get("approval_required", False):
        # Auto-approve low-risk transactions
        return Command(
            update={
                "status": "approved",
                "audit_log": [{
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "auto_approved"
                }]
            },
            goto="process_payment"
        )

    # Request human approval (simulated - in real app, this would pause)
    # For demo purposes, we'll auto-approve
    # In production, use: decision = interrupt({...})

    # Simulate approval decision
    decision = {
        "action": "approve",  # or "reject"
        "user": "manager_01",
        "reason": "Approved after review"
    }

    if decision["action"] == "approve":
        return Command(
            update={
                "status": "approved",
                "approved_by": decision["user"],
                "audit_log": [{
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "approved",
                    "approved_by": decision["user"]
                }]
            },
            goto="process_payment"
        )
    else:
        return Command(
            update={
                "status": "rejected",
                "audit_log": [{
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "rejected",
                    "rejected_by": decision["user"],
                    "reason": decision.get("reason", "")
                }]
            },
            goto=END
        )

def process_payment(state: TransactionState) -> dict:
    """Execute payment"""
    try:
        txn = state["transaction"]

        result = MockPaymentGateway.process(
            amount=float(txn.amount),
            account_from=txn.account_from,
            account_to=txn.account_to
        )

        return {
            "status": "completed",
            "audit_log": [{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "payment_processed",
                "payment_reference": result["reference"]
            }]
        }

    except Exception as e:
        return {
            "status": "failed",
            "validation_errors": [f"Payment processing failed: {str(e)}"],
            "error_count": state.get("error_count", 0) + 1,
            "audit_log": [{
                "timestamp": datetime.utcnow().isoformat(),
                "event": "payment_failed",
                "error": str(e)
            }]
        }

# --- Build Graph ---

def build_transaction_graph():
    """Build the complete transaction processing graph"""

    # Create state graph
    builder = StateGraph(TransactionState)

    # Add nodes
    builder.add_node("initialize", initialize_transaction)
    builder.add_node("validate", validate_transaction)
    builder.add_node("fraud_check", check_fraud)
    builder.add_node("approval", request_approval)
    builder.add_node("process_payment", process_payment)

    # Define flow
    builder.set_entry_point("initialize")
    builder.add_edge("initialize", "validate")

    # Validation routing
    builder.add_conditional_edges(
        "validate",
        lambda s: "success" if s["status"] == "validated" else "failed",
        {
            "success": "fraud_check",
            "failed": END
        }
    )

    builder.add_edge("fraud_check", "approval")
    # approval node uses Command to route to process_payment or END

    # Process payment routing
    builder.add_conditional_edges(
        "process_payment",
        lambda s: "success" if s["status"] == "completed" else "failed",
        {
            "success": END,
            "failed": END
        }
    )

    # Compile with checkpointer
    checkpointer = SqliteSaver.from_conn_string("transactions.db")
    return builder.compile(checkpointer=checkpointer)

# --- Main Execution ---

def main():
    """Run example transactions"""
    graph = build_transaction_graph()

    # Example 1: Small transaction (auto-approved)
    print("=" * 60)
    print("Example 1: Small Transaction (Auto-Approved)")
    print("=" * 60)

    txn1 = Transaction(
        amount=Decimal("5000.00"),
        account_from="ACC_12345",
        account_to="ACC_67890",
        description="Small payment"
    )

    config1 = {"configurable": {"thread_id": txn1.id}}
    result1 = graph.invoke({"transaction": txn1}, config1)

    print(f"Status: {result1['status']}")
    print(f"Risk Score: {result1.get('risk_score', 0):.2f}")
    print("\nAudit Trail:")
    for entry in result1["audit_log"]:
        print(f"  - {entry['timestamp']}: {entry['event']}")

    # Example 2: Large transaction (requires approval)
    print("\n" + "=" * 60)
    print("Example 2: Large Transaction (Requires Approval)")
    print("=" * 60)

    txn2 = Transaction(
        amount=Decimal("75000.00"),
        account_from="ACC_12345",
        account_to="ACC_67890",
        description="Large payment"
    )

    config2 = {"configurable": {"thread_id": txn2.id}}
    result2 = graph.invoke({"transaction": txn2}, config2)

    print(f"Status: {result2['status']}")
    print(f"Risk Score: {result2.get('risk_score', 0):.2f}")
    print(f"Approved By: {result2.get('approved_by', 'N/A')}")
    print("\nAudit Trail:")
    for entry in result2["audit_log"]:
        print(f"  - {entry['timestamp']}: {entry['event']}")

    # Example 3: Failed transaction (insufficient funds)
    print("\n" + "=" * 60)
    print("Example 3: Failed Transaction (Insufficient Funds)")
    print("=" * 60)

    txn3 = Transaction(
        amount=Decimal("200000.00"),
        account_from="ACC_11111",  # Low balance account
        account_to="ACC_67890",
        description="Payment exceeding balance"
    )

    config3 = {"configurable": {"thread_id": txn3.id}}
    result3 = graph.invoke({"transaction": txn3}, config3)

    print(f"Status: {result3['status']}")
    print(f"Errors: {result3.get('validation_errors', [])}")
    print("\nAudit Trail:")
    for entry in result3["audit_log"]:
        print(f"  - {entry['timestamp']}: {entry['event']}")

    # Demonstrate state history
    print("\n" + "=" * 60)
    print("State History for Transaction 2")
    print("=" * 60)

    states = list(graph.get_state_history(config2))
    print(f"Total checkpoints: {len(states)}")
    for i, state in enumerate(reversed(states)):
        print(f"\nCheckpoint {i + 1}:")
        print(f"  Status: {state.values.get('status')}")
        print(f"  Checkpoint ID: {state.config['configurable']['checkpoint_id'][:8]}...")

if __name__ == "__main__":
    main()
```

**Run the example:**
```bash
pip install langgraph langgraph-checkpoint-sqlite pydantic
python transaction_pipeline.py
```

---

## Limitations & Best Practices

### Limitations

1. **Pydantic Performance**
   - Recursive validation is slower than TypedDict
   - Validation error traces don't show which node failed
   - **Recommendation:** Use TypedDict for performance-critical paths, Pydantic only where validation is essential

2. **Checkpoint Storage**
   - InMemorySaver loses data on restart
   - SqliteSaver has limited concurrency
   - **Recommendation:** Use PostgresSaver for production

3. **Retry Policy**
   - If all retries fail, execution stops immediately
   - No automatic graceful degradation
   - **Recommendation:** Implement custom error handling nodes for graceful failure

4. **Connection Pooling**
   - PostgresSaver requires manual connection pool management
   - Connections can close unexpectedly
   - **Recommendation:** Create global connection pool, reuse across requests

5. **Interrupt Limitations**
   - Entire node re-executes when resuming
   - Static interrupts not recommended for HITL
   - **Recommendation:** Use dynamic interrupts with `interrupt()` function

6. **State Size**
   - Large states slow down checkpointing
   - Checkpoint storage can grow quickly
   - **Recommendation:** Keep state minimal, store large data externally

---

### Best Practices

#### 1. State Design

✅ **DO:**
- Use TypedDict for performance, Pydantic for validation
- Keep state minimal (only essential data)
- Use reducers (Annotated) for lists and accumulated data
- Design immutable state updates

❌ **DON'T:**
- Store large binary data in state
- Modify state directly (return updates instead)
- Use complex nested structures unnecessarily

```python
# Good: Minimal state with clear types
class State(TypedDict):
    transaction_id: str
    amount: Decimal
    status: str
    errors: Annotated[list[str], add]

# Bad: Bloated state with unnecessary data
class State(TypedDict):
    transaction_id: str
    amount: Decimal
    status: str
    errors: list[str]
    raw_request: dict  # Could be large
    full_customer_record: dict  # Unnecessary
    external_api_responses: list[dict]  # Store externally
```

#### 2. Error Handling

✅ **DO:**
- Use retry policies for transient errors
- Implement custom error nodes for graceful degradation
- Track error count in state
- Log errors with context
- Provide clear error messages

❌ **DON'T:**
- Retry permanent errors (validation failures, business rule violations)
- Let exceptions propagate unhandled
- Lose error context

```python
# Good: Explicit error handling
def process_transaction(state: State) -> dict:
    try:
        result = api.process(state)
        return {"status": "completed", "result": result}
    except TransientError as e:
        # Let retry policy handle
        raise
    except PermanentError as e:
        # Handle gracefully
        return {
            "status": "failed",
            "errors": [str(e)],
            "error_count": state.get("error_count", 0) + 1
        }

# Bad: Catch-all error handling
def process_transaction(state: State) -> dict:
    try:
        result = api.process(state)
        return {"status": "completed"}
    except Exception:
        return {"status": "failed"}  # Lost error context
```

#### 3. Checkpointing

✅ **DO:**
- Use PostgresSaver for production
- Create global connection pool
- Include thread_id in all invocations
- Build audit trails from checkpoint history
- Clean up old checkpoints periodically

❌ **DON'T:**
- Use InMemorySaver in production
- Create new connections for each request
- Forget thread_id (causes data loss)
- Store sensitive data in checkpoints without encryption

```python
# Good: Production setup
pool = ConnectionPool(conninfo=DB_URI, max_size=20)

def process_request(data: dict):
    with pool.connection() as conn:
        checkpointer = PostgresSaver(conn)
        graph = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": data["id"]}}
        return graph.invoke(data, config)

# Bad: Development setup in production
def process_request(data: dict):
    checkpointer = InMemorySaver()  # Lost on restart!
    graph = workflow.compile(checkpointer=checkpointer)
    return graph.invoke(data)  # Missing thread_id!
```

#### 4. Validation

✅ **DO:**
- Validate early (fail fast)
- Use Pydantic for complex validation rules
- Return clear validation errors
- Validate at each critical step

❌ **DON'T:**
- Skip validation to improve performance
- Validate too late (after expensive operations)
- Return generic error messages

```python
# Good: Clear validation with Pydantic
class Transaction(BaseModel):
    amount: Decimal = Field(ge=0, le=1000000)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v > 100000:
            # Clear business rule
            raise ValueError("Transactions over 100,000 require pre-approval")
        return v

# Bad: Unclear validation
def validate(state):
    if state["amount"] > 100000:
        return {"status": "error"}  # What's wrong?
```

#### 5. Financial Operations

✅ **DO:**
- Use Decimal for currency (never float)
- Build complete audit trails
- Implement rollback mechanisms
- Require approval for high-value transactions
- Validate at every step
- Store transaction references

❌ **DON'T:**
- Use float for currency amounts
- Skip audit logging
- Auto-approve high-risk transactions
- Allow partial state updates

```python
# Good: Proper financial handling
from decimal import Decimal

class Transaction(BaseModel):
    amount: Decimal  # Exact decimal arithmetic
    currency: str

def process_payment(state: State) -> dict:
    # Audit trail
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "payment_initiated",
        "amount": str(state["amount"])  # Preserve precision
    }

    # Process with rollback capability
    try:
        result = gateway.process(state)
        return {
            "status": "completed",
            "reference": result["ref"],
            "audit_log": [audit_entry, {
                "event": "payment_completed",
                "reference": result["ref"]
            }]
        }
    except Exception as e:
        # Rollback and audit
        gateway.rollback(state)
        return {
            "status": "failed",
            "audit_log": [audit_entry, {
                "event": "payment_failed",
                "error": str(e)
            }]
        }

# Bad: Float arithmetic and missing audit
def process_payment(state: State) -> dict:
    amount = float(state["amount"])  # Loss of precision!
    result = gateway.process(amount)
    return {"status": "completed"}  # No audit trail
```

#### 6. Human-in-the-Loop

✅ **DO:**
- Use dynamic interrupts (`interrupt()`)
- Provide full context in interrupt payload
- Use Command for routing after approval
- Log approval decisions

❌ **DON'T:**
- Use static interrupts for approval workflows
- Interrupt without checkpointer
- Forget to handle rejection case

```python
# Good: Complete HITL approval
def request_approval(state: State) -> Command:
    decision = interrupt({
        "question": "Approve this transaction?",
        "transaction_id": state["transaction_id"],
        "amount": state["amount"],
        "risk_score": state["risk_score"],
        "full_details": state["transaction"]
    })

    if decision["action"] == "approve":
        return Command(
            update={
                "status": "approved",
                "approved_by": decision["user"],
                "approved_at": datetime.utcnow().isoformat()
            },
            goto="process_payment"
        )
    else:
        return Command(
            update={
                "status": "rejected",
                "rejected_by": decision["user"],
                "rejection_reason": decision.get("reason")
            },
            goto="handle_rejection"
        )

# Bad: Incomplete HITL
def request_approval(state: State):
    # Missing interrupt - can't pause!
    return {"status": "approved"}  # Auto-approve everything
```

---

## Summary

### LangGraph for Financial Workflows: Key Takeaways

**Strengths:**
- ✅ Built-in checkpointing provides automatic audit trail
- ✅ Time travel enables rollback to any checkpoint
- ✅ Transactional supersteps provide transaction-like semantics
- ✅ Immutable state prevents race conditions
- ✅ Flexible validation (Pydantic, custom validators)
- ✅ Human-in-the-loop support for approvals
- ✅ Production-ready with PostgreSQL checkpointer

**Requirements Met:**
- ✅ Ability to rollback on errors (time travel + update_state)
- ✅ Full audit trail (checkpoint history with metadata)
- ✅ Validation at each step (Pydantic, ValidationNode, custom)
- ✅ Retry failed operations (retry policies, conditional routing)
- ✅ Clear error propagation (transactional supersteps)

**Production Recommendations:**
1. Use PostgresSaver with connection pooling
2. Implement retry policies for transient errors
3. Use Pydantic for financial data validation
4. Build audit trails from checkpoint history
5. Implement rollback mechanisms for errors
6. Use dynamic interrupts for approvals
7. Monitor state transitions and checkpoint creation
8. Clean up old checkpoints periodically

**Code Patterns:**
- State: TypedDict + Pydantic for validation
- Persistence: PostgresSaver with connection pool
- Error Handling: Retry policies + custom error nodes
- Validation: Pydantic models + ValidationNode
- Approval: Dynamic interrupts with Command routing
- Audit: Checkpoint history + state.audit_log field
- Rollback: Time travel + update_state

LangGraph provides a solid foundation for building reliable, auditable financial workflows with proper state management, error handling, and recovery capabilities.

---

**Resources:**
- Official Documentation: https://langchain-ai.github.io/langgraph/
- Checkpointing Guide: https://langchain-ai.github.io/langgraph/concepts/persistence/
- Error Handling: https://langchain-ai.github.io/langgraph/how-tos/graph-api/
- Human-in-the-Loop: https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/
- Time Travel: https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/

---

*End of Research Document*
