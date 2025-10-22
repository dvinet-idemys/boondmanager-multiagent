"""Main Coordinator agent factory.

This module provides a factory function to create the Main Coordinator agent
with consistent configuration for both production use and testing.
"""

from typing import List, Optional

from langchain_core.tools import BaseTool

from src.agents.agent import ReactAgent, Subagent
from src.agents.subagents.emailing import ToEmailingSubagent, emailing_agent
from src.agents.subagents.invoice import ToInvoiceSubagent, invoice_agent
from src.agents.subagents.query import ToQuerySubagent, query_agent
from src.agents.subagents.validation import ToValidationSubagent, validation_agent
from src.llm_config import get_llm

# TODO: implement summarization
# TODO: move majority of policy guidance to policy tools
PRIMARY_ASSISTANT_PROMPT = """You are the Main Orchestrator - a task decomposition and delegation specialist.

## Your Role
Break complex tasks into batches of parallel subtasks and dispatch them to specialized subagents.

## 📚 CRITICAL: Use Policy Guidance
You have access to comprehensive organizational policies through the `retrieve_policy` tool.

**🔴 MANDATORY: Consult policies BEFORE starting any workflow**

Use policy retrieval for:
- Workflow procedures (timesheet validation, invoice generation, discrepancy handling)
- Delegation best practices (how to craft effective prompts)
- Error handling protocols
- Standard processes and templates

**How to use**:
```
retrieve_policy("How should I handle timesheet validation discrepancies?")
retrieve_policy("How do I generate invoices for a project?")
retrieve_policy("Best practices for delegating to query agent")
retrieve_policy("Prompt engineering guidelines for ChatGPT subagents")
```

**Tip**: Run `list_policy_categories()` to see all available guidance.

## Core Principles (Details in Policies)

1. **Explicit Context**: Subagents are ChatGPT models - provide COMPLETE information
   - Full names (First + Last)
   - Exact project names
   - Specific time periods (month + year)
   - All relevant data

2. **Data Dependencies**: NEVER assume data - query first, use second
   - Query email address → THEN draft email
   - Query cost → THEN compare

3. **Batch Similar Tasks**: Use batch delegation for 3+ similar operations

**When uncertain about HOW to delegate → retrieve_policy("prompt engineering guidelines")**

Stay action-oriented. Consult policies proactively."""


def create_main_coordinator(
    policy_tools: Optional[List[BaseTool]] = None,
    custom_prompt: Optional[str] = None,
) -> ReactAgent:
    """Create Main Coordinator agent with standard configuration.

    This factory function ensures consistent agent configuration across
    production code and tests.

    Args:
        policy_tools: Optional list of policy RAG tools (retrieve_policy, list_policies)
        custom_prompt: Optional custom system prompt (uses default if not provided)

    Returns:
        Configured ReactAgent with all standard subagents

    Example:
        >>> # Production use with policy tools
        >>> from src.indexing.index_policies import index_policies
        >>> from src.tools.policy_rag_tool import create_policy_retrieval_tool
        >>> policy_vectorstore = index_policies()
        >>> retrieve_policy = create_policy_retrieval_tool(policy_vectorstore)
        >>> main_agent = create_main_coordinator(policy_tools=[retrieve_policy])
        >>>
        >>> # Testing without policy tools
        >>> main_agent = create_main_coordinator()
    """
    tools = policy_tools if policy_tools is not None else []
    prompt = custom_prompt if custom_prompt is not None else PRIMARY_ASSISTANT_PROMPT

    return ReactAgent(
        model=get_llm(),
        system_prompt=prompt,
        tools=tools,
        subagents=[
            Subagent(
                name="query",
                agent=query_agent,
                delegation_tool=ToQuerySubagent,
            ),
            Subagent(
                name="validation",
                agent=validation_agent,
                delegation_tool=ToValidationSubagent,
            ),
            Subagent(
                name="emailing",
                agent=emailing_agent,
                delegation_tool=ToEmailingSubagent,
            ),
            Subagent(
                name="invoice",
                agent=invoice_agent,
                delegation_tool=ToInvoiceSubagent,
            ),
        ],
        name="Main Coordinator",
    )
