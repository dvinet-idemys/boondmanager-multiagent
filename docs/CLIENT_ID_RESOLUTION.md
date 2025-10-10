# Client ID Resolution Strategy

## Problem
When receiving a billing email, determine which BoondManager `client_id` to use for invoice creation.

## Solution: Project-Based Lookup

### Flow
```
Email → Extract Project Name → GET /projects → Match Project → Get Client ID
```

### Steps

1. **Parse Email** - Extract project name from email content
   ```
   "Jean Dupont: 20 days - Project Alpha"
   → Project: "Project Alpha"
   ```

2. **Lookup Projects** - Query BoondManager
   ```
   GET /projects?status=active
   ```

3. **Match Project** - Find project by name
   ```python
   project = find_project("Project Alpha", all_projects)
   ```

4. **Extract Client ID** - From project response
   ```json
   {
     "id": "project-123",
     "name": "Project Alpha",
     "client": {
       "id": "client-456",
       "name": "ACME Corporation"
     }
   }
   ```

## Implementation

### Required API Endpoint
- **Endpoint**: `GET /projects?status=active`
- **Response**: Must include `client.id` and `client.name`

### State Schema Addition
```python
class ProjectInfo(TypedDict):
    name: str
    boond_id: Optional[str]
    client_id: Optional[str]
    client_name: Optional[str]

# Add to InvoiceWorkflowState:
projects: List[ProjectInfo]
primary_client_id: Optional[str]  # Resolved from project
```

### Workflow Integration
Add new step between email parsing and reconciliation:
```
extract_email → resolve_project_client → reconcile_cra → ...
```

## Edge Cases

**Multiple Projects**: MVP requires single project per email
**Project Not Found**: Fail workflow with error notification
**Ambiguous Match**: Use exact match, log warning for partial matches

## Benefits
✅ Dynamic - no hardcoded mappings
✅ Scalable - works with any number of clients
✅ Accurate - uses BoondManager as source of truth
