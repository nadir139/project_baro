"""
LLM integration for voice conversations.
Uses Claude Haiku for speed (lowest latency) during calls.
"""

import os
import logging
import httpx
from supabase import Client as SupabaseClient

logger = logging.getLogger("voice-bridge.llm")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# System prompt for voice conversations (shorter than text for speed)
VOICE_SYSTEM_PROMPT = """Sei un assistente commerciale italiano al telefono. Regole:
- Risposte BREVI (1-2 frasi, max 30 parole)
- Italiano naturale e parlato
- Professionale ma cordiale, dai del Lei
- Obiettivo: qualificare il lead e fissare appuntamento
- Se il lead è interessato, proponi subito 2-3 slot per una call
- Non inventare informazioni su prodotti o prezzi
- Se non sai qualcosa, dì che farai avere le info via email"""


async def get_llm_response(
    conversation_history: list[dict],
    client_id: str,
    caller: str,
    supabase_client: SupabaseClient,
) -> str:
    """
    Get LLM response for voice conversation.
    Uses Claude Haiku for minimal latency.
    """
    # Enrich context with lead info if available
    lead_context = await _get_lead_context(caller, client_id, supabase_client)

    system = VOICE_SYSTEM_PROMPT
    if lead_context:
        system += f"\n\nInformazioni sul chiamante:\n{lead_context}"

    # Get client config for company info
    client_config = await _get_client_config(client_id, supabase_client)
    if client_config:
        system += f"\n\nAzienda: {client_config.get('company_name', client_id)}"
        system += f"\nSettore: {client_config.get('sector', 'N/D')}"

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-20250514",
                "max_tokens": 150,  # Short responses for voice
                "system": system,
                "messages": conversation_history[-10:],  # Last 10 turns
            },
            timeout=8,
        )

        data = resp.json()
        return data["content"][0]["text"]


async def _get_lead_context(
    phone: str, client_id: str, supabase_client: SupabaseClient
) -> str:
    """Get existing lead info for context."""
    try:
        result = (
            supabase_client.table("leads")
            .select("name, company, status, qualification_score, notes")
            .eq("client_id", client_id)
            .eq("phone", phone)
            .execute()
        )

        if result.data:
            lead = result.data[0]
            return (
                f"Nome: {lead.get('name', 'Sconosciuto')}\n"
                f"Azienda: {lead.get('company', 'N/D')}\n"
                f"Status: {lead.get('status', 'new')}\n"
                f"Score: {lead.get('qualification_score', 0)}/100\n"
                f"Note: {lead.get('notes', '')}"
            )
    except Exception as e:
        logger.error(f"Error fetching lead context: {e}")

    return ""


async def _get_client_config(
    client_id: str, supabase_client: SupabaseClient
) -> dict:
    """Get client configuration."""
    try:
        result = (
            supabase_client.table("client_configs")
            .select("*")
            .eq("client_id", client_id)
            .single()
            .execute()
        )
        return result.data or {}
    except Exception:
        return {}
