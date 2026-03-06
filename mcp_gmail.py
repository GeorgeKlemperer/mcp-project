# MCP Server Entry Point

import os
from mcp.server.fastmcp import FastMCP
from tools.google import GmailTool, RAGTool

work_dir = os.path.dirname(__file__)
gmail_tool = GmailTool(client_secret_file=os.path.join(work_dir, 'client-secret.json'))
rag_tool = RAGTool()

mcp = FastMCP(
  'Gmail',
  dependencies=[
    'google-api-python-client',
    'google-auth-httplib2',
    'google-auth-oauthlib',
    'openai',
    'chromadb'
  ],
)

# Gmail tools
mcp.add_tool(gmail_tool.get_email_message_details, name='Gmail-Get-Email-Message-Details', description='Get details of an email message in Gmail')
mcp.add_tool(gmail_tool.get_email_message_body, name='Gmail-Get-Email-Message-Body', description='Get the body of an email message (Gmail)')
mcp.add_tool(gmail_tool.search_emails, name='Gmail-Search-Emails', description='Search or return emails in Gmail. Defualt is None, which returns all emails.')
mcp.add_tool(gmail_tool.get_unread_emails, name='Gmail-Get-Unread-Emails', description='Get unread emails from Gmail inbox')
mcp.add_tool(gmail_tool.create_draft_reply, name='Gmail-Create-Draft-Reply', description='Create a draft reply to an email thread in Gmail')

# RAG tools
mcp.add_tool(rag_tool.query_documents, name='RAG-Query-Documents', description='Query the knowledge base documents for information')
mcp.add_tool(rag_tool.refresh_documents, name='RAG-Refresh-Documents', description='Re-ingest all documents from the rag-documents folder')

if __name__ == '__main__': # Stops MCP running on import
    mcp.run()