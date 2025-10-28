# Claude Desktop Setup Guide

This guide explains how to use the Looker MCP Server with Claude Desktop and other MCP-compatible tools using the **stdio** transport protocol.

## Overview

The Looker MCP Server supports **two deployment modes**:

### 1. **Stdio Mode** (for Claude Desktop, Cursor, etc.)
- Direct integration with desktop AI assistants
- Uses stdin/stdout for communication
- Runs locally on your machine
- Perfect for personal use and development

### 2. **HTTP Mode** (for Cloud Run)
- Web service deployment for team/organization use
- RESTful API endpoints
- Runs on Google Cloud infrastructure
- Perfect for production and multi-user access

**This guide covers Stdio Mode for Claude Desktop.**

## Prerequisites

### 1. Python Environment
- Python 3.8 or higher
- pip package manager

### 2. Google Cloud Authentication
```bash
# Install gcloud CLI
# Download from: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login

# Enable Conversational Analytics API
gcloud services enable geminidataanalytics.googleapis.com
```

### 3. Looker Credentials
- Looker API Client ID
- Looker API Client Secret
- Looker instance URL

## Installation

### Step 1: Clone or Download the Repository

```bash
git clone https://github.com/cyrusj89/looker-mcp.git
cd looker-mcp
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy from template
cp .env.example .env

# Edit with your values
nano .env  # or use your preferred editor
```

Add your credentials:

```env
LOOKER_BASE_URL=https://labelboxdata.cloud.looker.com
LOOKER_CLIENT_ID=your_client_id_here
LOOKER_CLIENT_SECRET=your_client_secret_here
LOOKER_VERIFY_SSL=false
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
```

**Security Note**: The `.env` file is gitignored and should never be committed.

## Claude Desktop Configuration

### For macOS

1. **Locate the config file**:
   ```bash
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. **Edit the configuration**:
   ```json
   {
     "mcpServers": {
       "looker-conversational-analytics": {
         "command": "/path/to/your/venv/bin/python",
         "args": [
           "/path/to/looker-mcp/looker_conversational_analytics_mcp.py"
         ],
         "env": {
           "LOOKER_BASE_URL": "https://labelboxdata.cloud.looker.com",
           "LOOKER_CLIENT_ID": "your_client_id",
           "LOOKER_CLIENT_SECRET": "your_client_secret",
           "LOOKER_VERIFY_SSL": "false",
           "GOOGLE_CLOUD_PROJECT": "your_gcp_project_id"
         }
       }
     }
   }
   ```

### For Windows

1. **Locate the config file**:
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```

2. **Edit the configuration**:
   ```json
   {
     "mcpServers": {
       "looker-conversational-analytics": {
         "command": "C:\\path\\to\\your\\venv\\Scripts\\python.exe",
         "args": [
           "C:\\Users\\cyrus\\OneDrive - Labelbox\\Documents\\looker-mcp-cloud\\looker_conversational_analytics_mcp.py"
         ],
         "env": {
           "LOOKER_BASE_URL": "https://labelboxdata.cloud.looker.com",
           "LOOKER_CLIENT_ID": "nXFhdSpzgkTyzkTcGZjf",
           "LOOKER_CLIENT_SECRET": "Y4bGYJ2jdmrQwHdb5Vhqtfdk",
           "LOOKER_VERIFY_SSL": "false",
           "GOOGLE_CLOUD_PROJECT": "your_gcp_project_id"
         }
       }
     }
   }
   ```

**Important**: Use double backslashes (`\\`) in Windows paths or forward slashes (`/`).

### Alternative: Using System Python

If you prefer not to use a virtual environment:

```json
{
  "mcpServers": {
    "looker-conversational-analytics": {
      "command": "python",
      "args": [
        "/full/path/to/looker_conversational_analytics_mcp.py"
      ],
      "env": {
        "LOOKER_BASE_URL": "https://labelboxdata.cloud.looker.com",
        "LOOKER_CLIENT_ID": "your_client_id",
        "LOOKER_CLIENT_SECRET": "your_client_secret",
        "LOOKER_VERIFY_SSL": "false",
        "GOOGLE_CLOUD_PROJECT": "your_gcp_project_id"
      }
    }
  }
}
```

**Note**: Ensure all required packages are installed in your system Python environment.

## Verification

### Step 1: Test the MCP Server Directly

```bash
# Activate your virtual environment first
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Run the server (it will wait for stdin)
python looker_conversational_analytics_mcp.py
```

If it runs without errors, the server is working correctly. Press Ctrl+C to exit.

### Step 2: Restart Claude Desktop

1. Completely quit Claude Desktop
2. Reopen Claude Desktop
3. Check the settings/tools menu to verify the MCP server appears

### Step 3: Test with a Query

In Claude Desktop, try:

```
Can you use the looker_conversational_analytics tool to query:
"What are the top 10 products by revenue?"

Use these explore references:
- Model: ecommerce
- Explore: order_items
```

Claude should recognize the tool and execute the query.

## Troubleshooting

### Issue: "Server not found" or "Connection failed"

**Cause**: Path or Python environment issues

**Solutions**:
1. Verify Python path:
   ```bash
   # Mac/Linux
   which python

   # Windows
   where python
   ```

2. Use absolute paths in the configuration
3. Check that the virtual environment is correctly set up
4. Verify environment variables are set correctly

### Issue: "Authentication Error"

**Cause**: Google Cloud credentials not configured

**Solutions**:
1. Run authentication:
   ```bash
   gcloud auth application-default login
   ```

2. Verify credentials file exists:
   ```bash
   # Mac/Linux
   ls ~/.config/gcloud/application_default_credentials.json

   # Windows
   dir %APPDATA%\gcloud\application_default_credentials.json
   ```

3. Check Google Cloud project ID is correct

### Issue: "Looker Connection Failed"

**Cause**: Invalid Looker credentials or URL

**Solutions**:
1. Verify credentials in Looker Admin panel
2. Test credentials manually:
   ```bash
   curl -X POST "https://your-instance.looker.com/api/4.0/login" \
     -d "client_id=your_id&client_secret=your_secret"
   ```

3. Check LOOKER_BASE_URL format (no trailing slash)
4. Verify SSL settings match your Looker instance

### Issue: "Module not found" errors

**Cause**: Dependencies not installed

**Solution**:
```bash
# Make sure you're in the right directory and virtual environment
cd /path/to/looker-mcp
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: Claude Desktop doesn't show the tool

**Causes**:
1. Configuration file syntax error
2. Server failed to start
3. Claude Desktop not restarted

**Solutions**:
1. Validate JSON syntax: https://jsonlint.com/
2. Check Claude Desktop logs (if available)
3. Ensure you've completely quit and restarted Claude Desktop
4. Test the server independently first

## Advanced Configuration

### Using dotenv for Environment Variables

Instead of specifying environment variables in the Claude Desktop config, you can use a `.env` file:

1. **Install python-dotenv**:
   ```bash
   pip install python-dotenv
   ```

2. **Create `.env` file** (see Step 4 in Installation)

3. **Simplified Claude Desktop config**:
   ```json
   {
     "mcpServers": {
       "looker-conversational-analytics": {
         "command": "/path/to/venv/bin/python",
         "args": [
           "/path/to/looker_conversational_analytics_mcp.py"
         ]
       }
     }
   }
   ```

4. **Update the Python script** to load from `.env`:
   ```python
   # Add at the top of looker_conversational_analytics_mcp.py
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Multiple Looker Instances

To connect to multiple Looker instances, create separate server entries:

```json
{
  "mcpServers": {
    "looker-production": {
      "command": "python",
      "args": ["/path/to/looker_conversational_analytics_mcp.py"],
      "env": {
        "LOOKER_BASE_URL": "https://production.looker.com",
        "LOOKER_CLIENT_ID": "prod_id",
        "LOOKER_CLIENT_SECRET": "prod_secret",
        "GOOGLE_CLOUD_PROJECT": "prod_project"
      }
    },
    "looker-staging": {
      "command": "python",
      "args": ["/path/to/looker_conversational_analytics_mcp.py"],
      "env": {
        "LOOKER_BASE_URL": "https://staging.looker.com",
        "LOOKER_CLIENT_ID": "staging_id",
        "LOOKER_CLIENT_SECRET": "staging_secret",
        "GOOGLE_CLOUD_PROJECT": "staging_project"
      }
    }
  }
}
```

## Usage Examples

### Basic Query

```
Query the top 10 users by order count using the ecommerce model, users explore
```

### Multi-Explore Query

```
Analyze sales trends by comparing data from both orders and order_items explores
in the ecommerce model
```

### Complex Analysis with Python

```
Calculate customer cohort retention rates by signup month with Python analysis
enabled, using the users explore
```

### JSON Response Format

```
Give me product revenue data in JSON format using the order_items explore
```

## Best Practices

### Security
1. **Never commit** `.env` files or credentials to git
2. Use **read-only Looker API credentials** when possible
3. Enable **SSL verification** in production environments
4. Rotate credentials regularly

### Performance
1. **Be specific** with explore references to reduce API overhead
2. **Start simple** - test with basic queries first
3. **Use Python analysis** only when needed (it increases processing time)
4. **Limit result sets** with specific time ranges or filters in your questions

### Development
1. **Test queries** in Looker Explore UI first
2. **Verify explore names** match exactly (case-sensitive)
3. **Use descriptive questions** for better AI understanding
4. **Monitor quota usage** in Google Cloud Console

## Getting Help

### Check Logs

Claude Desktop logs (if available) can help diagnose issues.

### Test Components Separately

1. **Test Google Cloud authentication**:
   ```bash
   gcloud auth application-default print-access-token
   ```

2. **Test Looker API**:
   ```bash
   curl -X POST "https://your-instance.looker.com/api/4.0/login" \
     -d "client_id=YOUR_ID&client_secret=YOUR_SECRET"
   ```

3. **Test MCP server**:
   ```bash
   python looker_conversational_analytics_mcp.py
   ```

### Common Questions

**Q: Can I use this with Cursor or other MCP clients?**
A: Yes! The stdio mode works with any MCP-compatible client. Configuration may vary slightly.

**Q: Does this work offline?**
A: No, it requires internet access to connect to Google Cloud APIs and your Looker instance.

**Q: What about rate limits?**
A: Both Google Conversational Analytics API and Looker API have rate limits. Monitor usage in respective consoles.

**Q: Can I use this with Looker (Google Cloud core)?**
A: Yes, the configuration is the same. Just use your Looker (Google Cloud core) instance URL.

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [Claude Desktop Guide](https://claude.ai/desktop)
- [Conversational Analytics API Docs](https://cloud.google.com/gemini/docs/conversational-analytics-api)
- [Looker API Reference](https://cloud.google.com/looker/docs/api)

## Support

For issues specific to:
- **Claude Desktop**: Check Claude's support resources
- **Google Cloud APIs**: Visit Google Cloud Support
- **Looker**: Contact Looker support or check community forums
- **This MCP Server**: Open an issue on GitHub

---

**Note**: For production deployments serving multiple users, consider the [Cloud Run deployment](CLOUD_RUN_DEPLOYMENT.md) option instead of stdio mode.
