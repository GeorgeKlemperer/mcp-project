# Gmail MCP Server

An MCP (Model Context Protocol) server that allows AI assistants to read Gmail emails and create draft replies.

## Features

- 🔍 **Search emails** by query, label, or get all emails
- 📧 **Get unread emails** from inbox
- 📄 **Get email details** including sender, subject, body, and thread ID
- ✍️ **Create draft replies** that are properly threaded to original emails
- 🔒 **Secure OAuth 2.0** authentication with Gmail API

## Prerequisites

- Python 3.11+
- Gmail account
- Google Cloud Console project with Gmail API enabled
- Claude Desktop (for testing with AI assistant)

## Setup Instructions

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file and save it as `client-secret.json` in the project root

### 2. Project Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd mcp-project

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
or
pip install -U mcp 'mcp[cli]' google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 3. Authentication

Run the initial authentication setup:

```bash
ALLOW_INTERACTIVE_OAUTH=1 .venv/bin/python mcp_gmail.py
```

This will:
- Open your browser for Gmail OAuth consent
- Save authentication tokens locally
- Allow the MCP server to access Gmail without browser popups

### 4. Claude Desktop Configuration

My Claude Desktop configuration file (Claude/claude_desktop_config.json):

```
{
  "mcpServers": {
    "Gmail": {
      "command": "/Users/georgeklemperer/se-projects/mcp-project/.venv/bin/python",
      "args": ["/Users/georgeklemperer/se-projects/mcp-project/mcp_gmail.py"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```

**Note:** Update the paths to match your actual project location.

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `Gmail-Search-Emails` | Search emails by query/label | `query`, `label`, `max_results`, `next_page_token` |
| `Gmail-Get-Unread-Emails` | Get unread emails from inbox | `max_results` |
| `Gmail-Get-Email-Message-Details` | Get email details by message ID | `msg_id` |
| `Gmail-Get-Email-Message-Body` | Get full email body content | `msg_id` |
| `Gmail-Create-Draft-Reply` | Create threaded draft reply | `thread_id`, `reply_body`, `body_type` |

## Screenshots of MCP working with Claude Desktop to read emails and draft replies

<img width="800" alt="image" style="margin-bottom: 16px;" src="https://github.com/user-attachments/assets/e0f7b91a-7162-447b-83f1-2811a87ccba6" />
<img width="800" alt="image" src="https://github.com/user-attachments/assets/edb9f1e9-cf36-4c75-a1cd-8d2aa7712287" />
<img width="800" alt="image" src="https://github.com/user-attachments/assets/4ec601d3-fb73-4b4c-b147-d86a41d82603" />
<img width="800" alt="image" src="https://github.com/user-attachments/assets/eaed7475-e585-4df8-9e12-b55d2ccb1bba" />
<img width="800" alt="image" src="https://github.com/user-attachments/assets/c8dc2ba1-9dce-4bb2-9b46-100f6fdf9a5e" />

### Security & Permissions

- **Read-only access** to Gmail messages (`gmail.readonly` scope)
- **Draft creation only** (`gmail.compose` scope - cannot send emails)
- **Local token storage** in `token-files/` directory
- **No email sending capability** - drafts must be sent manually from Gmail

## File Structure

```
mcp-project/
├── tools/
│   └── google/
│       ├── __init__.py
│       ├── gmail_tools.py      # Gmail API wrapper
│       └── google_apis.py      # OAuth & service creation
├── mcp_gmail.py               # MCP server entry point
├── requirements.txt          # Python dependencies
└── README.md
```

## Dependencies

```txt
mcp
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
pydantic
```