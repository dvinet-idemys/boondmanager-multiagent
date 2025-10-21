# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MCP Documentation Rules

For ANY question about LangGraph or LangChain, use the langgraph-docs MCP server to help answer:
1. Call `list_doc_sources` tool to get the available llms.txt file
2. Call `fetch_docs` tool to read it
3. Reflect on the urls in llms.txt
4. Reflect on the input question
5. Call `fetch_docs` on any urls relevant to the question
6. Use this documentation to answer the question accurately

## Project Overview

**BoondManager Multi-Agent Invoice Workflow Automation**

A hierarchical multi-agent system for automated invoice workflow using React (Reasoning + Acting) agent architecture with LangGraph. The system validates consultant timesheets against client emails, handles discrepancies through email workflows with human-in-the-loop interrupts, and coordinates complex validation operations across multiple specialized subagents.

**Key Technologies:**
- Python 3.11+
- LangGraph (multi-agent workflow orchestration with checkpointing and interrupts)
- LangChain + OpenAI (LLM integration, ChatGPT models)
- Pydantic (data validation and tool schemas)
- httpx (async HTTP client for BoondManager API)
- deepagents (agent utilities)

**Entry Point:**
- [src/main.py](src/main.py) - Main React agent with 3-level hierarchical delegation

## Architecture

### React Agent Pattern with Hierarchical Delegation

The system implements a **React (Reasoning + Acting) agent architecture** with nested subagent delegation for complex workflow orchestration.

#### Core Pattern: React Loop

Each agent follows the React pattern:
1. **LLM Reasoning** - Analyzes task and decides which tools/subagents to use
2. **Tool Execution** - Executes tools or delegates to subagents
3. **Result Processing** - Incorporates results and decides next action
4. **Loop or End** - Continues until task completion

#### Three-Level Hierarchy

```
Level 1: Main Coordinator (src/main.py)
  ├─ Delegates to specialized subagents via tools
  ├─ Manages overall workflow and task decomposition
  └─ Handles human-in-the-loop interrupts

Level 2: Specialized Subagents (src/agents/subagents/)
  ├─ query_agent: Data querying coordinator (has own sub-subagents)
  ├─ validation_agent: Timesheet validation operations
  └─ emailing_agent: Email reading, drafting, sending, response waiting

Level 3: Domain-Specific Subagents (nested under query_agent)
  ├─ resource_agent: Resource/consultant lookup
  ├─ project_agent: Project and delivery management
  └─ timesheet_agent: CRA/timesheet operations
```

### Agent Implementation: ReactAgent Class

**Location:** [src/agents/agent.py](src/agents/agent.py)

**Key Features:**
- **Tool Binding**: Binds both regular tools and delegation tools to LLM
- **Parallel Execution**: Uses LangGraph's `Send` API for parallel subagent invocation
- **Batch Delegation**: Supports batching similar requests to same subagent
- **Message Isolation**: Parent agents only see final responses, not intermediate reasoning
- **Checkpointing**: Built-in memory with `InMemorySaver` for conversation persistence
- **Error Handling**: Fallback logic for tool errors (preserves `GraphInterrupt` for human-in-the-loop)

**Core Components:**
```python
class ReactAgent(Runnable):
    - model: ChatModel (ChatGPT via LangChain)
    - system_prompt: Agent behavior instructions
    - tools: List of regular tools (BaseTool)
    - subagents: List of Subagent configurations
    - graph: Compiled LangGraph StateGraph
```

**Subagent Configuration:**
```python
@dataclass
class Subagent:
    name: str                    # Unique identifier
    agent: ReactAgent            # Nested ReactAgent instance
    delegation_tool: BaseModel   # Pydantic schema for delegation
```

### Agent Structure

```
src/
├── main.py                      # Entry point with Main Coordinator setup
├── agents/
│   ├── agent.py                 # ReactAgent class implementation
│   └── subagents/
│       ├── query.py             # Data query coordinator (nested supervisor)
│       ├── validation.py        # Timesheet validation operations
│       ├── emailing.py          # Email management with interrupts
│       ├── resource.py          # Resource/consultant lookup
│       ├── project.py           # Project and delivery queries
│       └── timesheet.py         # CRA/timesheet operations
├── tools/
│   ├── common_tools.py          # Shared utilities (total_cost)
│   ├── email_tools.py           # Email operations (read, draft, send, wait)
│   ├── invoice_tools.py         # Invoice generation tools
│   ├── project_tools.py         # Project lookup and queries
│   ├── resource_tools.py        # Resource management
│   ├── timesheet_tools.py       # Timesheet/CRA operations
│   └── validation_tool.py       # Validation operations
├── integrations/
│   ├── boond_client.py          # BoondManager API client (JWT auth)
│   └── auth.py                  # JWT token generation
├── config.py                    # Environment configuration
├── llm_config.py                # OpenAI model configuration
└── utils.py                     # Utility functions
```

### Key Features

#### 1. Parallel Subagent Execution

The system uses LangGraph's `Send` API to invoke multiple subagents in parallel:

```python
# Main Coordinator can dispatch multiple queries in parallel
"Get cost for worker A on project X" → query_agent (instance 1)
"Get cost for worker B on project Y" → query_agent (instance 2)
"Get cost for worker C on project Z" → query_agent (instance 3)
# All execute in parallel, results aggregated back to coordinator
```

#### 2. Batch Delegation Tool

Automatically created for each agent with subagents:
- Takes `subagent_name` and list of `requests`
- Expands into individual tool calls with unique IDs
- Enables efficient parallel processing of similar operations
- Enforces consistent request patterns within batches

#### 3. Human-in-the-Loop Interrupts

**Email Response Workflow:**
- `emailing_agent` sends email and calls `wait_for_email` tool
- Tool raises `GraphInterrupt` to pause execution
- User provides response via CLI: `your response here: <user input>`
- Workflow resumes with user input passed back to agent

**Implementation:**
```python
# In main.py
while (interrupt := result.get("__interrupt__")) is not None:
    print(interrupt)
    resume = input("your response here: ")
    result = await main_agent.ainvoke(Command(resume=resume), config=config)
```

#### 4. Message Isolation (Clean Delegation)

Parent agents only receive final responses from subagents, not intermediate reasoning:
- Subagent executes full React loop internally
- Wrapper extracts final `AIMessage` content
- Converts to `ToolMessage` with matching `tool_call_id`
- Parent LLM sees only the answer, not the reasoning chain

### Delegation Flow

**Example: Multi-Worker Cost Query**

```
User → Main Coordinator:
"Get total costs for workers A, B, C on project X in Sep 2025"

Main Coordinator (LLM reasoning):
→ Recognizes need for batch queries
→ Calls DelegateToSubagents tool:
  - subagent_name: "query"
  - requests: [
      "Get total cost for worker A on project X in Sep 2025",
      "Get total cost for worker B on project X in Sep 2025",
      "Get total cost for worker C on project X in Sep 2025"
    ]

LangGraph Router:
→ Expands batch into 3 individual delegations
→ Creates 3 Send objects (parallel execution)

Query Agent (×3 parallel instances):
Instance 1 → Uses project_agent + timesheet_agent + total_cost
Instance 2 → Uses project_agent + timesheet_agent + total_cost
Instance 3 → Uses project_agent + timesheet_agent + total_cost

Results aggregated:
→ 3 ToolMessage responses sent back to Main Coordinator
→ Main Coordinator synthesizes final answer
```

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- BoondManager API credentials
- OpenAI API key

### Installation

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# Install dev dependencies
uv pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with credentials
```

### Environment Variables

```bash
# BoondManager API - JWT Authentication
BOOND_USER_TOKEN=your_user_token
BOOND_CLIENT_TOKEN=your_client_token
BOOND_CLIENT_KEY=your_signing_key
BOOND_BASE_URL=https://api.boondmanager.com/api/v3

# OpenAI
OPENAI_API_KEY=your_openai_key
```

## Common Commands

**IMPORTANT: Always use `uv` for all Python operations and project management in this project.**

### Running the Application

```bash
# Run the main React agent workflow
uv run python src/main.py

# Run with asyncio
uv run python -m asyncio src.main
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term

# Run specific test suites
uv run pytest tests/unit/
uv run pytest tests/integration/
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

## Working with This Codebase

### Understanding the React Agent Pattern

The **React (Reasoning + Acting) pattern** is the foundation of this system:

1. **Reasoning Phase**: LLM analyzes the task and available tools/subagents
2. **Acting Phase**: Executes tools or delegates to subagents
3. **Observation Phase**: Processes results and decides next step
4. **Iteration**: Repeats until task completion or termination condition

**Key Insight:** Each agent is autonomous - it has its own LLM, tools, and subagents. The hierarchy emerges from composition, not centralized control.

### Agent Prompt Engineering Guidelines

**CRITICAL: ChatGPT Compatibility**

All agent system prompts are optimized for **ChatGPT models** (via OpenAI API), not Claude. This requires specific prompt engineering patterns:

#### Prompt Structure for ChatGPT

1. **Explicit Instructions**: Clear, numbered steps and workflows
2. **Repetition for Emphasis**: Critical workflows stated multiple times
3. **Concrete Examples**: Step-by-step tool call sequences
4. **Visual Markers**: ⚠️, 🔴, ✅ for critical sections
5. **Mandatory Workflows**: "MANDATORY", "CRITICAL", "NEVER skip" enforcement

#### Common Pitfalls with ChatGPT

- **Stopping Early**: May skip verification steps
  - **Solution**: "NEVER stop after X without doing Y" instructions
- **Skipping Tools**: May skip "optional" steps
  - **Solution**: Make workflows MANDATORY with numbered steps
- **Hallucinating**: May fabricate instead of calling tools
  - **Solution**: "ALWAYS use tools, NEVER fabricate" as rule #1

#### Example: Query Agent Prompt

See [src/agents/subagents/query.py](src/agents/subagents/query.py:10-100):
- Clear role definition
- Explicit subagent usage instructions
- Concrete query handling examples
- Mandatory response format (ANSWER + REASONING sections)
- Machine-readable output emphasis (JSON/XML for complex data)

#### Example: Email Agent with Interrupts

See [src/agents/subagents/emailing.py](src/agents/subagents/emailing.py:13-80):
- System constraints clearly stated
- Multi-step workflow examples (read → draft → send → wait)
- Response waiting behavior explained
- Error handling patterns

### Adding New Subagents

1. **Create subagent file** in `src/agents/subagents/`
2. **Define delegation tool** using Pydantic `BaseModel`
3. **Create ReactAgent instance** with tools and system prompt
4. **Register in parent agent** via `subagents` list
5. **Design prompt for ChatGPT** (see guidelines above)

**Example Template:**

```python
from pydantic import BaseModel, Field
from src.agents.agent import ReactAgent
from src.llm_config import get_llm
from src.tools.your_tools import tool1, tool2

# Delegation tool schema
class ToYourSubagent(BaseModel):
    """Transfer work to the specialized your_domain agent."""
    requests: str = Field(
        description="Clear task description with all context"
    )

# Agent prompt
YOUR_AGENT_PROMPT = """You are a specialized agent for...
[Follow ChatGPT prompt engineering guidelines]
"""

# Create agent
your_agent = ReactAgent(
    model=get_llm(),
    system_prompt=YOUR_AGENT_PROMPT,
    tools=[tool1, tool2],
    subagents=[],  # Or nest more subagents
    name="Your Agent",
)
```

### Testing Agent Behavior

Each agent can be tested independently:

```python
from src.agents.subagents.query import query_agent
from langchain_core.messages import HumanMessage
import uuid

# Create config with thread_id for checkpointing
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# Invoke agent
result = await query_agent.ainvoke(
    [HumanMessage(content="How many days did worker A work in Sep 2025?")],
    config
)

# Check final response
print(result["messages"][-1].content)
```

### Human-in-the-Loop Testing

Test interrupt workflows:

```python
# Initial invocation
result = await main_agent.ainvoke([HumanMessage(content=query)], config)

# Handle interrupt
while (interrupt := result.get("__interrupt__")) is not None:
    print(f"Interrupt: {interrupt}")
    user_input = input("Your response: ")
    result = await main_agent.ainvoke(
        Command(resume=user_input),
        config=config
    )

# Final result
print(result["messages"][-1].content)
```

### BoondManager API Integration

**Client:** [src/integrations/boond_client.py](src/integrations/boond_client.py)

**Features:**
- JWT authentication with automatic token generation
- Retry logic with `tenacity` (exponential backoff)
- Async `httpx` client
- Comprehensive error handling and logging
- Support for GET, POST, PATCH, DELETE operations

**Usage in Tools:**

```python
from src.integrations.boond_client import BoondManagerClient

async def get_resource(resource_id: int):
    client = BoondManagerClient()
    response = await client.get(f"/resources/{resource_id}")
    return response
```

### Debugging Tips

**1. View Graph Structure:**
```python
# Visualize agent graph (requires graphviz)
from IPython.display import Image, display
display(Image(main_agent.graph.get_graph().draw_mermaid_png()))
```

**2. Enable LangGraph Tracing:**
```python
# Set environment variable
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_key
```

**3. Inspect Message History:**
```python
# Print all messages in conversation
for msg in result["messages"]:
    print(f"{msg.__class__.__name__}: {msg.content}")
```

**4. Check Checkpointer State:**
```python
# Get state for a thread
state = await main_agent.graph.aget_state(config)
print(state.values)
```

## Project Documentation

- [README.md](README.md) - Quick start and overview
- [API_SUMMARY.md](API_SUMMARY.md) - BoondManager API endpoints
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementation details
- [EXPLORATION_GUIDE.md](EXPLORATION_GUIDE.md) - Codebase exploration guide
- [docs/](docs/) - Architecture and requirements documentation

## Common Workflows

### 1. Timesheet Validation with Email Discrepancy Handling

```python
query = """
Validate timesheets when days worked and totals match.
Send an email to the worker when they don't.
Then instruct the emailing agent to wait for a response.

Query results:
LEGUAY Elodie       15j             9300
Original Email:
LEGUAY Elodie       12j             7860
"""

# Main Coordinator will:
# 1. Detect discrepancy (15j vs 12j)
# 2. Delegate to emailing_agent to draft email
# 3. Emailing_agent sends email and waits (GraphInterrupt)
# 4. User provides worker response
# 5. Resume validation or escalation based on response
```

### 2. Batch Cost Queries

```python
query = """
Get total costs for all workers on project 'Modernisation Ligne Production'
in September 2025 according to BoondManager CRA records.
"""

# Main Coordinator will:
# 1. Delegate to query_agent to get worker list
# 2. Query_agent uses project_agent for worker assignments
# 3. Batch delegation to query_agent instances for each worker cost
# 4. Aggregate results and present summary
```

### 3. Multi-Step Validation Workflow

```python
query = """
For worker Elodie LEGUAY:
1. Get September 2025 timesheet details
2. Validate the timesheet with validator ID 42
3. Report validation warnings if any
"""

# Main Coordinator will:
# 1. Delegate to validation_agent
# 2. Validation_agent uses timesheet_agent to get timesheet ID
# 3. Validation_agent calls validate_timesheet tool
# 4. Parse warnings and present results
```