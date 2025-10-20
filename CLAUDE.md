# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BoondManager Multi-Agent Invoice Workflow Automation**

A stateless MVP system for automated invoice generation from client emails using LangGraph multi-agent architecture. The system parses client emails, reconciles consultant activity data against BoondManager CRA, validates business rules, and generates invoices.

**Key Technologies:**
- Python 3.11+
- LangGraph (multi-agent workflow orchestration)
- LangChain + OpenAI (LLM integration)
- Pydantic (data validation)
- httpx (async HTTP client for BoondManager API)
- deepagents (agent utilities)

**Entry Points:**
- [src/graph.py](src/graph.py) - Main LangGraph workflow combining Planner & Orchestrator agents (tool-calling mode)
- [src/no_tool_calls/graph.py](src/no_tool_calls/graph.py) - Alternative supervisor workflow using pure graph routing (experimental)

## Architecture

### Two Implementation Modes

The system supports two different architectural patterns for multi-agent coordination:

#### Mode 1: Tool-Calling Workflow (Primary - `src/`)

The primary implementation uses a two-phase approach with tool-calling for agent dispatch:

1. **Planner Agent** ([src/agents/planner_agent.py](src/agents/planner_agent.py))
   - Analyzes user query and creates structured task list
   - Uses reflexion loop (plan → critic → refine) for high-quality planning
   - Outputs: `plan` (string) and `todos` (structured task list)

2. **Orchestrator Agent** ([src/agents/orchestrator_agent.py](src/agents/orchestrator_agent.py))
   - Executes the task list by dispatching to specialized subagents
   - Routes tasks to: query, validation, invoice, resource, timesheet, project agents
   - Manages execution flow and aggregates results

#### Mode 2: Pure Graph Supervisor Workflow (Experimental - `src/no_tool_calls/`)

An alternative implementation that uses LangGraph's native routing instead of tool calls:

**Architecture:** Supervisor pattern with graph-based delegation
- **Primary Assistant** ([src/no_tool_calls/assistant.py](src/no_tool_calls/assistant.py))
  - Main orchestrator that breaks down complex tasks into parallel subtasks
  - Delegates to specialized subagents through graph routing (not tool calls)
  - Emphasizes expert prompt engineering for ChatGPT models

**Key Components:**
- **AssistantWithSubagents** class: Builds hierarchical supervisor graphs
- **Dialog State Management** ([src/no_tool_calls/state.py](src/no_tool_calls/state.py)): Tracks which subagent is active
- **Routing Logic** ([src/no_tool_calls/routing.py](src/no_tool_calls/routing.py)): Entry/exit nodes, conditional edges, delegation flow
- **CompleteOrEscalate**: Tool for subagents to return control to supervisor

**Advantages:**
- More explicit control flow through graph structure
- Easier to visualize and debug with LangGraph's graph visualization
- Natural support for human-in-the-loop interrupts
- Clear dialog state tracking for nested delegation

**Entry Point:** [src/no_tool_calls/graph.py](src/no_tool_calls/graph.py)

**Example Subagent:** [src/no_tool_calls/subagents/query.py](src/no_tool_calls/subagents/query.py)
- Demonstrates nested supervisor pattern (query agent supervises resource and project subagents)
- Shows prompt engineering optimized for ChatGPT models with detailed instructions

### Agent Structure

**Tool-Calling Mode (`src/agents/`):**
```
src/agents/
├── planner_agent.py        # Task planning and decomposition
├── orchestrator_agent.py   # Task execution and subagent routing
├── query_agent.py          # Data querying and retrieval (answers "what/how many" questions)
├── validation_agent.py     # Business rule validation
├── invoice_agent.py        # Invoice generation
├── resource_agent.py       # Resource/consultant management
├── timesheet_agent.py      # Timesheet/CRA operations
└── project_agent.py        # Project lookup and validation
```

**Pure Graph Mode (`src/no_tool_calls/`):**
```
src/no_tool_calls/
├── graph.py                # Entry point with supervisor workflow
├── assistant.py            # AssistantWithSubagents class (supervisor builder)
├── state.py                # State management with dialog stack
├── routing.py              # Routing functions and CompleteOrEscalate tool
├── tools.py                # Tool node with error handling
└── subagents/
    ├── query.py            # Query subagent (nested supervisor)
    ├── resource.py         # Resource management subagent
    └── project.py          # Project lookup subagent
```

### Key Components

- **Tools** (`src/tools/`): BoondManager API integration tools for each domain
- **Middleware** (`src/middleware/`): Planning utilities and parse validation
- **Integrations** (`src/integrations/`): BoondManager API client with JWT auth
- **Config** (`src/config.py`): Environment configuration management
- **LLM Config** (`src/llm_config.py`): OpenAI model configuration

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

**Tool-Calling Mode (Primary):**
```bash
# Run the main workflow
uv run python src/graph.py

# Run with asyncio
uv run python -m asyncio src.graph
```

**Pure Graph Supervisor Mode (Experimental):**
```bash
# Run the supervisor workflow
uv run python src/no_tool_calls/graph.py
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

### Explaining the Architecture

When using `/sc:explain` or explaining the system architecture, **default to presenting the Pure Graph Supervisor Workflow** (`src/no_tool_calls/`) as the primary implementation pattern:

**Primary Focus:**
1. Explain the supervisor pattern with graph-based delegation
2. Show how `AssistantWithSubagents` builds hierarchical graphs
3. Demonstrate dialog state management and routing logic
4. Highlight advantages: explicit control flow, visualization, human-in-the-loop

**Secondary Context:**
- Mention the tool-calling mode (`src/`) as an alternative approach
- Compare/contrast the two patterns when relevant
- Link to specific files in both implementations

**Example Explanation Flow:**
```
This system uses a supervisor pattern with pure graph routing...
[Detailed explanation of no_tool_calls implementation]

Alternative: The system also has a tool-calling mode (src/) that uses...
[Brief comparison]
```

### Agent Prompt Engineering Guidelines

**CRITICAL: ChatGPT OSS Compatibility**

All agent system prompts must be optimized for ChatGPT-based models (via OpenAI API), not Claude. Key differences to consider:

#### Prompt Structure for ChatGPT
1. **Be Explicit and Directive**: ChatGPT responds better to clear, numbered instructions and explicit workflows
2. **Use Repetition for Emphasis**: Important instructions should be repeated in multiple sections (capabilities, examples, rules)
3. **Concrete Examples Over Abstract Rules**: Show step-by-step examples with exact tool call sequences
4. **Visual Markers**: Use ⚠️, 🔴, ✅, etc. to highlight critical sections
5. **Mandatory Workflow Enforcement**: For multi-step workflows (like generate → verify), state requirements as "MANDATORY", "CRITICAL", "NEVER skip"

#### Common Pitfalls with ChatGPT OSS
- **Stopping Early**: ChatGPT may complete a task prematurely without verification steps
  - **Solution**: Add explicit "NEVER stop after X without doing Y" instructions
- **Skipping Tool Calls**: May skip seemingly "optional" verification steps
  - **Solution**: Make workflows MANDATORY with numbered steps (Step 1, Step 2, Step 3)
- **Hallucinating Instead of Using Tools**: May fabricate responses instead of calling tools
  - **Solution**: Add "ALWAYS use tools, NEVER fabricate" as rule #1

#### Example: Invoice Generation Workflow
The [invoice_agent.py](src/agents/invoice_agent.py) demonstrates proper ChatGPT prompt engineering:
- Workflow stated 4 times: Core Capabilities, Query Strategy, Rules, Examples
- Uses ⚠️ CRITICAL markers for emphasis
- Explicit "NEVER finish after X without Y" instructions
- Concrete examples with exact tool call sequences
- Numbered steps (Step 1, Step 2, Step 3, Step 4)

#### Testing Agent Prompts
When modifying agent prompts:
1. Test with actual ChatGPT model (not Claude)
2. Verify multi-step workflows are followed completely
3. Check that tools are called instead of hallucinated responses
4. Ensure critical verification steps aren't skipped

### Adding New Agents

1. Create agent file in `src/agents/`
2. Define agent tools in `src/tools/`
3. Register agent in orchestrator routing logic
4. Add tests in `tests/unit/`
5. **Design system prompt for ChatGPT** (see prompt engineering guidelines above)

### Modifying the Workflow

The main workflow is defined in [src/graph.py](src/graph.py:103-127) using LangGraph's `StateGraph`:
- Modify `create_workflow_graph()` to change node connections
- Update `WorkflowState` to add/remove state fields
- Adjust routing logic in orchestrator for new agents

### Testing Agent Behavior

Each agent has dedicated tools and can be tested independently:
```python
from src.agents.planner_agent import create_planner_graph

planner = create_planner_graph()
result = await planner.ainvoke({"prompt": "your test query"})
```

### BoondManager API Integration

API client: [src/integrations/boond_client.py](src/integrations/boond_client.py)
- JWT authentication with automatic token generation
- Retry logic with tenacity
- Async httpx client
- Comprehensive error handling

## Project Documentation

- [README.md](README.md) - Quick start and overview
- [API_SUMMARY.md](API_SUMMARY.md) - BoondManager API endpoints
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementation details
- [EXPLORATION_GUIDE.md](EXPLORATION_GUIDE.md) - Codebase exploration guide
- [docs/](docs/) - Architecture and requirements documentation
