"""
SpeedLead AI - Voice Bridge
Twilio ↔ Deepgram STT ↔ LLM ↔ Cartesia TTS

Handles inbound/outbound phone calls with real-time voice AI.
Low-cost architecture: ~0.035€/min total.
"""

import os
import json
import asyncio
import base64
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, WebSocket, Request, Response
from fastapi.responses import JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Connect
from twilio.rest import Client as TwilioClient
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from supabase import create_client

from config import Settings
from tts import CartesiaTTS
from llm import get_llm_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-bridge")

settings = Settings()

# Initialize clients
twilio_client = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)
deepgram = DeepgramClient(settings.deepgram_api_key)
supabase = create_client(settings.supabase_url, settings.supabase_service_key)
tts = CartesiaTTS(settings.cartesia_api_key, settings.cartesia_voice_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Voice Bridge starting for client: {settings.client_id}")
    yield
    logger.info("Voice Bridge shutting down")


app = FastAPI(title="SpeedLead Voice Bridge", lifespan=lifespan)


# ─── Twilio Webhook: Incoming Call ──────────────────────────────

@app.post("/voice/incoming")
async def handle_incoming_call(request: Request):
    """
    Twilio hits this endpoint when a call comes in.
    We respond with TwiML to connect a WebSocket media stream.
    """
    form = await request.form()
    caller = form.get("From", "unknown")
    called = form.get("To", "")

    logger.info(f"Incoming call from {caller} to {called}")

    # Create call record in Supabase
    call_record = supabase.table("calls").insert({
        "client_id": settings.client_id,
        "phone_number": caller,
        "direction": "inbound",
        "status": "in_progress",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

    call_id = call_record.data[0]["id"]

    # Respond with TwiML to open WebSocket stream
    response = VoiceResponse()

    # Initial greeting via TTS (pre-generated for speed)
    response.say(
        "Buongiorno! Un momento, la metto in contatto con il nostro assistente.",
        voice="alice",
        language="it-IT",
    )

    # Connect WebSocket for real-time audio
    connect = Connect()
    stream = connect.stream(
        url=f"wss://{request.headers.get('host', 'localhost')}/voice/stream",
    )
    stream.parameter(name="call_id", value=str(call_id))
    stream.parameter(name="caller", value=caller)
    response.append(connect)

    return Response(content=str(response), media_type="application/xml")


# ─── WebSocket: Real-time Audio Stream ─────────────────────────

@app.websocket("/voice/stream")
async def handle_media_stream(websocket: WebSocket):
    """
    Real-time bidirectional audio stream.
    Twilio → Deepgram STT → LLM → Cartesia TTS → Twilio
    """
    await websocket.accept()

    stream_sid = None
    call_id = None
    caller = None
    transcript_parts = []
    conversation_history = []

    # Start Deepgram live transcription
    dg_connection = deepgram.listen.asyncwebsocket.v("1")

    async def on_transcript(self, result, **kwargs):
        """Handle Deepgram transcription results."""
        nonlocal conversation_history

        sentence = result.channel.alternatives[0].transcript
        if not sentence or not sentence.strip():
            return

        is_final = result.is_final
        if not is_final:
            return

        logger.info(f"STT [{caller}]: {sentence}")
        transcript_parts.append({"role": "caller", "text": sentence})

        # Add to conversation history
        conversation_history.append({"role": "user", "content": sentence})

        # Get LLM response
        try:
            response_text = await get_llm_response(
                conversation_history=conversation_history,
                client_id=settings.client_id,
                caller=caller,
                supabase_client=supabase,
            )

            logger.info(f"LLM response: {response_text}")
            conversation_history.append({"role": "assistant", "content": response_text})
            transcript_parts.append({"role": "agent", "text": response_text})

            # Convert to speech via Cartesia
            audio_chunks = await tts.synthesize(response_text)

            # Send audio back to Twilio
            for chunk in audio_chunks:
                audio_b64 = base64.b64encode(chunk).decode("utf-8")
                await websocket.send_json({
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "payload": audio_b64,
                    },
                })

            # Mark end of response
            await websocket.send_json({
                "event": "mark",
                "streamSid": stream_sid,
                "mark": {"name": "response_end"},
            })

        except Exception as e:
            logger.error(f"Error processing response: {e}")

    async def on_error(self, error, **kwargs):
        logger.error(f"Deepgram error: {error}")

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_transcript)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    # Configure Deepgram for Italian real-time
    dg_options = LiveOptions(
        model="nova-2",
        language="it",
        encoding="mulaw",
        sample_rate=8000,
        channels=1,
        punctuate=True,
        interim_results=True,
        endpointing=300,
        vad_events=True,
        smart_format=True,
    )

    await dg_connection.start(dg_options)

    try:
        async for message in websocket.iter_text():
            data = json.loads(message)
            event = data.get("event")

            if event == "start":
                stream_sid = data["start"]["streamSid"]
                # Extract custom parameters
                params = {
                    p["name"]: p["value"]
                    for p in data["start"].get("customParameters", {}).items()
                } if isinstance(data["start"].get("customParameters"), dict) else {}

                call_id = params.get("call_id", data["start"].get("callSid"))
                caller = params.get("caller", "unknown")

                logger.info(f"Stream started: {stream_sid}, call: {call_id}")

                # Send initial greeting via Cartesia TTS
                greeting = await _get_greeting(caller)
                audio_chunks = await tts.synthesize(greeting)
                conversation_history.append({"role": "assistant", "content": greeting})

                for chunk in audio_chunks:
                    audio_b64 = base64.b64encode(chunk).decode("utf-8")
                    await websocket.send_json({
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {"payload": audio_b64},
                    })

            elif event == "media":
                # Forward audio to Deepgram
                audio_data = base64.b64decode(data["media"]["payload"])
                await dg_connection.send(audio_data)

            elif event == "stop":
                logger.info(f"Stream stopped: {stream_sid}")
                break

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await dg_connection.finish()

        # Save call record
        if call_id:
            full_transcript = "\n".join(
                f"{'Chiamante' if t['role'] == 'caller' else 'Agente'}: {t['text']}"
                for t in transcript_parts
            )

            # Generate call summary
            summary = await _generate_summary(transcript_parts)

            supabase.table("calls").update({
                "transcript": full_transcript,
                "summary": summary,
                "status": "completed",
                "ended_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", call_id).execute()

            logger.info(f"Call {call_id} saved with {len(transcript_parts)} transcript parts")


async def _get_greeting(caller: str) -> str:
    """Get personalized greeting based on caller info."""
    # Check if caller is a known lead
    result = (
        supabase.table("leads")
        .select("name, company")
        .eq("client_id", settings.client_id)
        .eq("phone", caller)
        .execute()
    )

    if result.data:
        lead = result.data[0]
        name = lead.get("name", "")
        return f"Buongiorno {name}! Sono l'assistente di {settings.client_id}. Che piacere risentirti, come posso aiutarti?"

    return "Buongiorno! Sono l'assistente commerciale. Come posso aiutarla oggi?"


async def _generate_summary(transcript_parts: list[dict]) -> str:
    """Generate a brief summary of the call using LLM."""
    if not transcript_parts:
        return "Chiamata senza conversazione."

    transcript = "\n".join(
        f"{t['role']}: {t['text']}" for t in transcript_parts
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-20250514",
                "max_tokens": 200,
                "messages": [{
                    "role": "user",
                    "content": f"Riassumi questa chiamata commerciale in 2-3 frasi in italiano. "
                               f"Indica: chi ha chiamato, cosa cercava, esito.\n\n{transcript}",
                }],
            },
            timeout=10,
        )
        data = resp.json()
        return data["content"][0]["text"]


# ─── Outbound Call ─────────────────────────────────────────────

@app.post("/voice/call-out")
async def initiate_outbound_call(request: Request):
    """Initiate an outbound call to a lead."""
    body = await request.json()
    to_number = body["phone"]
    lead_id = body.get("lead_id")
    message = body.get("message", "")

    call = twilio_client.calls.create(
        to=to_number,
        from_=settings.twilio_phone_number,
        url=f"https://{settings.domain}/voice/incoming",
        status_callback=f"https://{settings.domain}/voice/status",
        status_callback_event=["completed"],
    )

    # Log the outbound call
    supabase.table("calls").insert({
        "client_id": settings.client_id,
        "lead_id": lead_id,
        "phone_number": to_number,
        "direction": "outbound",
        "status": "initiated",
        "external_id": call.sid,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

    return JSONResponse({"call_sid": call.sid, "status": "initiated"})


# ─── Twilio Status Callback ───────────────────────────────────

@app.post("/voice/status")
async def handle_call_status(request: Request):
    """Handle Twilio call status updates."""
    form = await request.form()
    call_sid = form.get("CallSid")
    status = form.get("CallStatus")
    duration = form.get("CallDuration", "0")

    logger.info(f"Call {call_sid} status: {status}, duration: {duration}s")

    if call_sid:
        supabase.table("calls").update({
            "status": status,
            "duration_seconds": int(duration),
            "ended_at": datetime.now(timezone.utc).isoformat(),
        }).eq("external_id", call_sid).execute()

    return Response(status_code=204)


# ─── Webhook Receiver (Lead Intake) ───────────────────────────

@app.post("/webhook/lead")
async def receive_lead_webhook(request: Request):
    """
    Receive leads from external sources (web forms, CRMs, etc.).
    Triggers the speed-to-lead flow.
    """
    body = await request.json()

    lead = {
        "client_id": settings.client_id,
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

    # Notify OpenClaw to handle the lead
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{settings.openclaw_gateway_url}/api/webhook",
            json={
                "type": "lead_notification",
                "lead_id": lead_record["id"],
                "phone": lead_record.get("phone"),
                "message": f"Nuovo lead: {lead_record['name']} - {lead_record.get('company', 'N/D')}",
                "channel": lead_record["channel"],
            },
            timeout=10,
        )

    return JSONResponse({
        "status": "ok",
        "lead_id": lead_record["id"],
        "message": "Lead received, agent notified",
    })


# ─── Health Check ─────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "healthy", "client_id": settings.client_id}
