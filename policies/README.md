# Policy Documentation

This directory contains organizational policies and process documentation that the Main Orchestrator can query via the Policy RAG system.

## Available Policies

### 1. `timesheet_validation.md`
**Purpose**: Complete workflow for validating consultant timesheets against client emails

**Key Topics**:
- Step-by-step validation process
- Discrepancy detection and handling
- Email communication workflows
- Human-in-the-loop triggers
- Error handling procedures

**Use When**: Orchestrator needs to validate timesheets or handle mismatches between client data and BoondManager records.

### 2. `delegation_best_practices.md`
**Purpose**: Guidelines for effective task delegation to subagents

**Key Topics**:
- Core delegation principles
- Subagent capabilities reference (Query, Validation, Emailing)
- Delegation patterns (sequential, parallel, conditional)
- Context completeness checklists
- Common anti-patterns to avoid

**Use When**: Orchestrator needs guidance on how to structure delegations or which subagent to use.

### 3. `error_handling_protocols.md`
**Purpose**: Standard error handling and recovery procedures

**Key Topics**:
- Error categories (API, Data Validation, LLM, Email, Workflow)
- Recovery strategies (retry, alternative approach, escalation)
- Escalation procedures
- Logging standards
- Preventive measures

**Use When**: Orchestrator encounters errors or needs to decide when to escalate to humans.

### 4. `orchestrator_prompt_engineering.md`
**Purpose**: Comprehensive guide for crafting effective prompts for ChatGPT-based subagents

**Key Topics**:
- ChatGPT prompting best practices
- Prompt quality examples (good vs bad)
- Critical rules for data handling
- Common anti-patterns
- Workflow-specific guidance
- Quality checklists

**Use When**: Orchestrator needs detailed guidance on how to craft high-quality delegation prompts.

## How Policies Are Used

### Automatic Indexing
On startup, `src/indexing/index_policies.py` automatically:
1. Loads all `.md` files from this directory
2. Splits documents by markdown headers
3. Embeds sections using OpenAI embeddings
4. Stores in `InMemoryVectorStore` for fast retrieval

### Retrieval by Orchestrator
The orchestrator uses `retrieve_policy(query)` tool to semantic search over these documents:

```python
# Example queries
retrieve_policy("How should I handle timesheet validation discrepancies?")
retrieve_policy("Best practices for delegating to query agent")
retrieve_policy("What to do when API calls fail?")
retrieve_policy("Prompt engineering guidelines for ChatGPT subagents")
```

### Benefits
- **Separation of Concerns**: Policies separate from code
- **Easy Updates**: Modify markdown files without code changes
- **Consistent Guidance**: Single source of truth for procedures
- **Reduced Prompt Size**: Orchestrator prompt is concise, details in RAG
- **Scalable**: Add new policies by creating new `.md` files

## Adding New Policies

### 1. Create Markdown File
```bash
touch policies/new_policy.md
```

### 2. Structure with Headers
Use markdown headers for semantic chunking:

```markdown
# Policy Title

## Overview
High-level description

## Section Name

### Subsection Name
Details...
```

**Header Levels**:
- `#` (H1) = Document title
- `##` (H2) = Major section
- `###` (H3) = Subsection

### 3. Restart Application
Indexing happens automatically on startup:
```bash
uv run python src/main.py
```

## Best Practices for Policy Writing

### Use Clear Headers
Headers create semantic chunks for retrieval:

✅ **Good**:
```markdown
## Error Handling
### When API Calls Fail
### When Data is Missing
```

❌ **Bad**:
```markdown
This section talks about what to do when things go wrong
```

### Include Concrete Examples
Examples make policies actionable:

✅ **Good**:
```markdown
✅ CORRECT: "How many days did Elodie LEGUAY work on project 'X' in September 2025?"
❌ WRONG: "How many days did Elodie work?"
```

### Use Consistent Formatting

**For Workflows**:
```markdown
### Step 1: Query Phase
1. Extract worker names
2. Query BoondManager
3. Compare results
```

**For Guidelines**:
```markdown
**Important**: Always query data first
- ❌ NEVER assume email addresses
- ✅ ALWAYS query worker contact info
```

## Policy Maintenance

### Version Control
All policies are version-controlled in git. Changes are tracked automatically.

### Review Schedule
Policies should be reviewed:
- After major workflow changes
- When recurring issues are identified
- Quarterly as part of process improvement

### Updates
To update a policy:
1. Edit the `.md` file
2. Commit changes to git
3. Restart the application (auto-reindexes)

## Troubleshooting

### "Policy vector store not initialized"
**Solution**: Check that `policies/` directory exists and contains `.md` files

### Poor retrieval quality
**Solutions**:
- Use more specific queries
- Improve policy document structure (better headers)
- Add more detailed examples
- Increase `top_k` parameter

### Indexing fails
**Solutions**:
- Check OpenAI API key is configured
- Verify `.md` files are valid markdown
- Check for file encoding issues (should be UTF-8)

## Summary

The Policy RAG system enables:
- ✅ **Dynamic guidance** for orchestrator decisions
- ✅ **Separation** of policies from code
- ✅ **Easy updates** without code changes
- ✅ **Consistent** workflow execution
- ✅ **Reduced** system prompt token usage
