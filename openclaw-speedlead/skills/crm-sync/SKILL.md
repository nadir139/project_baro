---
name: crm-sync
description: >
  Sincronizza i lead e le conversazioni con i CRM esterni del cliente.
  Supporta HubSpot, Zoho CRM e TeamSystem. Bidirezionale: importa lead
  dal CRM ed esporta qualificazioni e appuntamenti.
metadata:
  openclaw:
    requires:
      env:
        - SUPABASE_URL
        - SUPABASE_SERVICE_KEY
    primaryEnv: SUPABASE_SERVICE_KEY
---

# CRM Sync - Sincronizzazione CRM

Sincronizza bidirezionalmente i dati dei lead con i CRM del cliente.

## CRM Supportati

### 1. HubSpot
- **Env**: `HUBSPOT_API_KEY`
- Sincronizza: Contacts, Deals, Notes, Meetings
- Mappa: lead → Contact, appuntamento → Meeting, conversazione → Note

### 2. Zoho CRM
- **Env**: `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN`
- Sincronizza: Leads, Deals, Notes, Events
- Mappa: lead → Lead/Contact, appuntamento → Event

### 3. TeamSystem (Enterprise italiano)
- **Env**: `TEAMSYSTEM_API_URL`, `TEAMSYSTEM_API_KEY`
- Sincronizza: Anagrafiche, Opportunità, Attività
- Mappa: lead → Anagrafica + Opportunità

## Processo di Sincronizzazione

### Export (SpeedLead → CRM)
Quando un lead cambia stato in SpeedLead:
1. Controlla se il lead esiste già nel CRM (match per email o telefono)
2. Se esiste: aggiorna i campi
3. Se non esiste: crea nuovo record
4. Sincronizza note, conversazioni e appuntamenti

### Import (CRM → SpeedLead)
Periodicamente (ogni 15 minuti):
1. Controlla nuovi lead nel CRM
2. Importa lead non ancora presenti in SpeedLead
3. Aggiorna status se modificato nel CRM

## Mappatura Campi

| SpeedLead | HubSpot | Zoho | TeamSystem |
|-----------|---------|------|------------|
| name | firstname + lastname | Full_Name | ragione_sociale |
| email | email | Email | email |
| phone | phone | Phone | telefono |
| company | company | Company | ragione_sociale |
| status | lifecyclestage | Lead_Status | stato_opportunita |
| qualification_score | lead_score (custom) | Rating | priorita |
| notes | notes | Description | note |

## Configurazione per Cliente

Ogni cliente può configurare il proprio CRM in Supabase (tabella `client_configs`):

```json
{
  "crm": {
    "provider": "hubspot",
    "api_key": "...",
    "sync_interval_minutes": 15,
    "field_mapping": {},
    "auto_create_deals": true,
    "deal_pipeline_id": "..."
  }
}
```

## Regole di Conflitto
- Se un campo è stato modificato sia in SpeedLead che nel CRM: vince l'ultima modifica
- Gli appuntamenti creati da SpeedLead non vengono sovrascritti dal CRM
- Le conversazioni sono solo esportate (mai importate)
