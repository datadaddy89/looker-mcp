# Looker Conversational Analytics MCP Server - Quick Start

Welcome! This package contains everything you need to set up and run a Looker Conversational Analytics MCP server.

## 📦 What's Included

### Core Files
- **looker_conversational_analytics_mcp.py** - Main MCP server implementation (25KB)
- **requirements.txt** - Python dependencies
- **.env.example** - Configuration template

### Documentation
- **README.md** - Complete setup and usage guide (17KB)
- **TESTING.md** - Comprehensive testing guide (11KB)
- **PROJECT_SUMMARY.md** - Project overview (10KB)
- **looker_ca_mcp_implementation_plan.md** - Development plan and research (7KB)

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt --break-system-packages
```

### 2. Configure Environment
```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your actual values
# - LOOKER_BASE_URL: Your Looker instance URL
# - LOOKER_CLIENT_ID: Your Looker API client ID
# - LOOKER_CLIENT_SECRET: Your Looker API client secret
# - GOOGLE_CLOUD_PROJECT: Your GCP project ID

# Load environment variables
export $(cat .env | xargs)
```

### 3. Set Up Google Cloud Authentication
```bash
# Option A: Use your personal account (for testing)
gcloud auth application-default login

# Option B: Use a service account (for production)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 4. Run the Server
```bash
python looker_conversational_analytics_mcp.py
```

### 5. Connect from Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "looker-analytics": {
      "command": "python",
      "args": ["/full/path/to/looker_conversational_analytics_mcp.py"],
      "env": {
        "LOOKER_BASE_URL": "https://your-instance.looker.com",
        "LOOKER_CLIENT_ID": "your_client_id",
        "LOOKER_CLIENT_SECRET": "your_client_secret",
        "GOOGLE_CLOUD_PROJECT": "your-gcp-project"
      }
    }
  }
}
```

## 📖 Next Steps

1. **Read README.md** for detailed setup instructions
2. **Review TESTING.md** for test cases and validation
3. **Check PROJECT_SUMMARY.md** for architecture overview
4. **Try example queries** from the documentation

## 💡 Example Query

Once connected to Claude:

```
Use the looker_conversational_analytics tool to answer: 
"What are the top 10 products by revenue this quarter?"

With explore references:
- model: "ecommerce"
- explore: "order_items"
```

## 🆘 Need Help?

### Common Issues
- **"Module not found"** → Run `pip install -r requirements.txt --break-system-packages`
- **"Credentials not found"** → Run `gcloud auth application-default login`
- **"Permission denied"** → Check IAM permissions in Google Cloud Console
- **"Explore not found"** → Verify model and explore names in Looker

### Resources
- Full troubleshooting guide in README.md
- Testing guide in TESTING.md
- [MCP Documentation](https://modelcontextprotocol.io)
- [Conversational Analytics API](https://cloud.google.com/gemini/docs/conversational-analytics-api)

## 🔒 Security Checklist

Before deploying to production:
- [ ] Use service account (not personal credentials)
- [ ] Enable SSL verification (`LOOKER_VERIFY_SSL=true`)
- [ ] Store secrets in secure vault
- [ ] Set up monitoring and logging
- [ ] Configure rate limits
- [ ] Review IAM permissions
- [ ] Test with realistic queries

## 🎯 What This Tool Does

The `looker_conversational_analytics` tool allows AI assistants to:
- Query Looker data using natural language
- Generate SQL automatically from questions
- Analyze data across multiple explores
- Create visualizations and charts
- Perform advanced statistical analysis (with Python mode)
- Return results in Markdown or JSON format

## 📊 Features at a Glance

✅ Natural language to SQL  
✅ Multi-explore support (up to 5)  
✅ Automatic visualization generation  
✅ Advanced Python analysis  
✅ Markdown & JSON output  
✅ Comprehensive error handling  
✅ Production-ready security  
✅ Character limit management  
✅ Timeout handling  

## 🎓 Learn More

Start with **README.md** - it contains:
- Complete prerequisites checklist
- Step-by-step setup instructions
- Usage examples and best practices
- Troubleshooting guide
- Security considerations
- API reference
- Architecture diagrams

## 📝 File Guide

| File | Purpose | Read When |
|------|---------|-----------|
| README.md | Complete documentation | First - essential reading |
| looker_conversational_analytics_mcp.py | Server implementation | When customizing or debugging |
| requirements.txt | Dependencies list | During installation |
| .env.example | Configuration template | During initial setup |
| TESTING.md | Testing guide | Before/after deployment |
| PROJECT_SUMMARY.md | Architecture overview | Understanding the system |
| looker_ca_mcp_implementation_plan.md | Development details | Deep dive into design |

---

**Ready to start?** Open README.md and follow the Prerequisites section! 🚀
