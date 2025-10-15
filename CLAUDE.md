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

**Entry Point:** [src/graph.py](src/graph.py) - Main LangGraph workflow combining Planner & Orchestrator agents

## Architecture

### Workflow Graph Structure

The system uses a two-phase approach:

1. **Planner Agent** ([src/agents/planner_agent.py](src/agents/planner_agent.py))
   - Analyzes user query and creates structured task list
   - Uses reflexion loop (plan → critic → refine) for high-quality planning
   - Outputs: `plan` (string) and `todos` (structured task list)

2. **Orchestrator Agent** ([src/agents/orchestrator_agent.py](src/agents/orchestrator_agent.py))
   - Executes the task list by dispatching to specialized subagents
   - Routes tasks to: verification, validation, invoice, resource, timesheet, project agents
   - Manages execution flow and aggregates results

### Agent Structure

```
src/agents/
├── planner_agent.py        # Task planning and decomposition
├── orchestrator_agent.py   # Task execution and subagent routing
├── verification_agent.py   # Data verification and reconciliation
├── validation_agent.py     # Business rule validation
├── invoice_agent.py        # Invoice generation
├── resource_agent.py       # Resource/consultant management
├── timesheet_agent.py      # Timesheet/CRA operations
└── project_agent.py        # Project lookup and validation
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

### Running the Application

```bash
# Run the main workflow
python src/graph.py

# Run with asyncio
python -m asyncio src.graph
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Working with This Codebase

### Adding New Agents

1. Create agent file in `src/agents/`
2. Define agent tools in `src/tools/`
3. Register agent in orchestrator routing logic
4. Add tests in `tests/unit/`

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
