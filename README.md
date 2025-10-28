# Looker Conversational Analytics MCP Server

An MCP (Model Context Protocol) server that provides access to Looker's Conversational Analytics API, enabling AI assistants to ask natural language questions about data in Looker Explores.

**🚀 Now available for deployment on Google Cloud Run!** See [CLOUD_RUN_DEPLOYMENT.md](CLOUD_RUN_DEPLOYMENT.md) for deployment instructions.

## Overview

This MCP server integrates Google's Conversational Analytics API with Looker, allowing you to:

- 🗣️ **Query data using natural language** - No SQL or LookML knowledge required
- 🔍 **Multi-explore querying** - Query up to 5 different Looker Explores simultaneously
- 🤖 **AI-powered analysis** - Automatic SQL generation, data analysis, and insights
- 📊 **Automatic visualizations** - Generate charts and graphs from your queries
- 🐍 **Advanced Python analysis** - Enable complex statistical calculations and transformations
- ✅ **Grounded in truth** - Leverages Looker's semantic layer for accurate results

## Features

### Natural Language Queries
Ask questions in plain English:
- "What are the top 10 products by revenue this quarter?"
- "Show me user signup trends by month for the past year"
- "Which customers have the highest lifetime value?"
- "Compare sales performance across regions"

### Intelligent Explore Selection
Provide multiple explores and let the API automatically select the most relevant one for your question.

### Multi-Format Responses
Choose between:
- **Markdown**: Human-readable format with tables, headers, and formatted text
- **JSON**: Structured data for programmatic processing

### Advanced Analysis
Enable Python code interpreter for:
- Statistical analysis
- Complex calculations
- Advanced visualizations
- Period-over-period comparisons

## Deployment Options

### ☁️ Google Cloud Run (Production)
Deploy as a scalable HTTP service on Google Cloud Run for production use. Perfect for:
- Team/organization-wide access
- Integration with web applications
- Serverless, auto-scaling infrastructure
- Pay-per-use pricing

**Quick Deploy**:
```bash
./deploy.sh  # or deploy.ps1 for Windows
```

📖 **Full Guide**: See [CLOUD_RUN_DEPLOYMENT.md](CLOUD_RUN_DEPLOYMENT.md) for detailed instructions.

### 💻 Local/Desktop (Development)
Run locally for development and testing with Claude Desktop or other MCP clients.

**Quick Start**: See [Installation](#installation) section below.

## Prerequisites

### 1. Google Cloud Setup

1. **Create a Google Cloud Project** (or use existing):
   ```bash
   gcloud projects create my-looker-analytics
   gcloud config set project my-looker-analytics
   ```

2. **Enable required APIs**:
   ```bash
   gcloud services enable geminidataanalytics.googleapis.com
   gcloud services enable cloudaicompanion.googleapis.com
   ```

3. **Set up authentication**:
   ```bash
   # For development/testing
   gcloud auth application-default login
   
   # For production, use a service account:
   gcloud iam service-accounts create looker-ca-mcp \
     --display-name="Looker Conversational Analytics MCP"
   
   gcloud iam service-accounts keys create key.json \
     --iam-account=looker-ca-mcp@PROJECT_ID.iam.gserviceaccount.com
   
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
   ```

4. **Grant necessary IAM permissions**:
   ```bash
   # For the service account or your user account
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:looker-ca-mcp@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/geminidataanalytics.user"
   ```

### 2. Looker Setup

1. **Generate API credentials** in Looker:
   - Go to Admin → Users → Your User → Edit Keys
   - Generate new API3 keys
   - Save the Client ID and Client Secret

2. **Ensure proper Looker permissions**:
   - The API user needs:
     - `see_lookml` permission
     - `explore` permission
     - Access to the models/explores you want to query

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt --break-system-packages
   ```

   Or install individually:
   ```bash
   pip install mcp google-cloud-geminidataanalytics google-auth pydantic httpx --break-system-packages
   ```

3. **Set environment variables**:
   ```bash
   export LOOKER_BASE_URL="https://labelboxdata.cloud.looker.com"
   export LOOKER_CLIENT_ID="your_client_id"
   export LOOKER_CLIENT_SECRET="your_client_secret"
   export LOOKER_VERIFY_SSL="false"  # Set to "true" in production
   export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
   ```

   Or create a `.env` file (recommended):
   ```bash
   LOOKER_BASE_URL=https://labelboxdata.cloud.looker.com
   LOOKER_CLIENT_ID=your_client_id
   LOOKER_CLIENT_SECRET=your_client_secret
   LOOKER_VERIFY_SSL=false
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   ```

## Usage

### Running the Server

```bash
python looker_conversational_analytics_mcp.py
```

The server will start and listen for MCP protocol messages via stdio.

### Connecting to Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "looker-analytics": {
      "command": "python",
      "args": ["/path/to/looker_conversational_analytics_mcp.py"],
      "env": {
        "LOOKER_BASE_URL": "https://labelboxdata.cloud.looker.com",
        "LOOKER_CLIENT_ID": "your_client_id",
        "LOOKER_CLIENT_SECRET": "your_client_secret",
        "LOOKER_VERIFY_SSL": "false",
        "GOOGLE_CLOUD_PROJECT": "your-gcp-project-id"
      }
    }
  }
}
```

### Using the Tool

Once connected, you can use natural language to query your Looker data:

**Example 1: Simple Query**
```
Ask the looker_conversational_analytics tool:
"What are the top 10 products by revenue?" using the explore 
{"model": "ecommerce", "explore": "order_items"}
```

**Example 2: Multi-Explore Query**
```
Ask the looker_conversational_analytics tool:
"Compare user signups vs order volume by month for the past year" 
using explores:
- {"model": "ecommerce", "explore": "users"}
- {"model": "ecommerce", "explore": "orders"}
```

**Example 3: Advanced Analysis**
```
Ask the looker_conversational_analytics tool with Python analysis enabled:
"Calculate the cohort retention rate by signup month" using the explore
{"model": "ecommerce", "explore": "users"}
```

## Tool Parameters

### looker_conversational_analytics

**Required Parameters:**

- `user_query_with_context` (string): Your natural language question
  - Examples: "What are sales trends?", "Top customers by revenue?"
  - Max length: 5000 characters

- `explore_references` (list): 1-5 Looker explores to query
  - Format: `[{"model": "model_name", "explore": "explore_name"}, ...]`
  - The API automatically selects the most relevant explore

**Optional Parameters:**

- `system_instruction` (string): Additional context for the agent
  - Use to define business terms, specify formatting, or provide domain context
  - Default: "Help analyze the data and provide clear, actionable insights."
  - Max length: 5000 characters

- `enable_python_analysis` (boolean): Enable advanced Python code interpreter
  - Enables complex calculations and statistical analysis
  - May increase response time
  - Default: false

- `response_format` (enum): Output format
  - Options: "markdown" (default) or "json"
  - Markdown: Human-readable with tables and formatting
  - JSON: Structured data for programmatic processing

## Response Format

### Markdown Response (default)

```markdown
# Conversational Analytics Response

## 💭 Analysis Steps
Understanding your question...
Analyzing the order_items explore...
Generating SQL query...

## 🔍 Looker Query Details
- **Model**: ecommerce
- **Explore**: order_items
- **Fields**: products.name, order_items.total_revenue
- **Filters**: {"order_items.created_date": "this year"}

## 📝 Generated SQL
```sql
SELECT 
  products.name,
  SUM(order_items.sale_price) as total_revenue
FROM order_items
LEFT JOIN products ON order_items.product_id = products.id
WHERE order_items.created_date >= '2024-01-01'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10
```

## 📋 Query Results
| Product Name | Total Revenue |
|-------------|---------------|
| Product A   | $125,000      |
| Product B   | $98,500       |
...

## 📊 Answer
The top 10 products generated $1.2M in revenue this year, with Product A leading at $125K...
```

### JSON Response

```json
{
  "text_responses": [
    "The top 10 products generated $1.2M in revenue this year..."
  ],
  "analysis_steps": [
    "Understanding your question...",
    "Analyzing the order_items explore...",
    "Generating SQL query..."
  ],
  "queries": [
    {
      "model": "ecommerce",
      "explore": "order_items",
      "fields": ["products.name", "order_items.total_revenue"],
      "filters": {"order_items.created_date": "this year"},
      "sql": "SELECT products.name, SUM(order_items.sale_price) as total_revenue..."
    }
  ],
  "results": [
    {
      "schema": [
        {"name": "Product Name", "type": "string"},
        {"name": "Total Revenue", "type": "number"}
      ],
      "data": [
        {"Product Name": "Product A", "Total Revenue": 125000},
        {"Product Name": "Product B", "Total Revenue": 98500}
      ]
    }
  ],
  "charts": []
}
```

## Best Practices

### Query Construction

1. **Be specific**: "Top 10 products by revenue this quarter" vs "products"
2. **Provide context**: Include time frames, filters, and groupings in your question
3. **Use business terms**: The semantic layer understands your business language
4. **Start simple**: Test with simple queries before complex multi-step analysis

### Explore Selection

1. **Provide relevant explores**: Include explores that contain the data you need
2. **Limit to 5**: Maximum 5 explores per query for best performance
3. **Let the API decide**: Don't worry about which explore to use - the API will select the best one

### System Instructions

Use system instructions to:
- Define business-specific terms: "ARR means Annual Recurring Revenue"
- Set response preferences: "Always show results as percentages"
- Provide data context: "Our fiscal year starts in July"
- Guide formatting: "Round currency to nearest dollar"

### Performance Optimization

1. **Start without Python analysis**: Enable only when needed for complex calculations
2. **Be specific with filters**: Reduce data volume with time ranges and filters
3. **Limit result sets**: Ask for "top N" instead of all results
4. **Use pagination**: For large datasets, query in chunks

## Troubleshooting

### Common Issues

**Error: "Missing required environment variables"**
- Solution: Ensure all environment variables are set correctly
- Check: `echo $LOOKER_BASE_URL` to verify

**Error: "Google Cloud authentication failed"**
- Solution: Run `gcloud auth application-default login`
- Or set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

**Error: "Permission denied" or "403"**
- Solution: Check IAM permissions in Google Cloud
- Ensure your account has `roles/geminidataanalytics.user` role

**Error: "Looker authentication failed"**
- Solution: Verify Looker client ID and secret are correct
- Check that the API user has necessary Looker permissions

**Error: "Explore not found"**
- Solution: Verify model and explore names are correct
- Check that the user has access to these explores in Looker

**Timeout errors**
- Solution: Simplify your query or break into smaller parts
- Enable Python analysis only when needed
- Increase timeout if working with large datasets

### Debug Mode

For debugging, you can add verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

### Credentials
- ✅ Store credentials in environment variables (not in code)
- ✅ Use service accounts for production
- ✅ Rotate credentials regularly
- ✅ Use Secret Manager in production environments

### Access Control
- ✅ Leverage Looker's row-level security
- ✅ Use minimal required IAM permissions
- ✅ Audit API usage regularly
- ✅ Implement request rate limiting if needed

### Data Protection
- ✅ Enable SSL verification in production (`LOOKER_VERIFY_SSL=true`)
- ✅ Use private IP or VPN for Looker connections when possible
- ✅ Follow your organization's data governance policies
- ✅ Be mindful of PII in natural language queries

## Cost Considerations

### Google Cloud Costs
- Conversational Analytics API charges per query
- Python analysis may incur additional compute costs
- Monitor usage in Google Cloud Console
- Set spending alerts and quotas

### Optimization Tips
- Cache common queries when appropriate
- Use filters to reduce data scanned
- Start simple before adding Python analysis
- Monitor and optimize expensive queries

## API Limits

- **Maximum explores per query**: 5
- **Query timeout**: 300 seconds (5 minutes)
- **Response size limit**: 25,000 characters (truncated if exceeded)
- **Rate limits**: Subject to Google Cloud API quotas

## Advanced Usage

### Custom System Instructions

Provide detailed context for your domain:

```json
{
  "system_instruction": "You are analyzing e-commerce data for a B2B SaaS company. \n\nKey metrics: \n- MRR: Monthly Recurring Revenue \n- ARR: Annual Recurring Revenue \n- LTV: Lifetime Value \n- CAC: Customer Acquisition Cost \n\nAlways calculate metrics on a monthly basis unless otherwise specified. Show currency in USD rounded to nearest dollar. When showing growth, include both absolute and percentage changes."
}
```

### Multi-Step Analysis

For complex analysis, break into steps:

1. First query: Get base data
2. Second query: Analyze trends (referencing first query)
3. Third query: Generate comparisons

The API maintains context in multi-turn conversations.

## Example Queries

### Sales Analysis
```
"What were the top 5 products by revenue last quarter, and how does that compare to the previous quarter?"
```

### User Behavior
```
"Show me user signup trends by month for the past year, broken down by traffic source"
```

### Cohort Analysis (with Python)
```
"Calculate the retention rate by cohort for users who signed up in each month of 2024"
```

### Geographic Analysis
```
"Which regions have the highest average order value, and what percentage of total revenue does each region represent?"
```

### Time Series
```
"Plot daily active users over the past 90 days and identify any anomalies"
```

## Support

For issues or questions:

1. **MCP Server Issues**: Check this README and troubleshooting section
2. **Conversational Analytics API**: [Official Documentation](https://cloud.google.com/gemini/docs/conversational-analytics-api)
3. **Looker API**: [Looker API Documentation](https://cloud.google.com/looker/docs/api)
4. **Google Cloud Support**: [Google Cloud Console](https://console.cloud.google.com/support)

## Architecture

```
┌─────────────────┐
│   AI Assistant  │
│   (Claude)      │
└────────┬────────┘
         │ MCP Protocol
         ↓
┌─────────────────────────────────┐
│  Looker CA MCP Server           │
│  ┌──────────────────────────┐   │
│  │  Tool Handler            │   │
│  │  - Input validation      │   │
│  │  - Credential management │   │
│  └────────┬─────────────────┘   │
└───────────┼─────────────────────┘
            ↓
┌───────────────────────────────────┐
│  Google Cloud                     │
│  Conversational Analytics API     │
│  ┌───────────────────────────┐   │
│  │  AI Analysis Engine       │   │
│  │  - NL2SQL                 │   │
│  │  - Python Code Interpreter│   │
│  │  - Context Retrieval      │   │
│  └──────────┬────────────────┘   │
└─────────────┼────────────────────┘
              ↓
┌─────────────────────────────────┐
│  Looker Instance                │
│  ┌─────────────────────────┐   │
│  │  LookML Models          │   │
│  │  Explores & Dimensions  │   │
│  │  Semantic Layer         │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Powered by [Google Cloud Conversational Analytics API](https://cloud.google.com/gemini/docs/conversational-analytics-api)
- Integrates with [Looker](https://cloud.google.com/looker/docs)
