# Looker Conversational Analytics MCP Server - Implementation Plan

## Overview
Build an MCP server that provides access to Looker's Conversational Analytics API, enabling AI assistants to ask natural language questions about data in Looker Explores.

## Research Summary

### Conversational Analytics API
- **Endpoint**: `geminidataanalytics.googleapis.com`
- **Purpose**: AI-powered natural language queries against Looker, BigQuery, and Looker Studio data
- **Key Features**:
  - Natural language to SQL/Python code
  - Support for up to 5 Looker Explores simultaneously
  - Multi-turn conversations (stateful and stateless modes)
  - Advanced analysis with Python code interpreter
  - Automatic chart generation

### Authentication Requirements
1. **Google Cloud Authentication**: 
   - Service account or user credentials for accessing the Conversational Analytics API
   - Requires `geminidataanalytics.googleapis.com` API enabled
   
2. **Looker Authentication**:
   - Option A: API Keys (client ID + secret)
   - Option B: Access Token
   - Required Looker permissions: Get LookML Model Explore, Run Inline Query

### API Workflow
1. Authenticate to Google Cloud
2. Create data source references with Looker credentials and explore information
3. Either create a data agent (stateful) or use inline context (stateless)
4. Send chat requests with natural language questions
5. Stream responses containing text, SQL, data, and charts

## Tool Design

### Tool: looker_conversational_analytics

**Purpose**: Ask natural language questions about Looker data using Google's Conversational Analytics API

**Input Parameters**:
1. `user_query_with_context` (str, required): The natural language question
   - Examples: "What are the top 10 products by revenue?", "Show me sales trends by month"
   
2. `explore_references` (list of dicts, required): List of 1-5 Looker explores to query
   - Format: `[{"model": "model_name", "explore": "explore_name"}, ...]`
   - The API will automatically select the most relevant explore for the question
   
3. `system_instruction` (str, optional): Additional context/instructions for the agent
   - Default: "Help analyze the data and provide clear insights."
   
4. `enable_python_analysis` (bool, optional): Enable advanced Python analysis
   - Default: False
   
5. `response_format` (enum, optional): Format for the response
   - Options: "markdown" (default), "json"

**Annotations**:
- `readOnlyHint`: True (only reads data)
- `destructiveHint`: False (non-destructive)
- `idempotentHint`: False (responses may vary)
- `openWorldHint`: True (interacts with external Looker/GCP services)

**Output**:
Returns formatted response containing:
- Natural language answer
- Generated SQL query (if applicable)
- Data results (if applicable)
- Chart specifications (if applicable)
- Reasoning steps

## Implementation Details

### Environment Variables
From Looker MCP Config:
- `LOOKER_BASE_URL`: https://labelboxdata.cloud.looker.com
- `LOOKER_CLIENT_ID`: nXFhdSpzgkTyzkTcGZjf
- `LOOKER_CLIENT_SECRET`: Y4bGYJ2jdmrQwHdb5Vhqtfdk
- `LOOKER_VERIFY_SSL`: false
- `GOOGLE_CLOUD_PROJECT`: GCP project ID (user must provide)

### Key Components

1. **Authentication Module**:
   - Google Cloud authentication using default application credentials
   - Looker API key management
   - Credential caching

2. **Conversational Analytics Client**:
   - Initialize `geminidataanalytics` SDK clients:
     - `DataChatServiceClient` for queries
   - Handle stateless chat mode (simpler, no state management needed)

3. **Query Handler**:
   - Build explore references from input
   - Create inline context with Looker credentials
   - Send chat request with user query
   - Stream and process responses
   - Format output based on response_format

4. **Response Formatter**:
   - Parse system messages (text, SQL, data, charts)
   - Convert to Markdown or JSON format
   - Handle errors gracefully

### Error Handling Strategy
- Authentication failures → Clear error message with setup instructions
- API quota exceeded → Inform user and suggest retry
- Invalid explore references → Validate and provide correction suggestions
- Query timeout → Set reasonable timeout (300s default), inform user
- Network errors → Retry logic with exponential backoff

### Response Format Examples

**Markdown Format** (default):
```markdown
## Query Analysis

**Question**: What are the top 10 products by revenue?

**Data Source**: Model: ecommerce, Explore: order_items

## SQL Generated
```sql
SELECT product_name, SUM(sale_price) as total_revenue
FROM order_items
GROUP BY product_name
ORDER BY total_revenue DESC
LIMIT 10
```

## Results
| Product Name | Total Revenue |
|--------------|---------------|
| Product A    | $125,000      |
| Product B    | $98,500       |
...

## Insights
The top 10 products account for 45% of total revenue...
```

**JSON Format**:
```json
{
  "question": "What are the top 10 products by revenue?",
  "data_source": {
    "model": "ecommerce",
    "explore": "order_items"
  },
  "sql": "SELECT ...",
  "results": [...],
  "chart_spec": {...},
  "insights": "..."
}
```

## Dependencies
- `google-cloud-geminidataanalytics` - Python SDK for Conversational Analytics API
- `google-auth` - Google Cloud authentication
- `mcp` - MCP Python SDK (FastMCP)
- `pydantic` - Input validation
- `httpx` - Async HTTP client (for Looker API if needed)

## Quality Checklist
- [ ] Tool follows MCP naming conventions: `looker_conversational_analytics`
- [ ] Comprehensive docstring with examples
- [ ] Pydantic model with proper validation and constraints
- [ ] Proper error handling with actionable messages
- [ ] Support for both Markdown and JSON response formats
- [ ] Reasonable timeouts and retry logic
- [ ] Secure credential handling (environment variables)
- [ ] Tool annotations properly set
- [ ] Type hints throughout
- [ ] Character limit handling (25,000 chars)

## Testing Strategy
1. **Authentication Test**: Verify Google Cloud and Looker authentication work
2. **Simple Query Test**: "Count of records" type questions
3. **Complex Query Test**: Questions requiring joins and aggregations
4. **Multiple Explores Test**: Query that could use different explores
5. **Error Scenarios**: Invalid explores, malformed queries, timeout handling
6. **Format Tests**: Verify both Markdown and JSON outputs

## Security Considerations
- Store Looker credentials in environment variables (not hardcoded)
- Use minimal required Looker permissions
- Set appropriate timeouts to prevent resource exhaustion
- Sanitize user inputs to prevent injection attacks
- Follow Google Cloud security best practices

## Next Steps
1. Set up development environment with required dependencies
2. Implement authentication module
3. Implement core query functionality
4. Add response formatting
5. Add error handling
6. Test with real Looker instance
7. Create comprehensive documentation
8. Package and deploy
