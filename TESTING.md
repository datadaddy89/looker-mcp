# Testing Guide for Looker Conversational Analytics MCP Server

## Pre-Testing Checklist

### Environment Setup
- [ ] Python 3.8+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables configured (see `.env.example`)
- [ ] Google Cloud project created with APIs enabled
- [ ] Google Cloud authentication configured (`gcloud auth application-default login`)
- [ ] Looker API credentials generated
- [ ] Access to at least one Looker model and explore

### Verify Configuration
```bash
# Test environment variables are set
echo $LOOKER_BASE_URL
echo $LOOKER_CLIENT_ID
echo $GOOGLE_CLOUD_PROJECT

# Test Google Cloud auth
gcloud auth application-default print-access-token

# Test Python can import required packages
python -c "from google.cloud import geminidataanalytics; print('✓ SDK installed')"
```

## Manual Testing

### Test 1: Server Starts Successfully
```bash
# Start the server (will hang as it waits for input)
timeout 5s python looker_conversational_analytics_mcp.py

# Expected: Server starts without errors
# Note: Use tmux or separate terminal for interactive testing
```

### Test 2: Simple Single-Explore Query

**Input:**
```json
{
  "user_query_with_context": "What is the total count of records?",
  "explore_references": [
    {"model": "your_model", "explore": "your_explore"}
  ]
}
```

**Expected Output:**
- ✓ Query executes without errors
- ✓ SQL is generated
- ✓ Results are returned
- ✓ Natural language answer provided
- ✓ Response is well-formatted (Markdown by default)

### Test 3: Multi-Explore Query

**Input:**
```json
{
  "user_query_with_context": "Compare the count of users versus the count of orders",
  "explore_references": [
    {"model": "ecommerce", "explore": "users"},
    {"model": "ecommerce", "explore": "orders"}
  ]
}
```

**Expected Output:**
- ✓ API selects relevant explores for each part
- ✓ Multiple queries generated
- ✓ Results from both explores returned
- ✓ Comparison analysis provided

### Test 4: Complex Query with Aggregations

**Input:**
```json
{
  "user_query_with_context": "What are the top 10 products by total revenue, showing revenue and order count?",
  "explore_references": [
    {"model": "ecommerce", "explore": "order_items"}
  ],
  "system_instruction": "Show revenue in USD format rounded to nearest dollar"
}
```

**Expected Output:**
- ✓ Aggregation functions used (SUM, COUNT)
- ✓ Grouping applied correctly
- ✓ Top 10 filtering works
- ✓ Results formatted per system instruction

### Test 5: Time-Series Analysis

**Input:**
```json
{
  "user_query_with_context": "Show me monthly sales trends for the past 12 months",
  "explore_references": [
    {"model": "ecommerce", "explore": "orders"}
  ]
}
```

**Expected Output:**
- ✓ Time dimension used correctly
- ✓ Data grouped by month
- ✓ 12 months of data returned
- ✓ Trend analysis included

### Test 6: Python Analysis (Advanced)

**Input:**
```json
{
  "user_query_with_context": "Calculate the average order value by customer segment and show the standard deviation",
  "explore_references": [
    {"model": "ecommerce", "explore": "orders"}
  ],
  "enable_python_analysis": true
}
```

**Expected Output:**
- ✓ Python code generated for statistical calculations
- ✓ Standard deviation calculated correctly
- ✓ Results grouped by segment
- ✓ Statistical summary provided

### Test 7: JSON Response Format

**Input:**
```json
{
  "user_query_with_context": "Top 5 categories by revenue",
  "explore_references": [
    {"model": "ecommerce", "explore": "order_items"}
  ],
  "response_format": "json"
}
```

**Expected Output:**
- ✓ Response in valid JSON format
- ✓ Structured sections: queries, results, text_responses
- ✓ Schema information included
- ✓ Easy to parse programmatically

## Error Handling Tests

### Test 8: Invalid Explore Reference
**Input:**
```json
{
  "user_query_with_context": "Count of records",
  "explore_references": [
    {"model": "nonexistent_model", "explore": "nonexistent_explore"}
  ]
}
```

**Expected Output:**
- ✓ Clear error message about invalid explore
- ✓ Suggestions for correct format
- ✓ No server crash

### Test 9: Empty Query
**Input:**
```json
{
  "user_query_with_context": "",
  "explore_references": [
    {"model": "ecommerce", "explore": "orders"}
  ]
}
```

**Expected Output:**
- ✓ Validation error caught
- ✓ Message: "Query cannot be empty"
- ✓ Request rejected before API call

### Test 10: Too Many Explores
**Input:**
```json
{
  "user_query_with_context": "Analyze everything",
  "explore_references": [
    {"model": "m1", "explore": "e1"},
    {"model": "m2", "explore": "e2"},
    {"model": "m3", "explore": "e3"},
    {"model": "m4", "explore": "e4"},
    {"model": "m5", "explore": "e5"},
    {"model": "m6", "explore": "e6"}
  ]
}
```

**Expected Output:**
- ✓ Validation error caught
- ✓ Message about 5 explore limit
- ✓ Request rejected before API call

### Test 11: Authentication Failure
**Setup:** Temporarily set invalid Looker credentials

**Expected Output:**
- ✓ Clear authentication error message
- ✓ Guidance on fixing credentials
- ✓ Server continues running

### Test 12: API Quota Exceeded
**Setup:** Make many requests rapidly (if you have low quota)

**Expected Output:**
- ✓ Quota error caught
- ✓ Message suggests waiting/retry
- ✓ Server recovers gracefully

## Performance Tests

### Test 13: Response Time - Simple Query
**Measure:** Time from request to first response

**Target:** < 10 seconds for simple queries

### Test 14: Response Time - Complex Query
**Measure:** Time for multi-step analysis

**Target:** < 30 seconds without Python, < 60 seconds with Python

### Test 15: Large Result Sets
**Input:** Query that returns 1000+ rows

**Expected:**
- ✓ Results truncated to respect character limit
- ✓ Truncation message displayed
- ✓ Suggestion to add filters

### Test 16: Concurrent Requests
**Setup:** Multiple queries in parallel (if applicable)

**Expected:**
- ✓ All requests complete successfully
- ✓ No race conditions
- ✓ Proper resource cleanup

## Integration Tests

### Test 17: Claude Desktop Integration
**Setup:**
1. Add server to Claude Desktop config
2. Restart Claude Desktop
3. Verify tool appears in Claude

**Test Query:** "Use the Looker tool to show me top products by revenue"

**Expected:**
- ✓ Tool executes successfully
- ✓ Results displayed in Claude
- ✓ Follow-up queries work

### Test 18: Multi-Turn Conversation
**Query 1:** "What are the top 10 products by revenue?"

**Query 2:** "Show me a breakdown by category for those products"

**Expected:**
- ✓ Second query builds on first
- ✓ Context maintained appropriately
- ✓ Results are relevant

## Example Test Queries by Use Case

### Sales Analysis
```
"What were total sales last month compared to the previous month? Show the percentage change."

"Which sales representatives had the highest win rate in Q4 2024?"

"Show me the sales pipeline by stage and predicted close date"
```

### Customer Analytics
```
"What is the average customer lifetime value by acquisition channel?"

"Which customer segments have the highest retention rate?"

"Show me the cohort analysis for customers acquired in each month of 2024"
```

### Product Performance
```
"What are the top 5 products by revenue margin?"

"Which products have the highest return rate and why?"

"Compare product sales across different regions"
```

### Operational Metrics
```
"What is the average order fulfillment time by shipping method?"

"Show me inventory turnover rates by product category"

"Which warehouses have the highest error rates?"
```

## Quality Checklist

After all tests, verify:

- [ ] All environment variables properly validated
- [ ] Google Cloud authentication works correctly
- [ ] Looker credentials validated on first use
- [ ] Input validation catches all invalid inputs
- [ ] Error messages are clear and actionable
- [ ] Both Markdown and JSON formats work
- [ ] Character limits respected
- [ ] Timeout handling works correctly
- [ ] Tool annotations are accurate
- [ ] Documentation is comprehensive
- [ ] Example queries in README work
- [ ] No sensitive data logged
- [ ] Credentials handled securely

## Common Issues and Solutions

### Issue: "Module not found: geminidataanalytics"
**Solution:**
```bash
pip install google-cloud-geminidataanalytics --break-system-packages
```

### Issue: "Default credentials not found"
**Solution:**
```bash
gcloud auth application-default login
```

### Issue: "403: Permission Denied"
**Solution:**
```bash
# Check IAM permissions
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT

# Add required role
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="user:your-email@example.com" \
  --role="roles/geminidataanalytics.user"
```

### Issue: "Explore not found"
**Solution:**
- Verify model and explore names in Looker
- Check user has access to the explore
- Ensure correct capitalization

### Issue: "Timeout after 300 seconds"
**Solution:**
- Simplify the query
- Add filters to reduce data volume
- Check Looker instance performance
- Consider breaking into smaller queries

## Automated Testing Script

For convenience, here's a test script you can run:

```bash
#!/bin/bash
# test_looker_ca_mcp.sh

echo "Testing Looker Conversational Analytics MCP Server..."

# Check environment
echo "1. Checking environment variables..."
if [ -z "$LOOKER_BASE_URL" ]; then
    echo "❌ LOOKER_BASE_URL not set"
    exit 1
fi
echo "✓ Environment configured"

# Check dependencies
echo "2. Checking dependencies..."
python -c "from google.cloud import geminidataanalytics" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ geminidataanalytics not installed"
    exit 1
fi
echo "✓ Dependencies installed"

# Check Google Cloud auth
echo "3. Checking Google Cloud authentication..."
gcloud auth application-default print-access-token > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Google Cloud authentication failed"
    exit 1
fi
echo "✓ Google Cloud authenticated"

# Syntax check
echo "4. Checking Python syntax..."
python -m py_compile looker_conversational_analytics_mcp.py
if [ $? -ne 0 ]; then
    echo "❌ Python syntax errors"
    exit 1
fi
echo "✓ Python syntax valid"

echo ""
echo "✅ All pre-tests passed! Server is ready to use."
echo ""
echo "To test the server:"
echo "1. Start the server: python looker_conversational_analytics_mcp.py"
echo "2. Connect from Claude Desktop or other MCP client"
echo "3. Run test queries from this guide"
```

## Next Steps After Testing

1. **Document Test Results**: Record which tests passed/failed
2. **File Issues**: Create issues for any failures
3. **Performance Tuning**: Optimize slow queries
4. **Production Prep**: 
   - Enable SSL verification
   - Use service accounts
   - Set up monitoring
   - Configure rate limits
5. **User Documentation**: Create user guides with examples
6. **Deployment**: Deploy to production environment
