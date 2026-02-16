#!/usr/bin/env python3
"""
Speed-to-Lead Webhook Handler
Receives leads from external sources and triggers OpenClaw agent response.
"""

import os
import json
import httpx
from datetime import datetime, timezone
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
OPENCLAW_URL = os.environ.get("OPENCLAW_GATEWAY_URL", "http://localhost:18789")
CLIENT_ID = os.environ.get("CLIENT_ID", "default")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


async def handle_new_lead(lead_data: dict) -> dict:
    """
    Process a new lead from any source (web form, CRM, manual).
    Returns the created lead record.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Build lead record
    lead = {
        "client_id": CLIENT_ID,
        "name": lead_data.get("name", ""),
        "email": lead_data.get("email"),
        "phone": lead_data.get("phone"),
        "company": lead_data.get("company"),
        "source": lead_data.get("source", "web_form"),
        "channel": lead_data.get("channel", "whatsapp"),
        "status": "new",
        "qualification_score": 0,
        "qualification_data": {},
        "notes": lead_data.get("notes", ""),
        "metadata": lead_data.get("metadata", {}),
        "created_at": now,
        "updated_at": now,
    }

    # Insert into Supabase
    result = supabase.table("leads").insert(lead).execute()
    lead_record = result.data[0]

    # Trigger OpenClaw to respond
    await trigger_openclaw_response(lead_record)

    return lead_record


async def trigger_openclaw_response(lead: dict):
    """
    Send a message to OpenClaw gateway to trigger immediate response.
    OpenClaw will use the speed-to-lead skill to handle the conversation.
    """
    message = (
        f"NUOVO LEAD RICEVUTO - Rispondi immediatamente!\n"
        f"Nome: {lead['name']}\n"
        f"Telefono: {lead.get('phone', 'N/D')}\n"
        f"Email: {lead.get('email', 'N/D')}\n"
        f"Azienda: {lead.get('company', 'N/D')}\n"
        f"Canale: {lead['channel']}\n"
        f"Fonte: {lead['source']}\n"
        f"Note: {lead.get('notes', '')}\n"
        f"Lead ID: {lead['id']}"
    )

    async with httpx.AsyncClient() as client:
        # Send to OpenClaw webhook endpoint
        await client.post(
            f"{OPENCLAW_URL}/api/webhook",
            json={
                "type": "lead_notification",
                "lead_id": lead["id"],
                "phone": lead.get("phone"),
                "message": message,
                "channel": lead["channel"],
            },
            timeout=10,
        )


async def update_lead_status(lead_id: str, status: str, score: int = None, data: dict = None):
    """Update lead status and qualification data in Supabase."""
    update = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if score is not None:
        update["qualification_score"] = score
    if data is not None:
        update["qualification_data"] = data

    supabase.table("leads").update(update).eq("id", lead_id).execute()


async def log_conversation(lead_id: str, role: str, content: str, channel: str):
    """Log a conversation message to Supabase."""
    supabase.table("conversations").insert({
        "client_id": CLIENT_ID,
        "lead_id": lead_id,
        "role": role,  # "agent" or "lead"
        "content": content,
        "channel": channel,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


async def schedule_followup(lead_id: str, delay_hours: int, message_template: str):
    """Schedule a follow-up message for a lead."""
    from datetime import timedelta

    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=delay_hours)

    supabase.table("scheduled_actions").insert({
        "client_id": CLIENT_ID,
        "lead_id": lead_id,
        "action_type": "followup_message",
        "scheduled_at": scheduled_at.isoformat(),
        "payload": {"message_template": message_template},
        "status": "pending",
    }).execute()
