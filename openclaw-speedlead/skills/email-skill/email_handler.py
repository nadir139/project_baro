#!/usr/bin/env python3
"""
Email handler for SpeedLead AI.
Monitors IMAP inbox and sends emails via SMTP.
"""

import os
import ssl
import email
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import decode_header
from datetime import datetime, timezone
from supabase import create_client

SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
IMAP_HOST = os.environ["IMAP_HOST"]
IMAP_USER = os.environ["IMAP_USER"]
IMAP_PASS = os.environ["IMAP_PASS"]

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
CLIENT_ID = os.environ.get("CLIENT_ID", "default")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def check_inbox() -> list[dict]:
    """Check IMAP inbox for new unread emails."""
    messages = []

    imap = imaplib.IMAP4_SSL(IMAP_HOST)
    imap.login(IMAP_USER, IMAP_PASS)
    imap.select("INBOX")

    _, message_ids = imap.search(None, "UNSEEN")
    if not message_ids[0]:
        imap.logout()
        return messages

    for msg_id in message_ids[0].split():
        _, msg_data = imap.fetch(msg_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Decode subject
        subject = ""
        raw_subject = decode_header(msg["Subject"])
        for part, encoding in raw_subject:
            if isinstance(part, bytes):
                subject += part.decode(encoding or "utf-8", errors="replace")
            else:
                subject += part

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    body = part.get_payload(decode=True).decode(charset, errors="replace")
                    break
        else:
            charset = msg.get_content_charset() or "utf-8"
            body = msg.get_payload(decode=True).decode(charset, errors="replace")

        # Extract sender
        from_addr = email.utils.parseaddr(msg["From"])

        messages.append({
            "from_name": from_addr[0],
            "from_email": from_addr[1],
            "subject": subject,
            "body": body.strip(),
            "date": msg["Date"],
            "message_id": msg["Message-ID"],
        })

    imap.logout()
    return messages


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str = None,
    reply_to_message_id: str = None,
    attachments: list[dict] = None,
):
    """
    Send an email via SMTP.

    Args:
        to_email: Recipient email
        subject: Email subject
        body_html: HTML body
        body_text: Plain text body (fallback)
        reply_to_message_id: Message-ID to reply to
        attachments: List of {"filename": str, "content": bytes}
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    if reply_to_message_id:
        msg["In-Reply-To"] = reply_to_message_id
        msg["References"] = reply_to_message_id

    # Add text body
    if body_text:
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

    # Add HTML body
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    # Add attachments
    if attachments:
        for att in attachments:
            part = MIMEApplication(att["content"], Name=att["filename"])
            part["Content-Disposition"] = f'attachment; filename="{att["filename"]}"'
            msg.attach(part)

    # Send
    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    # Log to Supabase
    supabase.table("conversations").insert({
        "client_id": CLIENT_ID,
        "lead_id": None,  # Will be matched by email
        "role": "agent",
        "content": body_text or body_html,
        "channel": "email",
        "metadata": {"subject": subject, "to": to_email},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


def process_incoming_email(email_data: dict) -> dict:
    """
    Process an incoming email and determine if it's a lead.
    Returns lead data if it's a potential lead, None otherwise.
    """
    # Check if sender is already a known lead
    existing = (
        supabase.table("leads")
        .select("*")
        .eq("client_id", CLIENT_ID)
        .eq("email", email_data["from_email"])
        .execute()
    )

    if existing.data:
        # Existing lead - log conversation
        lead = existing.data[0]
        supabase.table("conversations").insert({
            "client_id": CLIENT_ID,
            "lead_id": lead["id"],
            "role": "lead",
            "content": f"Subject: {email_data['subject']}\n\n{email_data['body']}",
            "channel": "email",
            "metadata": {"message_id": email_data["message_id"]},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return {"type": "existing_lead", "lead": lead, "email": email_data}

    # New potential lead
    return {
        "type": "new_lead",
        "lead_data": {
            "name": email_data["from_name"],
            "email": email_data["from_email"],
            "source": "email",
            "channel": "email",
            "notes": f"Subject: {email_data['subject']}\n\n{email_data['body']}",
        },
        "email": email_data,
    }
