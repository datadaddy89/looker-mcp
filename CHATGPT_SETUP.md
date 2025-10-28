# Using Looker MCP Server with ChatGPT

This guide explains how to integrate the Looker MCP Server with ChatGPT using Custom GPTs.

## Important Note

**ChatGPT does not natively support MCP (Model Context Protocol).** MCP is primarily designed for:
- Claude Desktop ✅
- Cursor IDE ✅
- Other MCP-compatible tools ✅

However, we can still use our Looker server with ChatGPT via the **HTTP API** and **Custom GPTs**!

---

## Prerequisites

1. **ChatGPT Plus or Enterprise** subscription (required for Custom GPTs)
2. **Deployed Cloud Run service** (see [CLOUD_RUN_DEPLOYMENT.md](CLOUD_RUN_DEPLOYMENT.md))
3. **Service URL** from your Cloud Run deployment

---

## Setup Guide

### Step 1: Deploy to Cloud Run

If you haven't already deployed the HTTP server:

```bash
cd looker-mcp
./deploy.sh  # or deploy.ps1 on Windows
```

Save the service URL that's output at the end:
```
Service URL: https://looker-mcp-server-xxxxx-uc.a.run.app
```

### Step 2: Test Your Deployment

Verify the service is working:

```bash
# Test health endpoint
curl https://YOUR-SERVICE-URL/health

# Test query endpoint
curl -X POST https://YOUR-SERVICE-URL/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query_with_context": "What are the top 10 products by revenue?",
    "explore_references": [
      {"model": "ecommerce", "explore": "order_items"}
    ]
  }'
```

### Step 3: Create a Custom GPT

1. **Go to ChatGPT**:
   - Navigate to [https://chat.openai.com](https://chat.openai.com)
   - Click your profile picture in the bottom left
   - Select "My GPTs"
   - Click "Create a GPT"

2. **Configure the GPT**:

   #### In the "Create" Tab:
   - **Name**: "Looker Data Analyst"
   - **Description**: "Query Looker data using natural language. Ask questions about your data and get insights powered by Google's Conversational Analytics API."

   #### Instructions (paste this):
   ```
   You are a Looker data analyst that helps users query and analyze their Looker data using natural language.

   When a user asks a question about data:
   1. Identify which Looker model and explore are needed
   2. Use the queryLooker action to execute the query
   3. Present the results in a clear, easy-to-understand format
   4. Provide insights and recommendations based on the data

   Common Looker models and explores:
   - ecommerce model:
     - order_items: Product sales data
     - orders: Order-level data
     - users: Customer/user data
     - inventory_items: Product inventory

   Always ask for clarification if:
   - The user's question is ambiguous
   - You're unsure which model/explore to use
   - Multiple explores could answer the question

   Format responses with:
   - Clear headers and sections
   - Tables for data results
   - Key insights highlighted
   - Recommendations when appropriate
   ```

   #### Conversation Starters (add these):
   ```
   - What are the top selling products this quarter?
   - Show me user signup trends by month
   - Which customers have the highest lifetime value?
   - Compare sales across different regions
   ```

3. **Configure Actions**:

   Click "Configure" tab, then scroll to "Actions":

   - Click "Create new action"
   - Click "Import from URL"
   - Enter: `https://YOUR-SERVICE-URL/openapi.json`

   **If the URL doesn't work**, manually paste the schema:

   #### Manual Schema Configuration:

   Click "Edit" on the action schema and paste:

   ```yaml
   openapi: 3.0.0
   info:
     title: Looker Conversational Analytics API
     description: Query Looker data using natural language
     version: 1.0.0
   servers:
     - url: https://YOUR-SERVICE-URL.run.app

   paths:
     /query:
       post:
         operationId: queryLooker
         summary: Query Looker data with natural language
         requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 required:
                   - user_query_with_context
                   - explore_references
                 properties:
                   user_query_with_context:
                     type: string
                     description: Natural language question
                   explore_references:
                     type: array
                     items:
                       type: object
                       properties:
                         model:
                           type: string
                         explore:
                           type: string
                   system_instruction:
                     type: string
                     default: "Provide clear insights"
                   enable_python_analysis:
                     type: boolean
                     default: false
                   response_format:
                     type: string
                     enum: ["markdown", "json"]
                     default: "markdown"
         responses:
           '200':
             description: Success
   ```

   **Important**: Replace `YOUR-SERVICE-URL` with your actual Cloud Run URL!

4. **Authentication** (if needed):

   If you enabled authentication on Cloud Run:
   - In the Actions section, click "Authentication"
   - Choose "API Key" or "OAuth"
   - Configure according to your Cloud Run auth settings

   For public endpoints (default), select "None"

5. **Test the Action**:

   In the GPT builder, click "Test" and try:
   ```
   What are the top 10 products by revenue?
   ```

6. **Save and Publish**:
   - Click "Save" in the top right
   - Choose "Only me" or "Anyone with a link"
   - Click "Confirm"

---

## Usage Examples

Once your Custom GPT is set up, you can ask questions like:

### Basic Queries

```
What are the top 10 products by revenue this quarter?
```

The GPT will:
1. Identify the appropriate explore (order_items)
2. Call the queryLooker action
3. Format and present the results

### Complex Analysis

```
Show me user signup trends by month for the past year,
broken down by signup source
```

### Multi-Explore Queries

```
Compare sales performance across different customer segments
```

### With Python Analysis

```
Calculate the customer cohort retention rates and show statistical significance
```

---

## Alternative: Direct API Integration

If you don't have ChatGPT Plus, you can use the HTTP API directly from any application:

### Python Example

```python
import requests

url = "https://YOUR-SERVICE-URL/query"
payload = {
    "user_query_with_context": "What are the top 10 products by revenue?",
    "explore_references": [
        {"model": "ecommerce", "explore": "order_items"}
    ],
    "response_format": "json"
}

response = requests.post(url, json=payload)
result = response.json()
print(result["result"])
```

### JavaScript Example

```javascript
const response = await fetch('https://YOUR-SERVICE-URL/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_query_with_context: 'What are the top 10 products by revenue?',
    explore_references: [
      { model: 'ecommerce', explore: 'order_items' }
    ],
    response_format: 'json'
  })
});

const data = await response.json();
console.log(data.result);
```

### cURL Example

```bash
curl -X POST https://YOUR-SERVICE-URL/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query_with_context": "What are the top 10 products by revenue?",
    "explore_references": [
      {"model": "ecommerce", "explore": "order_items"}
    ],
    "response_format": "json"
  }'
```

---

## Comparison: ChatGPT vs Claude Desktop

| Feature | ChatGPT (Custom GPT) | Claude Desktop (MCP) |
|---------|---------------------|----------------------|
| **Protocol** | HTTP REST API | MCP (stdio) |
| **Setup** | Requires Cloud Run | Local installation |
| **Cost** | ChatGPT Plus + Cloud Run | Free (local) |
| **Integration** | Browser-based | Desktop app |
| **Sharing** | Easy (share GPT link) | Per-user setup |
| **Performance** | Network latency | Direct local |
| **Best For** | Teams, web access | Personal use |

---

## Troubleshooting

### Issue: "Action failed to execute"

**Causes**:
- Incorrect service URL in OpenAPI schema
- Cloud Run service is down
- Authentication issues

**Solutions**:
1. Verify service URL:
   ```bash
   gcloud run services list
   ```

2. Test endpoint manually:
   ```bash
   curl https://YOUR-SERVICE-URL/health
   ```

3. Check Cloud Run logs:
   ```bash
   gcloud run services logs read looker-mcp-server --limit=50
   ```

### Issue: "Schema validation failed"

**Cause**: Invalid OpenAPI schema format

**Solution**:
1. Validate your schema at [Swagger Editor](https://editor.swagger.io/)
2. Ensure all URLs point to your actual Cloud Run service
3. Check for YAML indentation errors

### Issue: "Timeout error"

**Cause**: Query taking too long (> 60s default timeout)

**Solutions**:
1. Simplify the query
2. Add specific filters/date ranges
3. Increase Cloud Run timeout:
   ```bash
   gcloud run services update looker-mcp-server \
     --region=us-central1 \
     --timeout=300
   ```

### Issue: "Authentication required"

**Cause**: Cloud Run service requires authentication

**Solutions**:
1. Make service public:
   ```bash
   gcloud run services add-iam-policy-binding looker-mcp-server \
     --region=us-central1 \
     --member="allUsers" \
     --role="roles/run.invoker"
   ```

2. Or configure authentication in Custom GPT Actions settings

---

## Advanced Configuration

### Enable Authentication

For production use, enable Cloud Run authentication:

1. **Update Cloud Run**:
   ```bash
   gcloud run services update looker-mcp-server \
     --region=us-central1 \
     --no-allow-unauthenticated
   ```

2. **Create Service Account for GPT**:
   ```bash
   gcloud iam service-accounts create chatgpt-looker \
     --display-name="ChatGPT Looker Access"

   gcloud run services add-iam-policy-binding looker-mcp-server \
     --region=us-central1 \
     --member="serviceAccount:chatgpt-looker@PROJECT.iam.gserviceaccount.com" \
     --role="roles/run.invoker"
   ```

3. **Generate Token**:
   ```bash
   gcloud auth print-identity-token
   ```

4. **Configure in Custom GPT**:
   - Actions → Authentication → Bearer Token
   - Paste the token

### Add Rate Limiting

Protect your API with rate limiting:

```python
# In server.py, add:
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/query")
@limiter.limit("10/minute")  # 10 requests per minute
async def query_looker(request: Request, query: QueryRequest):
    # ... existing code
```

### Custom Error Messages

Improve error handling for ChatGPT:

```python
# In server.py
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": str(exc.detail),
            "suggestion": "Try simplifying your query or check the model/explore names"
        }
    )
```

---

## Cost Considerations

### ChatGPT Custom GPT Approach

**Costs**:
- ChatGPT Plus: $20/month
- Cloud Run: ~$15-50/month (see [CLOUD_RUN_DEPLOYMENT.md](CLOUD_RUN_DEPLOYMENT.md))
- Conversational Analytics API: Variable

**Total**: ~$35-70/month for team usage

### Claude Desktop (MCP) Approach

**Costs**:
- Claude subscription: $20/month (Pro)
- Infrastructure: $0 (runs locally)
- Conversational Analytics API: Variable

**Total**: ~$20/month + API usage

---

## Best Practices

1. **Specific Queries**: Be specific about date ranges and filters
2. **Model/Explore Names**: Document your Looker structure in the GPT instructions
3. **Error Handling**: The GPT will show friendly errors if queries fail
4. **Monitoring**: Check Cloud Run logs regularly
5. **Cost Control**: Set max instances in Cloud Run config
6. **Testing**: Test queries in Looker first to validate explores

---

## Next Steps

1. **Deploy to Cloud Run** if you haven't already
2. **Create your Custom GPT** following this guide
3. **Test with sample queries** to verify setup
4. **Share with team** using the GPT share link
5. **Monitor usage** in Cloud Run console

---

## Getting Help

- **Custom GPT Issues**: Check [OpenAI Help Center](https://help.openai.com)
- **Cloud Run Issues**: See [CLOUD_RUN_DEPLOYMENT.md](CLOUD_RUN_DEPLOYMENT.md)
- **API Issues**: Check Cloud Run logs
- **General Questions**: Open an issue on [GitHub](https://github.com/datadaddy89/looker-mcp)

---

## Resources

- [OpenAI Custom GPTs Documentation](https://help.openai.com/en/articles/8554397-creating-a-gpt)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Cloud Run Authentication](https://cloud.google.com/run/docs/authenticating/overview)
- [Looker MCP Server Repo](https://github.com/datadaddy89/looker-mcp)

---

**Note**: For the best MCP experience, we recommend using [Claude Desktop](CLAUDE_DESKTOP_SETUP.md) which has native MCP support!
