#!/usr/bin/env python3
"""
Calendar booking handler for SpeedLead AI.
Supports Cal.com and Google Calendar.
"""

import os
import httpx
from datetime import datetime, timedelta, timezone
from supabase import create_client

CALCOM_API_KEY = os.environ.get("CALCOM_API_KEY", "")
CALCOM_BASE_URL = "https://api.cal.com/v1"
CALCOM_EVENT_TYPE_ID = os.environ.get("CALCOM_EVENT_TYPE_ID", "")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
CLIENT_ID = os.environ.get("CLIENT_ID", "default")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


async def get_available_slots(days_ahead: int = 5) -> list[dict]:
    """
    Get available booking slots for the next N business days.
    Returns list of {"date": str, "time": str, "datetime": str} dicts.
    """
    now = datetime.now(timezone.utc)
    date_from = now.strftime("%Y-%m-%d")
    date_to = (now + timedelta(days=days_ahead + 2)).strftime("%Y-%m-%d")  # extra for weekends

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{CALCOM_BASE_URL}/availability",
            params={
                "apiKey": CALCOM_API_KEY,
                "eventTypeId": CALCOM_EVENT_TYPE_ID,
                "dateFrom": date_from,
                "dateTo": date_to,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

    slots = []
    for slot in data.get("slots", {}).values():
        for s in slot:
            dt = datetime.fromisoformat(s["time"].replace("Z", "+00:00"))
            # Filter business hours (9-12:30, 14-18 CET)
            cet_hour = (dt.hour + 1) % 24  # UTC+1 rough CET
            if (9 <= cet_hour <= 12) or (14 <= cet_hour <= 17):
                slots.append({
                    "date": dt.strftime("%A %d %B"),
                    "time": dt.strftime("%H:%M"),
                    "datetime": s["time"],
                })

    return slots[:6]  # Return max 6 slots


async def create_booking(
    lead_id: str,
    lead_name: str,
    lead_email: str,
    slot_datetime: str,
    duration_minutes: int = 30,
    notes: str = "",
) -> dict:
    """
    Create a booking on Cal.com and save to Supabase.
    """
    # Create on Cal.com
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CALCOM_BASE_URL}/bookings",
            params={"apiKey": CALCOM_API_KEY},
            json={
                "eventTypeId": int(CALCOM_EVENT_TYPE_ID),
                "start": slot_datetime,
                "responses": {
                    "name": lead_name,
                    "email": lead_email,
                },
                "metadata": {
                    "lead_id": lead_id,
                    "client_id": CLIENT_ID,
                    "source": "speedlead_ai",
                },
                "timeZone": "Europe/Rome",
                "language": "it",
            },
            timeout=15,
        )
        resp.raise_for_status()
        booking = resp.json()

    # Save to Supabase
    booking_record = {
        "client_id": CLIENT_ID,
        "lead_id": lead_id,
        "scheduled_at": slot_datetime,
        "duration_minutes": duration_minutes,
        "meeting_type": "video",
        "meeting_url": booking.get("metadata", {}).get("videoCallUrl", ""),
        "status": "confirmed",
        "notes": notes,
        "external_id": str(booking.get("id", "")),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = supabase.table("bookings").insert(booking_record).execute()

    # Update lead status
    supabase.table("leads").update({
        "status": "booked",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", lead_id).execute()

    return result.data[0]


async def cancel_booking(booking_id: str, reason: str = "") -> bool:
    """Cancel a booking on Cal.com and update Supabase."""
    # Get booking from Supabase
    booking = (
        supabase.table("bookings")
        .select("*")
        .eq("id", booking_id)
        .single()
        .execute()
    )

    if not booking.data:
        return False

    # Cancel on Cal.com
    if booking.data.get("external_id"):
        async with httpx.AsyncClient() as client:
            await client.delete(
                f"{CALCOM_BASE_URL}/bookings/{booking.data['external_id']}",
                params={"apiKey": CALCOM_API_KEY},
                json={"reason": reason},
                timeout=10,
            )

    # Update Supabase
    supabase.table("bookings").update({
        "status": "cancelled",
        "notes": f"{booking.data.get('notes', '')}\nCancelled: {reason}",
    }).eq("id", booking_id).execute()

    return True


async def reschedule_booking(booking_id: str, new_datetime: str) -> dict:
    """Reschedule a booking to a new datetime."""
    booking = (
        supabase.table("bookings")
        .select("*")
        .eq("id", booking_id)
        .single()
        .execute()
    )

    if not booking.data:
        return None

    # Reschedule on Cal.com
    if booking.data.get("external_id"):
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{CALCOM_BASE_URL}/bookings/{booking.data['external_id']}",
                params={"apiKey": CALCOM_API_KEY},
                json={"start": new_datetime},
                timeout=10,
            )

    # Update Supabase
    result = supabase.table("bookings").update({
        "scheduled_at": new_datetime,
        "status": "confirmed",
    }).eq("id", booking_id).execute()

    return result.data[0]
