"""
Standalone webhook receiver for lead intake.
Runs as a separate service when voice bridge is not needed.
"""

import os
import logging
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from supabase import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook-receiver")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
CLIENT_ID = os.environ.get("CLIENT_ID", "default")
OPENCLAW_URL = os.environ.get("OPENCLAW_GATEWAY_URL", "http://openclaw:18789")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="SpeedLead Webhook Receiver")


@app.post("/webhook/lead")
async def receive_lead(request: Request):
    """Receive a lead from any external source."""
    body = await request.json()

    lead = {
        "client_id": CLIENT_ID,
        "name": body.get("name", ""),
        "email": body.get("email"),
        "phone": body.get("phone"),
        "company": body.get("company"),
        "source": body.get("source", "webhook"),
        "channel": body.get("channel", "whatsapp"),
        "status": "new",
        "qualification_score": 0,
        "notes": body.get("notes", ""),
        "metadata": body.get("metadata", {}),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = supabase.table("leads").insert(lead).execute()
    lead_record = result.data[0]

    # Notify OpenClaw
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{OPENCLAW_URL}/api/webhook",
                json={
                    "type": "lead_notification",
                    "lead_id": lead_record["id"],
                    "phone": lead_record.get("phone"),
                    "channel": lead_record["channel"],
                },
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Failed to notify OpenClaw: {e}")

    return JSONResponse({
        "status": "ok",
        "lead_id": lead_record["id"],
    })


@app.post("/webhook/form/{form_id}")
async def receive_form_submission(form_id: str, request: Request):
    """
    Receive form submissions from various providers.
    Maps common form fields to lead fields.
    """
    body = await request.json()

    # Map common form field names
    name = (
        body.get("name")
        or body.get("nome")
        or body.get("full_name")
        or f"{body.get('first_name', '')} {body.get('last_name', '')}".strip()
        or "Sconosciuto"
    )

    lead = {
        "client_id": CLIENT_ID,
        "name": name,
        "email": body.get("email") or body.get("email_address"),
        "phone": body.get("phone") or body.get("telefono") or body.get("phone_number"),
        "company": body.get("company") or body.get("azienda") or body.get("company_name"),
        "source": f"form_{form_id}",
        "channel": "whatsapp",
        "status": "new",
        "qualification_score": 0,
        "notes": body.get("message") or body.get("messaggio") or body.get("notes") or "",
        "metadata": {"form_id": form_id, "raw_data": body},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = supabase.table("leads").insert(lead).execute()
    lead_record = result.data[0]

    # Notify OpenClaw
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{OPENCLAW_URL}/api/webhook",
                json={
                    "type": "lead_notification",
                    "lead_id": lead_record["id"],
                    "phone": lead_record.get("phone"),
                    "channel": "whatsapp",
                },
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Failed to notify OpenClaw: {e}")

    return JSONResponse({"status": "ok", "lead_id": lead_record["id"]})


@app.get("/health")
async def health():
    return {"status": "healthy", "client_id": CLIENT_ID}
