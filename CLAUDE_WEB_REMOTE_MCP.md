# Claude Web App - Remote MCP Setup Guide

## 🎉 Great News: Claude Web DOES Support Custom Connectors!

As of 2025, Claude now supports **Remote MCP (Model Context Protocol)** custom connectors in the web app! This guide shows you how to connect your Looker MCP server to Claude's web interface.

## What is Remote MCP?

Remote MCP allows Claude (web and desktop) to connect to MCP servers hosted on the internet using the **HTTP Streamable transport protocol**. Unlike local stdio MCP, remote MCP servers:

- ✅ Run on cloud infrastructure (Google Cloud Run)
- ✅ Work with Claude web app
- ✅ Support multiple users simultaneously
- ✅ Require no local installation for end users
- ✅ Use HTTP with Server-Sent Events (SSE)

## Platform Support

Remote MCP connectors are available on:
- ✅ **Claude Web** (claude.ai)
- ✅ **Claude Desktop**
- ✅ **Pro, Team, Max, and Enterprise plans**
- ⚠️ Currently in Beta

---

## Prerequisites

### 1. Claude Subscription
- Claude Pro, Max, Team, or Enterprise plan
- Access to Settings → Connectors

### 2. Deployed MCP Server
Your Looker MCP server must be deployed to Google Cloud Run (publicly accessible).

---

## Step 1: Deploy Remote MCP Server

### Option A: Quick Deploy (Recommended)

```bash
cd looker-mcp-cloud

# Deploy using the remote MCP server
./deploy.sh
```

The remote MCP server (`remote_mcp_server.py`) implements the full MCP Streamable HTTP protocol required by Claude web.

### Option B: Manual Deployment

```bash
# 1. Enable APIs
gcloud services enable run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    geminidataanalytics.googleapis.com \
    secretmanager.googleapis.com

# 2. Build and deploy
gcloud builds submit --config cloudbuild.yaml

# 3. Get your service URL
gcloud run services describe looker-mcp-server \
    --region=us-central1 \
    --format="value(status.url)"
```

**Save this URL** - you'll need it for Claude configuration.

Example: `https://looker-mcp-server-xxxxx-uc.a.run.app`

---

## Step 2: Configure Claude Web App

### For Pro/Max Plans:

1. **Navigate to Settings**:
   - Go to [claude.ai](https://claude.ai)
   - Click your profile icon
   - Select "Settings"

2. **Access Connectors**:
   - Click "Connectors" in the left sidebar
   - Click "Add custom connector"

3. **Enter MCP Server URL**:
   ```
   https://looker-mcp-server-xxxxx-uc.a.run.app/mcp
   ```
   **Important**: Add `/mcp` to the end of your Cloud Run URL!

4. **Configure Name** (optional):
   - Name: "Looker Analytics"
   - Description: "Query Looker data with natural language"

5. **Authentication** (optional):
   - For public Cloud Run: Leave as "None"
   - For authenticated Cloud Run: Configure OAuth or API key

6. **Click "Add"**:
   - Claude will validate the connection
   - The connector will appear in your list

### For Team/Enterprise Plans:

1. **Admin Configuration**:
   - Primary Owners or Owners go to Admin Settings
   - Navigate to "Connectors"
   - Click "Add custom connector"
   - Enter MCP server URL with `/mcp` path
   - Configure authentication if needed
   - Save the connector

2. **User Activation**:
   - Individual users go to Settings → Connectors
   - Find "Looker Analytics" in the list
   - Click "Connect" to authenticate (if required)
   - Toggle specific tools on/off

---

## Step 3: Enable and Use the Connector

### Enable Tools:

1. **In any chat**:
   - Click the "Search and tools" button (🔍 icon)
   - Look for "Looker Analytics" connector
   - Toggle it ON

2. **For authenticated services**:
   - Click "Connect" to authorize access
   - Complete OAuth flow if configured
   - Return to Claude

### Start Querying:

Simply ask Claude natural language questions:

```
What are the top 10 products by revenue this quarter?
```

Claude will:
1. Recognize this is a Looker query
2. Call the `looker_conversational_analytics` tool
3. Pass your question to the Conversational Analytics API
4. Return formatted results with insights

---

## Example Queries

### Basic Analytics:
```
Show me monthly sales trends for the past year
```

### Complex Analysis:
```
Compare customer lifetime value across different acquisition channels
```

### Multi-Explore:
```
Analyze the correlation between user signup patterns and order volume
```

### With Context:
```
Using the ecommerce model, what's the average order value by customer segment?
```

---

## Troubleshooting

### Issue: "Failed to connect to custom connector"

**Possible Causes**:
1. Cloud Run service is not deployed
2. Service URL is incorrect
3. Missing `/mcp` path in URL
4. Service requires authentication

**Solutions**:

1. **Verify deployment**:
   ```bash
   gcloud run services list --filter="looker-mcp-server"
   ```

2. **Test endpoint manually**:
   ```bash
   curl -X POST https://YOUR-URL/mcp \
     -H "Content-Type: application/json" \
     -H "MCP-Protocol-Version: 2024-11-05" \
     -d '{
       "jsonrpc": "2.0",
       "id": 1,
       "method": "initialize",
       "params": {
         "protocolVersion": "2024-11-05",
         "capabilities": {},
         "clientInfo": {"name": "test", "version": "1.0.0"}
       }
     }'
   ```

   Should return:
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "result": {
       "protocolVersion": "2024-11-05",
       "capabilities": {...},
       "serverInfo": {"name": "looker-mcp-server", "version": "1.0.0"}
     }
   }
   ```

3. **Check logs**:
   ```bash
   gcloud run services logs read looker-mcp-server --limit=50
   ```

### Issue: "Origin validation failed"

**Cause**: CORS configuration issue

**Solution**: Update `remote_mcp_server.py` CORS settings:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://claude.ai",
        "https://*.claude.ai",
        "https://your-domain.com"  # Add your domain
    ],
    ...
)
```

Redeploy after changes.

### Issue: "Tool execution failed"

**Causes**:
1. Invalid Looker credentials
2. Google Cloud authentication issues
3. Explore references don't exist

**Solutions**:

1. **Check environment variables**:
   ```bash
   gcloud run services describe looker-mcp-server \
     --region=us-central1 \
     --format="value(spec.template.spec.containers[0].env)"
   ```

2. **Verify secrets**:
   ```bash
   gcloud secrets versions access latest --secret=looker-client-id
   gcloud secrets versions access latest --secret=looker-client-secret
   ```

3. **Test Looker connection**:
   ```bash
   curl -X POST "https://labelboxdata.cloud.looker.com/api/4.0/login" \
     -d "client_id=YOUR_ID&client_secret=YOUR_SECRET"
   ```

### Issue: "Session expired"

**Cause**: Session timeout or server restart

**Solution**:
- Disable and re-enable the connector in Claude
- Refresh the page
- Start a new chat

---

## Configuration Options

### Public Access (Default)

Cloud Run service is publicly accessible:
- ✅ No authentication required
- ✅ Easy setup
- ⚠️ Anyone with URL can access
- 💡 Use for testing/development

### Authenticated Access (Production)

Require authentication for production:

#### Option 1: Cloud Run IAM

```bash
# Make service private
gcloud run services update looker-mcp-server \
    --region=us-central1 \
    --no-allow-unauthenticated

# Claude will use OAuth
```

In Claude:
- Configure OAuth in "Advanced settings"
- Use Google Cloud OAuth credentials

#### Option 2: API Key

Add API key validation in `remote_mcp_server.py`:

```python
API_KEY = os.getenv("MCP_API_KEY")

@app.post("/mcp")
async def mcp_endpoint_post(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    # Validate API key
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    # ... rest of code
```

In Claude:
- Select "API Key" authentication
- Enter your API key

---

## Cost Estimation

### Remote MCP on Cloud Run

**Monthly Costs** (10,000 queries, 30s avg):
- Cloud Run: $15-50
- Secret Manager: $0.12
- Artifact Registry: $0.10
- Conversational Analytics API: Variable
- **Total**: ~$15-60/month

### vs Other Options

| Option | Cost | Users | Setup | Best For |
|--------|------|-------|-------|----------|
| **Remote MCP (Web)** | $15-60/mo | Unlimited | Medium | Teams |
| **Stdio (Desktop)** | $0 | Single | Easy | Personal |
| **ChatGPT Custom GPT** | $20-50/mo | Unlimited | Easy | ChatGPT users |

---

## Security Best Practices

### 1. Origin Validation
✅ Already implemented in `remote_mcp_server.py`
- Validates `Origin` header
- Prevents DNS rebinding attacks

### 2. Authentication
- 🟢 **Development**: Public access OK
- 🟡 **Staging**: Consider API keys
- 🔴 **Production**: Use OAuth/IAM

### 3. Rate Limiting

Add to `remote_mcp_server.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/mcp")
@limiter.limit("10/minute")
async def mcp_endpoint_post(...):
    # ... existing code
```

### 4. Monitoring

Enable Cloud Run logging:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=looker-mcp-server" \
    --limit=50 \
    --format=json
```

### 5. Secrets Management
- ✅ Use Secret Manager (not env vars)
- ✅ Rotate credentials regularly
- ✅ Minimum required permissions

---

## Advanced Configuration

### Custom Session Management

For production, use Redis for session storage:

```python
import redis

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=6379,
    decode_responses=True
)

# Store sessions in Redis instead of memory
@app.post("/mcp")
async def mcp_endpoint_post(...):
    if method == "initialize":
        session_id = create_session_id()
        redis_client.setex(
            f"session:{session_id}",
            3600,  # 1 hour TTL
            json.dumps({
                "created_at": datetime.now().isoformat(),
                "protocol_version": mcp_protocol_version
            })
        )
```

### Multiple Looker Instances

Support multiple Looker environments:

```python
LOOKER_INSTANCES = {
    "production": {
        "url": os.getenv("LOOKER_PROD_URL"),
        "client_id": os.getenv("LOOKER_PROD_CLIENT_ID"),
        "client_secret": os.getenv("LOOKER_PROD_SECRET")
    },
    "staging": {
        "url": os.getenv("LOOKER_STAGING_URL"),
        "client_id": os.getenv("LOOKER_STAGING_CLIENT_ID"),
        "client_secret": os.getenv("LOOKER_STAGING_SECRET")
    }
}

# Add instance parameter to tool
```

### Custom Tool Metadata

Enhance tool descriptions:

```python
{
    "name": "looker_conversational_analytics",
    "description": "Query Looker data with natural language...",
    "inputSchema": {...},
    "metadata": {
        "examples": [
            "What are the top 10 products by revenue?",
            "Show me monthly sales trends"
        ],
        "availableExplores": [
            {"model": "ecommerce", "explore": "order_items"},
            {"model": "ecommerce", "explore": "users"}
        ]
    }
}
```

---

## Comparison: Remote MCP vs Other Methods

### Remote MCP (This Guide)
- ✅ Works in Claude web app
- ✅ Native MCP protocol
- ✅ Best integration with Claude
- ✅ Supports multiple users
- ⚠️ Requires Cloud Run deployment
- 💰 $15-60/month

### Stdio MCP (Desktop Only)
- ✅ No cloud infrastructure needed
- ✅ Free (except API usage)
- ✅ Direct local execution
- ❌ Claude Desktop only
- ❌ Per-user setup

### HTTP API (Legacy)
- ✅ Works with any HTTP client
- ✅ Simple REST API
- ❌ Not MCP protocol
- ❌ No native Claude integration
- ❌ Manual tool invocation

### ChatGPT Custom GPT
- ✅ Easy to share
- ✅ Works in web
- ❌ Not MCP protocol
- ❌ ChatGPT-specific
- 💰 $20/month + Cloud Run

---

## What's Next?

### Immediate Steps:
1. ✅ Deploy remote MCP server to Cloud Run
2. ✅ Add connector in Claude web settings
3. ✅ Enable tools and start querying

### Enhancements:
- Add authentication for production
- Implement rate limiting
- Set up monitoring and alerts
- Add custom session management
- Support multiple Looker instances

### Team Rollout:
- Share connector with team (Enterprise)
- Document available explores
- Create query examples
- Train users on capabilities

---

## Resources

- [Claude Custom Connectors Docs](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp)
- [MCP Specification](https://modelcontextprotocol.io)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Looker API Reference](https://cloud.google.com/looker/docs/api)

## Support

- **Connector Issues**: Check Cloud Run logs
- **MCP Protocol**: Review MCP specification
- **Looker Queries**: Test explores in Looker first
- **Claude Issues**: Contact Anthropic support
- **GitHub Issues**: [Open an issue](https://github.com/datadaddy89/looker-mcp/issues)

---

## Summary

**You CAN connect your Looker MCP server to Claude web app!**

1. Deploy `remote_mcp_server.py` to Cloud Run
2. Add connector in Claude settings with `/mcp` endpoint
3. Enable tools and start asking questions

This is the **official, supported way** to use custom MCP servers with Claude web. Enjoy! 🎉
