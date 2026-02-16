#!/usr/bin/env python3
"""
CRM Sync handler for SpeedLead AI.
Bidirectional sync with HubSpot, Zoho CRM, and TeamSystem.
"""

import os
import logging
from datetime import datetime, timezone
from abc import ABC, abstractmethod

import httpx
from supabase import create_client

logger = logging.getLogger("crm-sync")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
CLIENT_ID = os.environ.get("CLIENT_ID", "default")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ─── Base CRM Interface ────────────────────────────────────────

class CRMProvider(ABC):
    """Abstract base class for CRM integrations."""

    @abstractmethod
    async def find_contact(self, email: str = None, phone: str = None) -> dict | None:
        """Find a contact in the CRM by email or phone."""

    @abstractmethod
    async def create_contact(self, lead: dict) -> str:
        """Create a contact in the CRM. Returns external ID."""

    @abstractmethod
    async def update_contact(self, external_id: str, data: dict) -> bool:
        """Update an existing contact in the CRM."""

    @abstractmethod
    async def create_note(self, external_id: str, content: str) -> str:
        """Add a note to a contact. Returns note external ID."""

    @abstractmethod
    async def create_meeting(self, external_id: str, booking: dict) -> str:
        """Create a meeting/event. Returns meeting external ID."""

    @abstractmethod
    async def get_recent_leads(self, since: datetime) -> list[dict]:
        """Get leads created/modified since a given datetime."""


# ─── HubSpot CRM ───────────────────────────────────────────────

class HubSpotCRM(CRMProvider):
    """HubSpot CRM integration using REST API v3."""

    BASE_URL = "https://api.hubapi.com"

    def __init__(self, api_key: str, config: dict = None):
        self.api_key = api_key
        self.config = config or {}
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def find_contact(self, email: str = None, phone: str = None) -> dict | None:
        async with httpx.AsyncClient() as client:
            if email:
                resp = await client.post(
                    f"{self.BASE_URL}/crm/v3/objects/contacts/search",
                    headers=self.headers,
                    json={
                        "filterGroups": [{
                            "filters": [{
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": email,
                            }]
                        }],
                        "properties": ["firstname", "lastname", "email", "phone", "company",
                                       "lifecyclestage", "hs_lead_status"],
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        return self._parse_contact(results[0])

            if phone:
                resp = await client.post(
                    f"{self.BASE_URL}/crm/v3/objects/contacts/search",
                    headers=self.headers,
                    json={
                        "filterGroups": [{
                            "filters": [{
                                "propertyName": "phone",
                                "operator": "EQ",
                                "value": phone,
                            }]
                        }],
                        "properties": ["firstname", "lastname", "email", "phone", "company"],
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        return self._parse_contact(results[0])

        return None

    async def create_contact(self, lead: dict) -> str:
        name_parts = (lead.get("name") or "").split(" ", 1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        properties = {
            "firstname": first_name,
            "lastname": last_name,
            "email": lead.get("email") or "",
            "phone": lead.get("phone") or "",
            "company": lead.get("company") or "",
            "hs_lead_status": self._map_status_to_hubspot(lead.get("status", "new")),
            "lifecyclestage": "lead",
        }

        # Add custom lead_score property if configured
        if lead.get("qualification_score") is not None:
            properties["hs_lead_score"] = str(lead["qualification_score"])

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/crm/v3/objects/contacts",
                headers=self.headers,
                json={"properties": properties},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["id"]

    async def update_contact(self, external_id: str, data: dict) -> bool:
        properties = {}
        if "name" in data:
            parts = data["name"].split(" ", 1)
            properties["firstname"] = parts[0]
            if len(parts) > 1:
                properties["lastname"] = parts[1]
        if "email" in data:
            properties["email"] = data["email"]
        if "phone" in data:
            properties["phone"] = data["phone"]
        if "company" in data:
            properties["company"] = data["company"]
        if "status" in data:
            properties["hs_lead_status"] = self._map_status_to_hubspot(data["status"])
        if "qualification_score" in data:
            properties["hs_lead_score"] = str(data["qualification_score"])

        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{self.BASE_URL}/crm/v3/objects/contacts/{external_id}",
                headers=self.headers,
                json={"properties": properties},
                timeout=10,
            )
            return resp.status_code == 200

    async def create_note(self, external_id: str, content: str) -> str:
        async with httpx.AsyncClient() as client:
            # Create note
            resp = await client.post(
                f"{self.BASE_URL}/crm/v3/objects/notes",
                headers=self.headers,
                json={
                    "properties": {
                        "hs_note_body": content,
                        "hs_timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                },
                timeout=10,
            )
            resp.raise_for_status()
            note_id = resp.json()["id"]

            # Associate note with contact
            await client.put(
                f"{self.BASE_URL}/crm/v3/objects/notes/{note_id}/associations/contacts/{external_id}/202",
                headers=self.headers,
                timeout=10,
            )
            return note_id

    async def create_meeting(self, external_id: str, booking: dict) -> str:
        start_time = booking.get("scheduled_at", "")
        duration = booking.get("duration_minutes", 30)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/crm/v3/objects/meetings",
                headers=self.headers,
                json={
                    "properties": {
                        "hs_meeting_title": f"SpeedLead - Appuntamento Commerciale",
                        "hs_meeting_body": booking.get("notes", ""),
                        "hs_meeting_start_time": start_time,
                        "hs_meeting_end_time": "",  # HubSpot calculates from duration
                        "hs_meeting_external_url": booking.get("meeting_url", ""),
                    }
                },
                timeout=10,
            )
            resp.raise_for_status()
            meeting_id = resp.json()["id"]

            # Associate meeting with contact
            await client.put(
                f"{self.BASE_URL}/crm/v3/objects/meetings/{meeting_id}/associations/contacts/{external_id}/200",
                headers=self.headers,
                timeout=10,
            )
            return meeting_id

    async def get_recent_leads(self, since: datetime) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/crm/v3/objects/contacts/search",
                headers=self.headers,
                json={
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "lastmodifieddate",
                            "operator": "GTE",
                            "value": str(int(since.timestamp() * 1000)),
                        }]
                    }],
                    "properties": ["firstname", "lastname", "email", "phone", "company",
                                   "lifecyclestage", "hs_lead_status", "hs_lead_score"],
                    "limit": 100,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return [self._parse_contact(r) for r in resp.json().get("results", [])]
        return []

    def _parse_contact(self, raw: dict) -> dict:
        props = raw.get("properties", {})
        return {
            "external_id": raw["id"],
            "name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
            "email": props.get("email"),
            "phone": props.get("phone"),
            "company": props.get("company"),
            "status": self._map_status_from_hubspot(props.get("hs_lead_status", "")),
            "score": int(props.get("hs_lead_score", 0) or 0),
        }

    @staticmethod
    def _map_status_to_hubspot(status: str) -> str:
        mapping = {
            "new": "NEW",
            "contacted": "ATTEMPTED_TO_CONTACT",
            "qualifying": "IN_PROGRESS",
            "qualified": "OPEN_DEAL",
            "booked": "OPEN_DEAL",
            "won": "WON",
            "lost": "LOST",
            "cold": "UNQUALIFIED",
        }
        return mapping.get(status, "NEW")

    @staticmethod
    def _map_status_from_hubspot(hs_status: str) -> str:
        mapping = {
            "NEW": "new",
            "ATTEMPTED_TO_CONTACT": "contacted",
            "IN_PROGRESS": "qualifying",
            "OPEN_DEAL": "qualified",
            "WON": "won",
            "LOST": "lost",
            "UNQUALIFIED": "cold",
        }
        return mapping.get(hs_status, "new")


# ─── Zoho CRM ──────────────────────────────────────────────────

class ZohoCRM(CRMProvider):
    """Zoho CRM integration using REST API v2."""

    BASE_URL = "https://www.zohoapis.eu/crm/v2"

    def __init__(self, client_id: str, client_secret: str, refresh_token: str, config: dict = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.config = config or {}

    async def _ensure_token(self):
        """Refresh the access token if needed."""
        if self.access_token:
            return

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://accounts.zoho.eu/oauth/v2/token",
                params={
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                },
                timeout=10,
            )
            resp.raise_for_status()
            self.access_token = resp.json()["access_token"]

    def _headers(self) -> dict:
        return {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json",
        }

    async def find_contact(self, email: str = None, phone: str = None) -> dict | None:
        await self._ensure_token()

        criteria = None
        if email:
            criteria = f"(Email:equals:{email})"
        elif phone:
            criteria = f"(Phone:equals:{phone})"
        else:
            return None

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/Leads/search",
                headers=self._headers(),
                params={"criteria": criteria},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    return self._parse_lead(data[0])
        return None

    async def create_contact(self, lead: dict) -> str:
        await self._ensure_token()

        zoho_data = {
            "Full_Name": lead.get("name", ""),
            "Email": lead.get("email") or "",
            "Phone": lead.get("phone") or "",
            "Company": lead.get("company") or "",
            "Lead_Status": self._map_status_to_zoho(lead.get("status", "new")),
            "Description": lead.get("notes") or "",
            "Lead_Source": "SpeedLead AI",
        }

        if lead.get("qualification_score") is not None:
            zoho_data["Rating"] = self._score_to_rating(lead["qualification_score"])

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/Leads",
                headers=self._headers(),
                json={"data": [zoho_data]},
                timeout=10,
            )
            resp.raise_for_status()
            result = resp.json()
            return result["data"][0]["details"]["id"]

    async def update_contact(self, external_id: str, data: dict) -> bool:
        await self._ensure_token()

        zoho_data = {}
        if "name" in data:
            zoho_data["Full_Name"] = data["name"]
        if "email" in data:
            zoho_data["Email"] = data["email"]
        if "phone" in data:
            zoho_data["Phone"] = data["phone"]
        if "company" in data:
            zoho_data["Company"] = data["company"]
        if "status" in data:
            zoho_data["Lead_Status"] = self._map_status_to_zoho(data["status"])
        if "qualification_score" in data:
            zoho_data["Rating"] = self._score_to_rating(data["qualification_score"])

        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{self.BASE_URL}/Leads/{external_id}",
                headers=self._headers(),
                json={"data": [zoho_data]},
                timeout=10,
            )
            return resp.status_code == 200

    async def create_note(self, external_id: str, content: str) -> str:
        await self._ensure_token()

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/Leads/{external_id}/Notes",
                headers=self._headers(),
                json={"data": [{"Note_Content": content}]},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["details"]["id"]

    async def create_meeting(self, external_id: str, booking: dict) -> str:
        await self._ensure_token()

        event_data = {
            "Event_Title": "SpeedLead - Appuntamento Commerciale",
            "Start_DateTime": booking.get("scheduled_at", ""),
            "End_DateTime": "",  # Calculate from duration
            "Description": booking.get("notes", ""),
            "What_Id": external_id,
            "se_module": "Leads",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/Events",
                headers=self._headers(),
                json={"data": [event_data]},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["details"]["id"]

    async def get_recent_leads(self, since: datetime) -> list[dict]:
        await self._ensure_token()

        since_str = since.strftime("%Y-%m-%dT%H:%M:%S%z")

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/Leads",
                headers=self._headers(),
                params={
                    "modified_since": since_str,
                    "per_page": 100,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                return [self._parse_lead(d) for d in data]
        return []

    def _parse_lead(self, raw: dict) -> dict:
        return {
            "external_id": raw.get("id", ""),
            "name": raw.get("Full_Name", ""),
            "email": raw.get("Email"),
            "phone": raw.get("Phone"),
            "company": raw.get("Company"),
            "status": self._map_status_from_zoho(raw.get("Lead_Status", "")),
            "score": self._rating_to_score(raw.get("Rating", "")),
        }

    @staticmethod
    def _map_status_to_zoho(status: str) -> str:
        mapping = {
            "new": "Not Contacted",
            "contacted": "Attempted to Contact",
            "qualifying": "Contact in Future",
            "qualified": "Contacted",
            "booked": "Contacted",
            "won": "Closed Won",
            "lost": "Closed Lost",
            "cold": "Lost Lead",
        }
        return mapping.get(status, "Not Contacted")

    @staticmethod
    def _map_status_from_zoho(zoho_status: str) -> str:
        mapping = {
            "Not Contacted": "new",
            "Attempted to Contact": "contacted",
            "Contact in Future": "qualifying",
            "Contacted": "qualified",
            "Closed Won": "won",
            "Closed Lost": "lost",
            "Lost Lead": "cold",
        }
        return mapping.get(zoho_status, "new")

    @staticmethod
    def _score_to_rating(score: int) -> str:
        if score >= 70:
            return "Hot"
        if score >= 40:
            return "Warm"
        return "Cold"

    @staticmethod
    def _rating_to_score(rating: str) -> int:
        mapping = {"Hot": 80, "Active": 60, "Warm": 50, "Cold": 20}
        return mapping.get(rating, 0)


# ─── TeamSystem CRM ────────────────────────────────────────────

class TeamSystemCRM(CRMProvider):
    """TeamSystem CRM integration (Italian enterprise ERP/CRM)."""

    def __init__(self, api_url: str, api_key: str, config: dict = None):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.config = config or {}
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def find_contact(self, email: str = None, phone: str = None) -> dict | None:
        async with httpx.AsyncClient() as client:
            params = {}
            if email:
                params["email"] = email
            elif phone:
                params["telefono"] = phone
            else:
                return None

            resp = await client.get(
                f"{self.api_url}/api/v1/anagrafiche/search",
                headers=self.headers,
                params=params,
                timeout=10,
            )
            if resp.status_code == 200:
                results = resp.json().get("data", [])
                if results:
                    return self._parse_anagrafica(results[0])
        return None

    async def create_contact(self, lead: dict) -> str:
        anagrafica = {
            "ragione_sociale": lead.get("company") or lead.get("name", ""),
            "nome_referente": lead.get("name", ""),
            "email": lead.get("email") or "",
            "telefono": lead.get("phone") or "",
            "tipo": "lead",
            "origine": "SpeedLead AI",
            "note": lead.get("notes") or "",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_url}/api/v1/anagrafiche",
                headers=self.headers,
                json=anagrafica,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            external_id = str(data.get("id", data.get("data", {}).get("id", "")))

            # Also create an opportunity
            await self._create_opportunity(external_id, lead)

            return external_id

    async def _create_opportunity(self, anagrafica_id: str, lead: dict):
        """Create an opportunity (opportunita) linked to the contact."""
        opportunita = {
            "anagrafica_id": anagrafica_id,
            "titolo": f"Lead SpeedLead - {lead.get('name', '')}",
            "stato_opportunita": self._map_status_to_teamsystem(lead.get("status", "new")),
            "priorita": self._score_to_priority(lead.get("qualification_score", 0)),
            "origine": "SpeedLead AI",
            "note": lead.get("notes") or "",
        }

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.api_url}/api/v1/opportunita",
                headers=self.headers,
                json=opportunita,
                timeout=10,
            )

    async def update_contact(self, external_id: str, data: dict) -> bool:
        update_data = {}
        if "name" in data:
            update_data["nome_referente"] = data["name"]
        if "company" in data:
            update_data["ragione_sociale"] = data["company"]
        if "email" in data:
            update_data["email"] = data["email"]
        if "phone" in data:
            update_data["telefono"] = data["phone"]

        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{self.api_url}/api/v1/anagrafiche/{external_id}",
                headers=self.headers,
                json=update_data,
                timeout=10,
            )
            return resp.status_code == 200

    async def create_note(self, external_id: str, content: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_url}/api/v1/anagrafiche/{external_id}/note",
                headers=self.headers,
                json={
                    "testo": content,
                    "tipo": "conversazione",
                    "origine": "SpeedLead AI",
                },
                timeout=10,
            )
            resp.raise_for_status()
            return str(resp.json().get("id", ""))

    async def create_meeting(self, external_id: str, booking: dict) -> str:
        attivita = {
            "anagrafica_id": external_id,
            "tipo": "appuntamento",
            "titolo": "Appuntamento Commerciale SpeedLead",
            "data_inizio": booking.get("scheduled_at", ""),
            "durata_minuti": booking.get("duration_minutes", 30),
            "note": booking.get("notes", ""),
            "luogo": booking.get("meeting_url", "Videochiamata"),
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_url}/api/v1/attivita",
                headers=self.headers,
                json=attivita,
                timeout=10,
            )
            resp.raise_for_status()
            return str(resp.json().get("id", ""))

    async def get_recent_leads(self, since: datetime) -> list[dict]:
        since_str = since.strftime("%Y-%m-%dT%H:%M:%S")

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.api_url}/api/v1/anagrafiche",
                headers=self.headers,
                params={
                    "modificato_da": since_str,
                    "tipo": "lead",
                    "limit": 100,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                return [self._parse_anagrafica(d) for d in data]
        return []

    def _parse_anagrafica(self, raw: dict) -> dict:
        return {
            "external_id": str(raw.get("id", "")),
            "name": raw.get("nome_referente", raw.get("ragione_sociale", "")),
            "email": raw.get("email"),
            "phone": raw.get("telefono"),
            "company": raw.get("ragione_sociale"),
            "status": self._map_status_from_teamsystem(raw.get("stato", "")),
            "score": 0,
        }

    @staticmethod
    def _map_status_to_teamsystem(status: str) -> str:
        mapping = {
            "new": "nuovo",
            "contacted": "contattato",
            "qualifying": "in_qualifica",
            "qualified": "qualificato",
            "booked": "appuntamento",
            "won": "vinto",
            "lost": "perso",
            "cold": "freddo",
        }
        return mapping.get(status, "nuovo")

    @staticmethod
    def _map_status_from_teamsystem(ts_status: str) -> str:
        mapping = {
            "nuovo": "new",
            "contattato": "contacted",
            "in_qualifica": "qualifying",
            "qualificato": "qualified",
            "appuntamento": "booked",
            "vinto": "won",
            "perso": "lost",
            "freddo": "cold",
        }
        return mapping.get(ts_status, "new")

    @staticmethod
    def _score_to_priority(score: int) -> str:
        if score >= 70:
            return "alta"
        if score >= 40:
            return "media"
        return "bassa"


# ─── CRM Factory ───────────────────────────────────────────────

def create_crm_provider(provider: str, config: dict) -> CRMProvider:
    """Factory to create the appropriate CRM provider."""
    if provider == "hubspot":
        return HubSpotCRM(
            api_key=config.get("api_key", ""),
            config=config,
        )
    elif provider == "zoho":
        return ZohoCRM(
            client_id=config.get("client_id", ""),
            client_secret=config.get("client_secret", ""),
            refresh_token=config.get("refresh_token", ""),
            config=config,
        )
    elif provider == "teamsystem":
        return TeamSystemCRM(
            api_url=config.get("api_url", ""),
            api_key=config.get("api_key", ""),
            config=config,
        )
    else:
        raise ValueError(f"Unknown CRM provider: {provider}")


# ─── Sync Orchestrator ─────────────────────────────────────────

async def sync_lead_to_crm(lead_id: str):
    """
    Sync a single lead from SpeedLead to the configured CRM.
    Called when a lead status changes.
    """
    # Get client CRM config
    config_result = (
        supabase.table("client_configs")
        .select("crm_provider, crm_config")
        .eq("client_id", CLIENT_ID)
        .single()
        .execute()
    )

    if not config_result.data or not config_result.data.get("crm_provider"):
        return  # No CRM configured

    provider_name = config_result.data["crm_provider"]
    crm_config = config_result.data.get("crm_config", {})

    crm = create_crm_provider(provider_name, crm_config)

    # Get lead data
    lead_result = supabase.table("leads").select("*").eq("id", lead_id).single().execute()
    if not lead_result.data:
        return

    lead = lead_result.data

    # Check if contact exists in CRM
    existing = await crm.find_contact(email=lead.get("email"), phone=lead.get("phone"))

    if existing:
        # Update existing contact
        await crm.update_contact(existing["external_id"], {
            "name": lead["name"],
            "email": lead.get("email"),
            "phone": lead.get("phone"),
            "company": lead.get("company"),
            "status": lead["status"],
            "qualification_score": lead.get("qualification_score", 0),
        })
        external_id = existing["external_id"]
    else:
        # Create new contact
        external_id = await crm.create_contact(lead)

    # Update lead with CRM external ID
    supabase.table("leads").update({
        "metadata": {
            **(lead.get("metadata") or {}),
            "crm_external_id": external_id,
            "crm_provider": provider_name,
            "crm_synced_at": datetime.now(timezone.utc).isoformat(),
        }
    }).eq("id", lead_id).execute()

    logger.info(f"Lead {lead_id} synced to {provider_name} as {external_id}")


async def sync_conversations_to_crm(lead_id: str):
    """Sync recent conversations for a lead to CRM notes."""
    config_result = (
        supabase.table("client_configs")
        .select("crm_provider, crm_config")
        .eq("client_id", CLIENT_ID)
        .single()
        .execute()
    )

    if not config_result.data or not config_result.data.get("crm_provider"):
        return

    crm = create_crm_provider(
        config_result.data["crm_provider"],
        config_result.data.get("crm_config", {}),
    )

    # Get lead's CRM external ID
    lead = supabase.table("leads").select("metadata").eq("id", lead_id).single().execute()
    if not lead.data:
        return

    external_id = (lead.data.get("metadata") or {}).get("crm_external_id")
    if not external_id:
        return

    # Get unsorted conversations
    conversations = (
        supabase.table("conversations")
        .select("*")
        .eq("lead_id", lead_id)
        .order("created_at", desc=False)
        .limit(20)
        .execute()
    )

    if not conversations.data:
        return

    # Build conversation summary
    summary_lines = []
    for msg in conversations.data:
        role = "Agente" if msg["role"] == "agent" else "Lead"
        summary_lines.append(f"[{msg['channel']}] {role}: {msg['content']}")

    summary = "\n".join(summary_lines)
    note_content = f"[SpeedLead AI] Riepilogo conversazione:\n\n{summary}"

    await crm.create_note(external_id, note_content)


async def sync_booking_to_crm(booking_id: str):
    """Sync a booking to the CRM as a meeting/event."""
    config_result = (
        supabase.table("client_configs")
        .select("crm_provider, crm_config")
        .eq("client_id", CLIENT_ID)
        .single()
        .execute()
    )

    if not config_result.data or not config_result.data.get("crm_provider"):
        return

    crm = create_crm_provider(
        config_result.data["crm_provider"],
        config_result.data.get("crm_config", {}),
    )

    # Get booking
    booking = supabase.table("bookings").select("*").eq("id", booking_id).single().execute()
    if not booking.data:
        return

    # Get lead's CRM external ID
    lead_id = booking.data.get("lead_id")
    if not lead_id:
        return

    lead = supabase.table("leads").select("metadata").eq("id", lead_id).single().execute()
    if not lead.data:
        return

    external_id = (lead.data.get("metadata") or {}).get("crm_external_id")
    if not external_id:
        return

    await crm.create_meeting(external_id, booking.data)


async def import_leads_from_crm():
    """
    Import new leads from CRM that don't exist in SpeedLead.
    Called periodically (every 15 minutes).
    """
    config_result = (
        supabase.table("client_configs")
        .select("crm_provider, crm_config")
        .eq("client_id", CLIENT_ID)
        .single()
        .execute()
    )

    if not config_result.data or not config_result.data.get("crm_provider"):
        return 0

    crm = create_crm_provider(
        config_result.data["crm_provider"],
        config_result.data.get("crm_config", {}),
    )

    # Get leads modified in last 20 minutes (overlap to avoid gaps)
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(minutes=20)
    crm_leads = await crm.get_recent_leads(since)

    imported = 0
    for crm_lead in crm_leads:
        # Check if already in SpeedLead
        existing = None
        if crm_lead.get("email"):
            result = (
                supabase.table("leads")
                .select("id")
                .eq("client_id", CLIENT_ID)
                .eq("email", crm_lead["email"])
                .execute()
            )
            if result.data:
                existing = result.data[0]

        if not existing and crm_lead.get("phone"):
            result = (
                supabase.table("leads")
                .select("id")
                .eq("client_id", CLIENT_ID)
                .eq("phone", crm_lead["phone"])
                .execute()
            )
            if result.data:
                existing = result.data[0]

        if existing:
            continue  # Already in SpeedLead

        # Import new lead
        supabase.table("leads").insert({
            "client_id": CLIENT_ID,
            "name": crm_lead.get("name", "Importato da CRM"),
            "email": crm_lead.get("email"),
            "phone": crm_lead.get("phone"),
            "company": crm_lead.get("company"),
            "source": f"crm_{config_result.data['crm_provider']}",
            "channel": "manual",
            "status": crm_lead.get("status", "new"),
            "qualification_score": crm_lead.get("score", 0),
            "metadata": {
                "crm_external_id": crm_lead.get("external_id"),
                "crm_provider": config_result.data["crm_provider"],
                "imported_at": datetime.now(timezone.utc).isoformat(),
            },
        }).execute()
        imported += 1

    logger.info(f"Imported {imported} leads from CRM")
    return imported
