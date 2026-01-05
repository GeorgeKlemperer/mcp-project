import os
import base64
from typing import Literal, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pydantic import BaseModel, Field
from .google_apis import create_service

class EmailMessage(BaseModel):
    msg_id: str = Field(..., description="The ID of the email message.")
    subject: str = Field(..., description="The subject of the email message.")
    sender: str = Field(..., description="The sender of the email message.")
    recipients: str = Field(..., description="The recipients of the email message.")
    body: str = Field(..., description="The body of the email message.")
    snippet: str = Field(..., description="A snippet of the email message.")
    has_attachments: bool = Field(..., description="Indicates if the email has attachments.")
    date: str = Field(..., description="The date when the email was sent.")
    star: bool = Field(..., description="Indicates if the email is starred.")
    label: str = Field(..., description="Labels associated with the email message.")

class EmailMessages(BaseModel):
    count: int = Field(..., description="The number of email messages.")
    messages: list[EmailMessage] = Field(..., description="List of email messages.")
    next_page_token: str | None = Field(..., description="Token for the next page of results.")
    
class GmailTool:
    API_NAME = 'gmail'
    API_VERSION = 'v1'
    SCOPES = [
      'https://www.googleapis.com/auth/gmail.readonly',
      'https://www.googleapis.com/auth/gmail.compose'
    ]
    
    def __init__(self, client_secret_file: str) -> None:
      self.client_secret_file = client_secret_file
      self._init_service()
      
    def _init_service(self) -> None:
      """
      Initialize the Gmail API service.
      """
      
      # Manual login command to allow non-interactive OAuth:
      # ALLOW_INTERACTIVE_OAUTH=1 .venv/bin/python mcp_gmail.py
      allow_interactive = os.getenv("ALLOW_INTERACTIVE_OAUTH", "0") == "1"

      self.service = create_service(
          self.client_secret_file,
          self.API_NAME,
          self.API_VERSION,
          self.SCOPES,
          allow_interactive=allow_interactive,
      )

    def search_emails(
        self,
        query: Optional[str] = None,
        label: Literal['ALL', 'INBOX', 'SENT', 'DRAFT', 'SPAM', 'TRASH'] = 'INBOX',
        max_results: Optional[int] = 10,
        next_page_token: Optional[str] = None
      ):
        """
        Search for emails in the user's mailbox using the Gmail API.

        Args:
          query (str): Search query string. Default is None, which returns all emails.
          labels (str): Labels to filter the search results. Default is 'INBOX'.
            Available labels include: 'INBOX', 'SENT', 'DRAFT', 'SPAM', 'TRASH'.
          max_results (int): Maximum number of messages to return. The maximum allowed is 500.
        """
        messages = []
        next_page_token_ = next_page_token

        if label == 'ALL':
          label_ = None
        else:
          label_ = [label]

        while True:
          result = self.service.users().messages().list(
            userId='me',
            q=query,
            labelIds=label_,
            maxResults=min(500, max_results - len(messages)) if max_results else 500,
            pageToken=next_page_token_
          ).execute()

          messages.extend(result.get('messages', []))

          next_page_token_ = result.get('nextPageToken')
          if not next_page_token_ or (max_results and len(messages) >= max_results):
            break

        # compile emails details
        email_messages = []
        for message in messages:
          msg_id = message['id']
          msg_details = self.get_email_message_details(msg_id)
          email_messages.append(msg_details)

        email_messages_ = email_messages[:max_results] if max_results else email_messages

        return EmailMessages(
          count=len(email_messages_),
          messages=email_messages_,
          next_page_token=next_page_token_
        )

    def get_email_message_details(
        self,
        msg_id: str
      ) -> EmailMessage:
        message = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        payload = message['payload']
        headers = payload.get('headers', [])

        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), None)
        if not subject:
          subject = message.get('subject', 'No subject')

        sender = next((header['value'] for header in headers if header['name'] == 'From'), 'No sender')
        recipients = next((header['value'] for header in headers if header['name'] == 'To'), 'No recipients')
        snippet = message.get('snippet', 'No snippet')
        has_attachments = any(part.get('filename') for part in payload.get('parts', []) if part.get('filename'))
        date = next((header['value'] for header in headers if header['name'] == 'Date'), 'No date')
        star = message.get('labelIds', []).count('STARRED') > 0
        label = ', '.join(message.get('labelIds', []))

        # Add thread_id to the body field or create a new field
        thread_id = message.get('threadId', 'No thread ID')
        body = f'<not included> | Thread ID: {thread_id}'
        
        return EmailMessage(
          msg_id=msg_id,
          subject=subject,
          sender=sender,
          recipients=recipients,
          body=body,
          snippet=snippet,
          has_attachments=has_attachments,
          date=date,
          star=star,
          label=label
        )

    def get_email_message_body(
        self,
        msg_id: str
      ) -> str:
        """
        Get the body of an email message using its ID.

        Args:
          msg_id (str): The ID of the email message.

        Returns:
          str: The body of the email message.
        """
        message = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        payload = message['payload']
        return self._extract_body(payload)

    def _extract_body(
        self,
        payload: dict
      ) -> str:
        """
        Extract the email body from the payload.

        Args:
          payload (dict): The payload of the email message.

        Returns:
          str: The extracted email body.
        """
        body = '<Text body not available>'
        if 'parts' in payload:
          for part in payload['parts']:
            if part['mimeType'] == 'multipart/alternative':
              for subpart in part['parts']:
                if subpart['mimeType'] == 'text/plain' and 'data' in subpart['body']:
                  body = base64.urlsafe_b64decode(subpart['body']['data']).decode('utf-8')
                  break
            elif part['mimeType'] == 'text/plain' and 'data' in part['body']:
              body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
              break
        elif 'body' in payload and 'data' in payload['body']:
          body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        return body

    def get_unread_emails(
        self,
        max_results: Optional[int] = 10
    ) -> EmailMessages:
        """
        Get unread emails from the user's inbox using the Gmail API.

        Args:
            max_results (int): Maximum number of unread emails to return.

        Returns:
            EmailMessages: Object containing unread email messages.
        """
        try:
            # Search for unread emails in inbox
            result = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                labelIds=['INBOX'],
                maxResults=max_results if max_results else 10
            ).execute()

            messages = result.get('messages', [])
            
            # Get detailed information for each message
            email_messages = []
            for message in messages:
                msg_id = message['id']
                msg_details = self.get_email_message_details(msg_id)
                email_messages.append(msg_details)

            return EmailMessages(
                count=len(email_messages),
                messages=email_messages,
                next_page_token=result.get('nextPageToken')
            )

        except Exception as e:
            return EmailMessages(
                count=0,
                messages=[],
                next_page_token=None
            )
        
    def create_draft_reply(
        self,
        thread_id: str,
        reply_body: str,
        body_type: Literal['plain', 'html'] = 'plain'
    ) -> dict:
        """
        Create a draft reply to an email thread using the Gmail API.

        Args:
            thread_id (str): The thread ID of the original email to reply to.
            reply_body (str): The body content of the reply.
            body_type (str): Type of the body content ('plain' or 'html').

        Returns:
            dict: Response from the Gmail API containing draft details.
        """
        try:
            # Get the original thread to extract reply information
            thread = self.service.users().threads().get(userId='me', id=thread_id).execute()
            messages = thread.get('messages', [])
            
            if not messages:
                return {'error': 'No messages found in thread', 'status': 'failed'}
            
            # Get the last message in the thread (most recent)
            original_message = messages[-1]
            original_payload = original_message['payload']
            original_headers = original_payload.get('headers', [])
            
            # Extract necessary headers for the reply
            original_subject = next((h['value'] for h in original_headers if h['name'].lower() == 'subject'), '')
            original_from = next((h['value'] for h in original_headers if h['name'].lower() == 'from'), '')
            original_to = next((h['value'] for h in original_headers if h['name'].lower() == 'to'), '')
            original_message_id = next((h['value'] for h in original_headers if h['name'].lower() == 'message-id'), '')
            
            # Prepare reply subject
            reply_subject = original_subject
            if not reply_subject.lower().startswith('re:'):
                reply_subject = f"Re: {reply_subject}"
            
            # Create the reply message
            message = MIMEMultipart()
            message['to'] = original_from  # Reply to the original sender
            message['subject'] = reply_subject
            message['In-Reply-To'] = original_message_id  # Threading
            message['References'] = original_message_id   # Threading
            
            if body_type.lower() not in ['plain', 'html']:
                return {'error': 'body_type must be either "plain" or "html"', 'status': 'failed'}

            # Attach the reply body
            message.attach(MIMEText(reply_body, body_type.lower()))

            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Create the draft
            draft_body = {
                'message': {
                    'raw': raw_message,
                    'threadId': thread_id
                }
            }

            draft = self.service.users().drafts().create(
                userId='me',
                body=draft_body
            ).execute()

            return {
                'draft_id': draft['id'],
                'message_id': draft['message']['id'],
                'thread_id': draft['message']['threadId'],
                'status': 'success'
            }

        except Exception as e:
            return {'error': f'An error occurred: {str(e)}', 'status': 'failed'}
        