# Looker MCP Server Architecture

This document explains the architecture and design of the Looker MCP Server, covering both deployment modes.

## Overview

The Looker MCP Server provides a bridge between AI assistants and Looker's Conversational Analytics API, supporting two deployment architectures:

1. **Stdio Mode**: Direct integration with desktop AI tools
2. **HTTP Mode**: Scalable cloud deployment

## Architecture Diagrams

### Stdio Mode (Claude Desktop / Cursor)

```
┌─────────────────────────────────────────────────────────────────┐
│                     User's Local Machine                        │
│                                                                 │
│  ┌──────────────────┐                                          │
│  │  Claude Desktop  │                                          │
│  │    or Cursor     │                                          │
│  └────────┬─────────┘                                          │
│           │ MCP Protocol (stdio)                               │
│           │                                                     │
│  ┌────────▼──────────────────────────────────────┐            │
│  │  looker_conversational_analytics_mcp.py       │            │
│  │                                                │            │
│  │  - FastMCP Server                             │            │
│  │  - Tool: looker_conversational_analytics      │            │
│  │  - Input validation (Pydantic)                │            │
│  │  - Response formatting                        │            │
│  └────────┬──────────────────────────────────────┘            │
│           │                                                     │
└───────────┼─────────────────────────────────────────────────────┘
            │
            │ HTTPS
            │
┌───────────▼─────────────────────────────────────────────────────┐
│                    Google Cloud Platform                        │
│                                                                 │
│  ┌─────────────────────────────────────────┐                  │
│  │  Conversational Analytics API            │                  │
│  │  (geminidataanalytics.googleapis.com)    │                  │
│  │                                           │                  │
│  │  - Natural language processing            │                  │
│  │  - SQL generation                         │                  │
│  │  - Query execution                        │                  │
│  │  - Python analysis (optional)             │                  │
│  └─────────────┬───────────────────────────┘                  │
│                │                                                 │
└────────────────┼─────────────────────────────────────────────────┘
                 │
                 │ HTTPS + Looker API Auth
                 │
┌────────────────▼─────────────────────────────────────────────────┐
│                    Looker Instance                               │
│              (labelboxdata.cloud.looker.com)                     │
│                                                                  │
│  ┌────────────────────────────────────────┐                    │
│  │  LookML Models & Explores               │                    │
│  │  - Semantic layer                        │                    │
│  │  - Business logic                        │                    │
│  │  - Data relationships                    │                    │
│  └────────────┬───────────────────────────┘                    │
│               │                                                   │
│  ┌────────────▼───────────────────────────┐                    │
│  │  Data Warehouse (BigQuery, etc.)        │                    │
│  └────────────────────────────────────────┘                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Key Components**:
- **AI Client**: Claude Desktop, Cursor, or other MCP-compatible tool
- **MCP Server**: Python process communicating via stdin/stdout
- **Conversational Analytics API**: Google's AI-powered query engine
- **Looker Instance**: Your Looker deployment with semantic layer
- **Data Warehouse**: Underlying data storage (BigQuery, Snowflake, etc.)

**Data Flow**:
1. User asks question in Claude Desktop
2. Claude invokes `looker_conversational_analytics` tool via MCP
3. MCP server sends request to Conversational Analytics API
4. API analyzes question and generates SQL using Looker explore structure
5. Looker executes query against data warehouse
6. Results flow back through chain: Looker → API → MCP → Claude
7. Claude presents formatted results to user

---

### HTTP Mode (Google Cloud Run)

```
┌─────────────────────────────────────────────────────────────────┐
│                          Clients                                 │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ Web Browser │  │   Mobile    │  │  API Client │           │
│  │    / App    │  │     App     │  │             │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         │                 │                 │                   │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          │                 │                 │
          │           HTTPS (POST /query)     │
          │                 │                 │
┌─────────▼─────────────────▼─────────────────▼───────────────────┐
│                    Google Cloud Run                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Container Instance(s)                       │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────┐            │  │
│  │  │  server.py (FastAPI HTTP Wrapper)      │            │  │
│  │  │                                         │            │  │
│  │  │  Endpoints:                             │            │  │
│  │  │  - GET  /          (info)               │            │  │
│  │  │  - GET  /health    (health check)       │            │  │
│  │  │  - GET  /tools     (list tools)         │            │  │
│  │  │  - POST /query     (execute query)      │            │  │
│  │  │  - POST /query/stream (streaming)       │            │  │
│  │  └────────┬───────────────────────────────┘            │  │
│  │           │                                              │  │
│  │  ┌────────▼──────────────────────────────┐             │  │
│  │  │  looker_conversational_analytics_mcp  │             │  │
│  │  │                                        │             │  │
│  │  │  - Tool implementation                 │             │  │
│  │  │  - Input validation                    │             │  │
│  │  │  - Response formatting                 │             │  │
│  │  └────────┬──────────────────────────────┘             │  │
│  │           │                                              │  │
│  └───────────┼──────────────────────────────────────────────┘  │
│              │                                                 │
│  ┌───────────▼──────────────────────────────────────────────┐  │
│  │  Secret Manager                                          │  │
│  │  - looker-client-id                                      │  │
│  │  - looker-client-secret                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Cloud Logging & Monitoring                              │  │
│  │  - Request logs                                           │  │
│  │  - Error tracking                                         │  │
│  │  - Performance metrics                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      │ HTTPS
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│              Conversational Analytics API                        │
│  (same as stdio mode - see diagram above)                       │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│              Looker Instance                                     │
│  (same as stdio mode - see diagram above)                       │
└──────────────────────────────────────────────────────────────────┘
```

**Key Components**:
- **Cloud Run**: Serverless container platform with auto-scaling
- **FastAPI Wrapper**: HTTP server exposing MCP tool as REST API
- **Secret Manager**: Secure credential storage
- **Cloud Logging**: Centralized logging and monitoring
- **Load Balancer**: Automatic HTTPS and traffic distribution

**Additional Features**:
- Auto-scaling from 0 to N instances based on traffic
- Built-in HTTPS certificates
- Health checks and automatic restarts
- Streaming responses via Server-Sent Events (SSE)
- Request/response logging
- Secure credential injection from Secret Manager

---

## Component Details

### 1. MCP Server Core (`looker_conversational_analytics_mcp.py`)

**Responsibilities**:
- Implements FastMCP server
- Defines `looker_conversational_analytics` tool
- Validates input using Pydantic models
- Authenticates to Google Cloud
- Constructs API requests
- Formats responses (Markdown or JSON)
- Handles errors gracefully

**Key Classes**:
```python
ConversationalAnalyticsInput  # Input validation model
ExploreReference              # Looker explore reference
ResponseFormat                # Output format enum (Markdown/JSON)
```

**Key Functions**:
```python
looker_conversational_analytics()  # Main tool implementation
get_environment_config()           # Load and validate env vars
initialize_clients()               # Setup Google Cloud clients
format_response_markdown()         # Format as Markdown
format_response_json()             # Format as JSON
```

### 2. HTTP Wrapper (`server.py`) - Cloud Run Only

**Responsibilities**:
- Exposes HTTP/REST API
- Translates HTTP requests to MCP tool calls
- Provides health check endpoint
- Implements streaming responses (SSE)
- Handles CORS for web clients

**Endpoints**:
- `GET /`: Service information
- `GET /health`: Health check for Cloud Run
- `GET /tools`: List available tools and schemas
- `POST /query`: Execute query and return results
- `POST /query/stream`: Execute query with streaming response

### 3. Conversational Analytics API

**Responsibilities**:
- Natural language understanding
- SQL query generation
- Looker explore analysis
- Query optimization
- Python code execution (when enabled)
- Chart specification generation

**API Components**:
- `DataChatServiceClient`: Main client for queries
- `Message`: Request/response message types
- `Context`: Agent configuration and data sources
- `DatasourceReferences`: Looker explore configuration

### 4. Looker Instance

**Responsibilities**:
- Semantic layer (LookML)
- Business logic and metrics
- SQL generation and optimization
- Query execution
- Result formatting

## Authentication & Security

### Stdio Mode

```
┌──────────────────────────────────────────────────────────────┐
│  User's Machine                                              │
│                                                              │
│  Environment Variables:                                      │
│  - LOOKER_BASE_URL                                           │
│  - LOOKER_CLIENT_ID                                          │
│  - LOOKER_CLIENT_SECRET                                      │
│  - GOOGLE_CLOUD_PROJECT                                      │
│                                                              │
│  Google Cloud Credentials:                                   │
│  - Application Default Credentials (ADC)                     │
│  - Obtained via: gcloud auth application-default login      │
│  - Stored in: ~/.config/gcloud/application_default_credentials.json │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Security Features**:
- Credentials stored in environment variables or .env file
- Google Cloud uses ADC for authentication
- Looker credentials encrypted in memory
- SSL/TLS for all API communications

### HTTP Mode (Cloud Run)

```
┌──────────────────────────────────────────────────────────────┐
│  Google Cloud Run                                            │
│                                                              │
│  Environment Variables:                                      │
│  - LOOKER_BASE_URL (from deployment config)                  │
│  - GOOGLE_CLOUD_PROJECT (auto-injected)                      │
│                                                              │
│  Secrets (from Secret Manager):                              │
│  - LOOKER_CLIENT_ID → secret: looker-client-id              │
│  - LOOKER_CLIENT_SECRET → secret: looker-client-secret      │
│                                                              │
│  Service Account:                                            │
│  - Default Compute Service Account                           │
│  - IAM Roles:                                                │
│    • roles/geminidataanalytics.user                         │
│    • roles/secretmanager.secretAccessor                      │
│                                                              │
│  Network Security:                                           │
│  - HTTPS only (automatic certificates)                       │
│  - Optional authentication (IAM)                             │
│  - VPC connector for private Looker instances (optional)     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Security Features**:
- Credentials in Secret Manager (encrypted at rest)
- IAM-based service account authentication
- Automatic HTTPS with Google-managed certificates
- Optional Cloud Run authentication
- VPC connectivity for private networks
- Audit logging via Cloud Logging

## Data Flow Details

### Request Processing

1. **Input Validation**
   - Pydantic validates all input parameters
   - Check explore reference limits (max 5)
   - Validate query length constraints
   - Sanitize user inputs

2. **Authentication**
   - Retrieve Google Cloud credentials
   - Validate Looker API credentials
   - Initialize API clients

3. **API Request Construction**
   - Build explore references
   - Create inline context
   - Configure analysis options
   - Set system instructions

4. **Query Execution**
   - Stream responses from API
   - Collect all message parts
   - Handle progress updates
   - Monitor timeouts

5. **Response Formatting**
   - Parse system messages
   - Extract SQL, data, charts
   - Format as Markdown or JSON
   - Apply character limits
   - Add error context

### Response Structure

**Markdown Format**:
```markdown
# Conversational Analytics Response

## 💭 Analysis Steps
[Reasoning and approach]

## 📊 Answer
[Natural language response]

## 🔍 Looker Query Details
- Model: ecommerce
- Explore: order_items
- Fields: product_name, total_revenue

## 📝 Generated SQL
```sql
SELECT ...
```

## 📋 Query Results
| Column1 | Column2 |
|---------|---------|
| Value1  | Value2  |

## 📈 Visualization
[Chart specification available]
```

**JSON Format**:
```json
{
  "text_responses": ["Natural language answer"],
  "analysis_steps": ["Step 1", "Step 2"],
  "queries": [{
    "model": "ecommerce",
    "explore": "order_items",
    "sql": "SELECT ..."
  }],
  "results": [{
    "schema": [...],
    "data": [...]
  }],
  "charts": [...]
}
```

## Scaling Considerations

### Stdio Mode
- **Scaling**: One process per user
- **Concurrency**: Handled by AI client
- **Resource Usage**: Local machine resources
- **Cost**: Zero (except API usage)

### HTTP Mode (Cloud Run)
- **Scaling**: Automatic (0 to max instances)
- **Concurrency**: 80 requests per container (default)
- **Resource Usage**: 2 vCPU, 2 GB RAM per instance
- **Cost**: Pay per request + compute time

**Scaling Configuration**:
```yaml
# In cloudbuild.yaml
--min-instances: 0  # Scale to zero when idle
--max-instances: 10  # Limit maximum scale
--concurrency: 80   # Requests per container
--cpu: 2            # vCPUs per instance
--memory: 2Gi       # RAM per instance
--timeout: 300s     # Request timeout
```

## Performance Characteristics

### Typical Response Times

| Query Type | Stdio Mode | HTTP Mode | Notes |
|------------|-----------|-----------|-------|
| Simple aggregation | 5-15s | 6-16s | First query may be slower |
| Complex query | 15-30s | 16-31s | Depends on data volume |
| Multi-explore | 20-40s | 21-41s | API selects best explore |
| Python analysis | 30-60s | 31-61s | Additional processing time |

**Factors Affecting Performance**:
- Explore complexity and size
- Data warehouse query time
- Python analysis requirements
- Network latency
- Cold start (Cloud Run only)

### Optimization Strategies

1. **Query Optimization**
   - Use specific time ranges
   - Limit result sets with filters
   - Choose appropriate explores
   - Cache common queries (HTTP mode)

2. **Resource Optimization**
   - Use min instances for latency-sensitive apps
   - Adjust memory/CPU based on usage
   - Monitor and optimize timeout settings

3. **Cost Optimization**
   - Scale to zero when idle
   - Use appropriate instance limits
   - Monitor API quota usage
   - Implement query result caching

## Monitoring & Observability

### Stdio Mode
- **Logs**: Local stdout/stderr
- **Errors**: Returned to AI client
- **Debugging**: Run directly with Python

### HTTP Mode
- **Cloud Logging**: Centralized log aggregation
- **Cloud Monitoring**: Metrics and dashboards
- **Error Reporting**: Automatic error aggregation
- **Cloud Trace**: Request tracing

**Key Metrics to Monitor**:
- Request count and latency
- Error rate and types
- Instance count and utilization
- API quota usage
- Cost per request

## Deployment Comparison

| Feature | Stdio Mode | HTTP Mode |
|---------|-----------|-----------|
| **Use Case** | Personal/Desktop | Team/Production |
| **Setup Complexity** | Low | Medium |
| **Scalability** | One user | Unlimited users |
| **Availability** | When machine is on | 24/7 |
| **Cost** | $0 + API usage | ~$15-50/month + API |
| **Maintenance** | None | Minimal (automated) |
| **Security** | Local credentials | Secret Manager |
| **Monitoring** | None | Built-in |
| **Integration** | MCP clients only | Any HTTP client |

## Future Enhancements

Potential improvements for consideration:

1. **Response Caching**: Cache common query results
2. **Query History**: Store and retrieve past queries
3. **Streaming Improvements**: Real-time progress updates
4. **Multi-tenancy**: Support multiple Looker instances
5. **Custom Formatting**: User-defined response templates
6. **Webhook Support**: Trigger queries from external events
7. **GraphQL API**: Alternative API interface
8. **Dashboard Integration**: Direct embedding in Looker

## References

- [MCP Specification](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/anthropics/mcp-python)
- [Conversational Analytics API](https://cloud.google.com/gemini/docs/conversational-analytics-api)
- [Looker API Reference](https://cloud.google.com/looker/docs/api)
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
