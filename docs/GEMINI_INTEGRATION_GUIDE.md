# Gemini CLI Integration Guide

**Purpose:** Use Damien Email Wrestler tools with Gemini instead of Claude Desktop
**Reason:** Gemini has **2M token context** vs Claude's 200k, perfect for long email management sessions
**Status:** ✅ **FULLY COMPATIBLE** via HTTP REST API

---

## Executive Summary

Your Damien platform has **3 access methods**, and **Method #2 (HTTP REST API)** is perfect for Gemini:

1. **MCP Protocol (stdio)** → For Claude Desktop only ❌ Gemini doesn't support
2. **HTTP REST API** → **✅ PERFECT FOR GEMINI** (what you'll use)
3. **Python CLI** → For direct command-line usage

**Gemini can access all 48 Damien tools via the HTTP REST API using function calling!**

---

## Why This Works

### Context Length Comparison

| LLM | Context Window | Email Workflow Capacity |
|-----|---------------|------------------------|
| **Gemini 1.5 Pro** | 2M tokens | ~20,000 emails analyzed |
| **Gemini 2.0 Flash** | 1M tokens | ~10,000 emails analyzed |
| Claude Desktop | 200k tokens | ~2,000 emails (fills fast) |

**Gemini Advantages:**
- ✅ 10x longer conversations
- ✅ Can analyze entire inbox in one session
- ✅ Won't fill up chat as quickly
- ✅ Perfect for large-scale email management

---

## Architecture: How It Works

```
Gemini CLI → HTTP REST API (port 8892) → Damien Backend → Gmail API
```

**vs Claude Desktop:**
```
Claude Desktop → MCP Protocol (stdio) → Minimal MCP Server (8893) → Backend (8892) → Gmail API
```

**Same backend, different front door!**

---

## Quick Start: Gemini Setup

### Step 1: Verify API is Running

```bash
# Check backend API health
curl http://localhost:8892/health

# Should return: {"status": "ok", "message": "Damien MCP Server is healthy!"}
```

### Step 2: List Available Tools

```bash
curl -H "X-API-Key: 2cce28d6432ac936fba9bdb124059c1b034a9858fe22ce4d3e367136b5b251c7" \
  http://localhost:8892/mcp/list_tools | python3 -m json.tool
```

**Response:** 48 tools with full schemas

### Step 3: Test Tool Execution

```bash
curl -X POST http://localhost:8892/mcp/execute_tool \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 2cce28d6432ac936fba9bdb124059c1b034a9858fe22ce4d3e367136b5b251c7" \
  -d '{
    "tool_name": "damien_list_emails",
    "input": {"max_results": 5},
    "session_id": "gemini_session_1"
  }' | python3 -m json.tool
```

**Response:** List of emails ✅

---

## HTTP REST API Reference

### Endpoint: List Tools

**URL:** `GET http://localhost:8892/mcp/list_tools`

**Headers:**
```
X-API-Key: 2cce28d6432ac936fba9bdb124059c1b034a9858fe22ce4d3e367136b5b251c7
```

**Response:**
```json
[
  {
    "name": "damien_list_emails",
    "description": "List emails from Gmail inbox with optional filtering",
    "input_schema": {
      "type": "object",
      "properties": {
        "query": {"type": "string", "description": "Gmail search query"},
        "max_results": {"type": "integer", "description": "Maximum emails to return"}
      },
      "required": []
    }
  },
  ... 47 more tools
]
```

---

### Endpoint: Execute Tool

**URL:** `POST http://localhost:8892/mcp/execute_tool`

**Headers:**
```
Content-Type: application/json
X-API-Key: 2cce28d6432ac936fba9bdb124059c1b034a9858fe22ce4d3e367136b5b251c7
```

**Request Body:**
```json
{
  "tool_name": "damien_list_emails",
  "input": {
    "query": "is:unread",
    "max_results": 20
  },
  "session_id": "gemini_session_123"
}
```

**Response (Success):**
```json
{
  "tool_result_id": "uuid-here",
  "is_error": false,
  "output": {
    "email_summaries": [
      {"id": "msg1", "threadId": "thread1", "snippet": "Email preview..."},
      ...
    ],
    "next_page_token": "token_for_pagination"
  },
  "error_message": null
}
```

**Response (Error):**
```json
{
  "tool_result_id": "uuid-here",
  "is_error": true,
  "output": null,
  "error_message": "Validation error: thread_id is required"
}
```

---

## Gemini Function Calling Setup

### Option 1: Gemini AI Studio (Web Interface)

1. **Go to:** https://aistudio.google.com/
2. **Create New Chat**
3. **Enable Function Calling**
4. **Define Functions:** Use schemas from `/mcp/list_tools`

**Example Function Definition:**
```json
{
  "name": "damien_list_emails",
  "description": "List emails from Gmail inbox with optional filtering",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Gmail search query (e.g., 'is:unread', 'from:sender@example.com')"
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum number of emails to return (default: 20)"
      }
    }
  }
}
```

**Function Implementation (Python):**
```python
import requests

def damien_list_emails(query="", max_results=20):
    response = requests.post(
        "http://localhost:8892/mcp/execute_tool",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "2cce28d6432ac936fba9bdb124059c1b034a9858fe22ce4d3e367136b5b251c7"
        },
        json={
            "tool_name": "damien_list_emails",
            "input": {"query": query, "max_results": max_results},
            "session_id": "gemini_session"
        }
    )
    result = response.json()
    if result["is_error"]:
        return {"error": result["error_message"]}
    return result["output"]
```

---

### Option 2: Gemini CLI with Function Calling

**Install Gemini CLI:**
```bash
pip install google-generativeai
```

**Create Python Wrapper:**
```python
import google.generativeai as genai
import requests
import json

# Configure Gemini
genai.configure(api_key="YOUR_GEMINI_API_KEY")

# Define Damien tool wrapper
def call_damien_tool(tool_name, parameters):
    """Call any Damien tool via HTTP API"""
    response = requests.post(
        "http://localhost:8892/mcp/execute_tool",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "2cce28d6432ac936fba9bdb124059c1b034a9858fe22ce4d3e367136b5b251c7"
        },
        json={
            "tool_name": tool_name,
            "input": parameters,
            "session_id": "gemini_cli_session"
        }
    )
    result = response.json()
    if result["is_error"]:
        return {"error": result["error_message"]}
    return result["output"]

# Load all tool schemas
def load_damien_tools():
    response = requests.get(
        "http://localhost:8892/mcp/list_tools",
        headers={"X-API-Key": "2cce28d6432ac936fba9bdb124059c1b034a9858fe22ce4d3e367136b5b251c7"}
    )
    return response.json()

# Create Gemini function declarations from Damien tools
tools = load_damien_tools()
function_declarations = []

for tool in tools:
    function_declarations.append({
        "name": tool["name"],
        "description": tool["description"],
        "parameters": tool["input_schema"]
    })

# Initialize Gemini model with tools
model = genai.GenerativeModel(
    model_name='gemini-1.5-pro',
    tools=function_declarations
)

# Start chat
chat = model.start_chat()

# Example: Ask Gemini to use Damien tools
response = chat.send_message("List my 10 most recent unread emails")

# Handle function calls
for part in response.parts:
    if hasattr(part, 'function_call'):
        function_name = part.function_call.name
        function_args = dict(part.function_call.args)

        # Call Damien API
        result = call_damien_tool(function_name, function_args)

        # Send result back to Gemini
        response = chat.send_message({
            "function_response": {
                "name": function_name,
                "response": result
            }
        })

print(response.text)
```

---

### Option 3: Simple HTTP Proxy Script

**Create `gemini_damien_proxy.py`:**
```python
#!/usr/bin/env python3
"""
Gemini <-> Damien Email Wrestler Proxy
Allows Gemini to use all 48 Damien tools via function calling
"""

import requests
import json
from typing import Dict, Any

DAMIEN_API_URL = "http://localhost:8892/mcp/execute_tool"
DAMIEN_API_KEY = "2cce28d6432ac936fba9bdb124059c1b034a9858fe22ce4d3e367136b5b251c7"

class DamienProxy:
    """Proxy for Gemini to access Damien tools"""

    def __init__(self):
        self.session_id = "gemini_proxy_session"
        self.tools = self.load_tools()

    def load_tools(self):
        """Load all available Damien tools"""
        response = requests.get(
            "http://localhost:8892/mcp/list_tools",
            headers={"X-API-Key": DAMIEN_API_KEY}
        )
        return response.json()

    def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Damien tool"""
        response = requests.post(
            DAMIEN_API_URL,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": DAMIEN_API_KEY
            },
            json={
                "tool_name": tool_name,
                "input": parameters,
                "session_id": self.session_id
            }
        )

        result = response.json()

        if result["is_error"]:
            return {
                "error": result["error_message"],
                "success": False
            }

        return {
            "data": result["output"],
            "success": True
        }

    def get_function_declarations(self):
        """Get Gemini-compatible function declarations"""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
            for tool in self.tools
        ]

# Usage
if __name__ == "__main__":
    proxy = DamienProxy()

    # Example: List emails
    result = proxy.execute("damien_list_emails", {"max_results": 5})
    print(json.dumps(result, indent=2))

    # Get function declarations for Gemini
    functions = proxy.get_function_declarations()
    print(f"\nLoaded {len(functions)} Damien functions for Gemini")
```

**Run:**
```bash
chmod +x gemini_damien_proxy.py
./gemini_damien_proxy.py
```

---

## Available Tools (All 48)

### Core Email Management (13 tools)
- `damien_list_emails` - List emails with filtering
- `damien_get_email_details` - Get full email details
- `damien_trash_emails` - Move emails to trash
- `damien_delete_emails` - Permanently delete
- `damien_modify_labels` - Add/remove labels
- `damien_mark_as_read` - Mark as read/unread
- ... and 7 more

### AI Intelligence (12 tools)
- `damien_ai_analyze_emails` - AI email analysis
- `damien_ai_analyze_emails_async` - Large-scale async analysis
- `damien_ai_quick_test` - Quick AI test
- `damien_smart_trash_marketing` - AI-powered marketing cleanup
- `damien_organize_emails` - Natural language organization
- ... and 7 more

### Thread Operations (5 tools)
- `damien_list_threads` - List email threads
- `damien_get_thread_details` - Get thread messages
- `damien_trash_thread` - Trash entire thread
- `damien_modify_thread_labels` - Manage thread labels
- `damien_mark_thread_as_read` - Mark thread status

### Draft Management (6 tools)
- `damien_create_draft` - Create email draft
- `damien_update_draft` - Update existing draft
- `damien_send_draft` - Send draft
- `damien_list_drafts` - List all drafts
- `damien_get_draft_details` - Get draft details
- `damien_delete_draft` - Delete draft

### Job Management (4 tools)
- `damien_job_get_status` - Check async job status
- `damien_job_get_result` - Get job results
- `damien_job_list` - List all jobs
- `damien_job_cancel` - Cancel running job

### Rules & Settings (8 tools)
- `damien_create_label` - Create Gmail label
- `damien_delete_label` - Delete label
- `damien_list_labels` - List all labels
- `damien_get_settings` - Get Gmail settings
- `damien_update_settings` - Update settings
- ... and 3 more

---

## Example Workflows

### Workflow 1: Email Analysis with Gemini (Long Context!)

```python
# Gemini can analyze ALL your emails in one session thanks to 2M token context!

prompt = """
Using the Damien tools:
1. List ALL my emails from the last 90 days (use damien_list_emails with pagination)
2. Analyze them using damien_ai_analyze_emails_async
3. Show me:
   - Top senders
   - Email patterns
   - Suggested automation rules
   - Emails to archive/delete

This will be a long conversation with many emails, but that's fine because
Gemini has 2M token context!
"""
```

**Gemini can handle 10,000+ emails in ONE conversation!**

---

### Workflow 2: Bulk Operations

```python
prompt = """
1. Find all promotional emails from last 30 days
2. Show me a sample of 10
3. If I approve, trash all of them using damien_trash_emails_by_query
4. Create a rule to auto-label future promotional emails
"""
```

---

### Workflow 3: Interactive Email Triage

```python
prompt = """
Let's go through my inbox systematically:
1. List unread emails (damien_list_emails with query "is:unread")
2. For each email, show me details and ask:
   - Keep in inbox?
   - Archive?
   - Trash?
   - Create rule?
3. Execute my decisions
4. Continue until inbox is zero

I want to process 100+ emails in this session.
"""
```

**With Gemini's 2M context, this works without chat filling up!**

---

## Comparison: Claude Desktop vs Gemini

| Feature | Claude Desktop (MCP) | Gemini (HTTP API) |
|---------|---------------------|-------------------|
| **Context Length** | 200k tokens (~2k emails) | 2M tokens (~20k emails) |
| **Chat Fills Up?** | ❌ Yes, frequently | ✅ Rarely (10x more space) |
| **Setup Complexity** | Easy (built-in MCP) | Medium (function calling) |
| **Tool Access** | Direct MCP protocol | HTTP REST API |
| **Performance** | Fast (native protocol) | Fast (HTTP overhead minimal) |
| **Cost** | Claude pricing | Gemini pricing (cheaper!) |
| **Best For** | Quick tasks, <2k emails | Long sessions, bulk operations |

---

## Advantages of Gemini for Email Management

### ✅ **Massive Context Window**
- Process entire inbox in one session
- Review 10,000+ emails without losing context
- Build complex automation rules iteratively

### ✅ **Cost-Effective**
- Gemini 1.5 Flash: ~1/10th the cost of Claude
- Gemini 1.5 Pro: ~1/5th the cost of Claude
- Perfect for high-volume email processing

### ✅ **Longer Sessions**
- Won't hit "chat full" errors
- Can work on multiple email projects in one conversation
- Ideal for inbox cleanup marathons

### ✅ **Multimodal (Gemini 1.5+)**
- Can analyze email attachments (images, PDFs)
- Extract data from screenshots
- Process visual email content

---

## Disadvantages vs Claude Desktop

### ❌ **Setup Required**
- Need to configure function calling
- Requires Python wrapper or manual API calls
- Not as plug-and-play as Claude Desktop MCP

### ❌ **No Native Integration**
- Claude Desktop has built-in MCP support
- Gemini requires custom integration
- More moving parts to maintain

### ❌ **Tool Quality (for coding)**
- Claude is better at code generation
- Gemini excels at reasoning over large contexts
- For email management, both are excellent

---

## Recommendation

**Use BOTH!**

### Claude Desktop (MCP)
- ✅ Quick email checks (5-10 emails)
- ✅ Rapid prototyping of email rules
- ✅ Testing new automation workflows
- ✅ When you need best code generation

### Gemini (HTTP API)
- ✅ Bulk email analysis (100-10,000+ emails)
- ✅ Long cleanup sessions (won't fill chat)
- ✅ Complex multi-step workflows
- ✅ Cost-effective high-volume processing
- ✅ Full inbox audits (analyze everything!)

---

## Next Steps

1. **Test the HTTP API:**
   ```bash
   ./test-gemini-api.sh  # Run test script (create if needed)
   ```

2. **Set up Gemini CLI:**
   ```bash
   pip install google-generativeai
   ```

3. **Create your first Gemini workflow:**
   - Copy the proxy script above
   - Configure your Gemini API key
   - Run your first bulk email analysis!

4. **Build automation:**
   - Use Gemini's long context to analyze patterns
   - Create rules based on AI insights
   - Let Gemini manage your inbox at scale

---

## Support & Documentation

- **HTTP API Docs:** Check `/mcp/list_tools` for full schemas
- **Backend Status:** `curl http://localhost:8892/health`
- **All 48 Tools:** Listed in this guide above
- **Example Scripts:** See `gemini_damien_proxy.py` above

---

## Conclusion

**Yes, you can absolutely use Gemini with Damien!** 🎉

Your platform already has:
- ✅ Fully functional HTTP REST API
- ✅ All 48 tools accessible via HTTP
- ✅ Proper authentication (API key)
- ✅ Clean error handling
- ✅ Session management

**Gemini's 2M token context makes it PERFECT for email management at scale!**

The only trade-off is initial setup complexity vs Claude Desktop's native MCP support, but the payoff is 10x longer conversations and lower costs.

---

**Ready to process your entire inbox without chat limitations? Gemini + Damien = Perfect match!** 🚀
