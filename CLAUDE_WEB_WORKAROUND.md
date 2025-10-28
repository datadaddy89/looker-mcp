# Using Looker MCP Server with Claude Web App - Workarounds

## The Situation

**Claude's web app (claude.ai) does NOT support custom MCP servers or custom connectors.**

### Platform Comparison

| Feature | Claude Desktop | Claude Web App |
|---------|---------------|----------------|
| MCP Protocol | ✅ Full Support | ❌ Not Available |
| Custom Servers | ✅ Via Config File | ❌ No API |
| Your Looker MCP | ✅ Works Perfectly | ❌ Cannot Connect |
| Built-in Tools | Limited | Some integrations |

**Why?** Claude web runs in a browser sandbox and cannot execute local processes or connect to custom MCP servers for security reasons.

---

## Recommended Solutions

### ⭐ Option 1: Use Claude Desktop (Best Option)

**This is the intended way to use MCP servers with Claude.**

1. **Download Claude Desktop**:
   - Mac: [Download from Anthropic](https://claude.ai/download)
   - Windows: Available in the Claude app

2. **Configure MCP**:
   - Follow [CLAUDE_DESKTOP_SETUP.md](CLAUDE_DESKTOP_SETUP.md)
   - Add your Looker server to config file
   - Restart Claude Desktop

3. **Start using**:
   ```
   Query Looker: What are the top 10 products by revenue?
   ```

**Advantages**:
- ✅ Native MCP support
- ✅ Direct connection to your server
- ✅ No additional infrastructure needed
- ✅ Works offline (for local execution)
- ✅ Best performance

---

### Option 2: Build a Custom Web Interface

Since Claude web doesn't support custom connectors, build your own interface that combines:
1. Your Looker API (Cloud Run deployment)
2. Claude API for AI responses

#### Architecture

```
┌─────────────────┐
│   Your Web UI   │
│  (React/Next.js)│
└────┬────────┬───┘
     │        │
     │        └─────────────┐
     │                      │
     v                      v
┌──────────────┐    ┌──────────────┐
│  Looker MCP  │    │  Claude API  │
│  (Cloud Run) │    │  (Anthropic) │
└──────────────┘    └──────────────┘
```

#### Implementation Example

**Frontend (Next.js/React)**:

```typescript
// app/api/query/route.ts
import Anthropic from "@anthropic-ai/sdk";

export async function POST(req: Request) {
  const { userQuery } = await req.json();

  // Step 1: Call your Looker API
  const lookerResponse = await fetch('https://your-cloud-run-url/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_query_with_context: userQuery,
      explore_references: [
        { model: "ecommerce", explore: "order_items" }
      ],
      response_format: "json"
    })
  });

  const lookerData = await lookerResponse.json();

  // Step 2: Send to Claude for analysis
  const anthropic = new Anthropic({
    apiKey: process.env.CLAUDE_API_KEY,
  });

  const message = await anthropic.messages.create({
    model: "claude-3-5-sonnet-20241022",
    max_tokens: 1024,
    messages: [{
      role: "user",
      content: `Here's data from Looker: ${JSON.stringify(lookerData)}.
                Please analyze and explain: ${userQuery}`
    }]
  });

  return Response.json({
    lookerData,
    claudeAnalysis: message.content
  });
}
```

**Frontend Component**:

```typescript
// components/LookerQuery.tsx
'use client';

import { useState } from 'react';

export function LookerQuery() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleQuery = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userQuery: query })
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Query failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask about your Looker data..."
      />
      <button onClick={handleQuery} disabled={loading}>
        {loading ? 'Querying...' : 'Query'}
      </button>

      {result && (
        <div>
          <h3>Looker Data:</h3>
          <pre>{JSON.stringify(result.lookerData, null, 2)}</pre>

          <h3>Claude's Analysis:</h3>
          <div>{result.claudeAnalysis}</div>
        </div>
      )}
    </div>
  );
}
```

**Deploy to Vercel/Netlify**:

```bash
# Deploy your custom interface
vercel deploy
# or
netlify deploy
```

**Cost**: ~$20/month (Claude API) + Cloud Run costs

---

### Option 3: Use Slack with Claude Integration

If your team uses Slack, you can:

1. **Add Claude to Slack** (official integration)
2. **Create a Slack bot** that:
   - Listens for queries
   - Calls your Looker Cloud Run API
   - Formats results
   - Sends to Claude in Slack

**Limitation**: Claude in Slack also doesn't support custom MCP servers, so you'd still need to call your API separately.

---

### Option 4: Wait for Claude Web MCP Support

**Anthropic may add MCP support to Claude web in the future**, but there's no official timeline.

**Current Status**:
- ❌ Not available
- ❓ No announced plans
- 💡 Feature request: Could be submitted to Anthropic

---

## Comparison Matrix

| Solution | Complexity | Cost | MCP Support | Best For |
|----------|-----------|------|-------------|----------|
| **Claude Desktop** | Low | $20/mo | ✅ Native | Personal use |
| **Custom Web UI** | High | $20-50/mo | ⚠️ Manual | Custom needs |
| **ChatGPT Custom GPT** | Low | $20-50/mo | ❌ HTTP only | Team sharing |
| **Slack Bot** | Medium | Variable | ⚠️ Workaround | Slack teams |

---

## Recommendation

### For Individual Users
**Use Claude Desktop** - It's specifically designed for this use case and provides the best experience.

### For Teams
**Choose based on needs**:
- If using Claude → Build custom web interface
- If using ChatGPT → Use Custom GPT (easier)
- If using Slack → Build Slack bot integration

### Why Not Claude Web?
The platform limitation isn't a flaw - it's by design for security:
- Web apps run in sandboxes
- Cannot execute arbitrary code
- Cannot connect to local processes
- Cannot access MCP protocol

**Claude Desktop exists specifically to provide MCP support.**

---

## Future Possibilities

### Anthropic Could Add:
1. **Web-based MCP support** via OAuth/webhooks
2. **Custom integrations API** for web app
3. **Plugin marketplace** similar to ChatGPT

### What You Can Do Now:
1. ✅ Use Claude Desktop for MCP
2. ✅ Use Cloud Run API for web access
3. ✅ Build custom interfaces as needed
4. 📧 Request the feature from Anthropic

---

## Getting Started Today

### Immediate Action (5 minutes):
1. Download Claude Desktop
2. Configure your Looker MCP server
3. Start querying!

### Custom Solution (1-2 days):
1. Deploy to Cloud Run (done ✅)
2. Build simple web interface
3. Integrate Claude API
4. Deploy your custom app

---

## Resources

- [Claude Desktop Setup](CLAUDE_DESKTOP_SETUP.md)
- [Cloud Run Deployment](CLOUD_RUN_DEPLOYMENT.md)
- [ChatGPT Alternative](CHATGPT_SETUP.md)
- [Architecture Docs](ARCHITECTURE.md)
- [Claude API Docs](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Anthropic Discord](https://discord.gg/anthropic) - Ask about future web MCP support

---

## Summary

**Bottom Line**:
- ❌ Claude web app doesn't support custom MCP servers (by design)
- ✅ Claude Desktop is the official way to use MCP
- 🔧 Custom solutions are possible but require development
- 💡 Use the tool that fits your needs (Claude Desktop, ChatGPT, or custom)

The good news: You already have all the pieces needed - just use Claude Desktop for the best experience! 🚀
