# SpeedLead AI

**Il tuo venditore AI che risponde su WhatsApp, Email e Telefono in italiano, 24/7, qualifica lead e prenota appuntamenti.**

Prodotto B2B completo basato su [OpenClaw](https://openclaw.ai) (l'agente AI autonomo open-source) per aziende italiane.

---

## Architettura

```
                    ┌─────────────────────────────────┐
                    │        Dashboard (Next.js)       │
                    │    Vercel / VPS EU (Hetzner)      │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────┴──────────────────┐
                    │        Supabase EU               │
                    │  (Postgres + Realtime + Auth)    │
                    └──────────────┬──────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
┌─────────┴─────────┐  ┌─────────┴─────────┐  ┌──────────┴──────────┐
│  OpenClaw Agent    │  │   Voice Bridge     │  │  Webhook Receiver   │
│  (per client)      │  │   (Python/FastAPI) │  │  (lead intake)      │
│                    │  │                    │  │                     │
│  WhatsApp (Baileys)│  │  Twilio +39        │  │  Web forms          │
│  Email (SMTP/IMAP) │  │  Deepgram STT      │  │  CRM webhooks       │
│  Skills system     │  │  Cartesia TTS      │  │  Fair/eventi        │
└────────────────────┘  └────────────────────┘  └─────────────────────┘
```

### Multi-Tenant: Un'Istanza per Cliente

Ogni cliente ha il proprio container Docker isolato con:
- OpenClaw agent dedicato con skills personalizzate
- Numero WhatsApp separato
- Configurazione e system prompt specifici
- Dati isolati (via Supabase RLS)

---

## Prerequisiti

- **Server**: Ubuntu 22.04+ VPS in EU (Hetzner CPX21: 4 vCPU, 8GB RAM, ~8 EUR/mese)
- **Docker**: Engine 24.0+ e Compose 2.20+
- **Node.js**: 20+ (per dashboard)
- **API Keys**: Anthropic (Claude), Supabase, Twilio, Deepgram, Cartesia
- **Dominio**: Per HTTPS via Caddy

---

## Installazione Rapida

### 1. Clona il Repository

```bash
git clone <repository-url>
cd openclaw-speedlead
```

### 2. Configura Supabase

1. Crea un nuovo progetto su [supabase.com](https://supabase.com) (seleziona regione EU)
2. Esegui lo schema SQL:

```bash
# Vai su Supabase Dashboard > SQL Editor > New Query
# Copia e incolla il contenuto di supabase/schema.sql
# Clicca "Run"
```

### 3. Configura Ambiente

```bash
cp .env.example .env
# Modifica .env con le tue API keys
```

### 4. Provisiona un Nuovo Cliente (1 comando)

```bash
./scripts/provision-client.sh acme-srl "Acme S.r.l." manifattura
```

Poi:
```bash
cd clients/acme-srl
# Modifica .env con le API keys del cliente
# Modifica config.json con i dettagli aziendali
docker compose up -d
```

### 5. Configura WhatsApp

```bash
# Dalla directory del cliente:
docker compose exec openclaw openclaw channels login
# Scannerizza il QR code con WhatsApp
```

### 6. Deploy Dashboard

```bash
cd dashboard
npm install
npm run build

# Per Vercel:
npx vercel

# O per self-hosted:
npm start
```

---

## Struttura del Progetto

```
openclaw-speedlead/
├── docker-compose.yml          # Docker Compose base
├── Dockerfile.openclaw         # Dockerfile per OpenClaw
├── .env.example                # Template variabili ambiente
│
├── skills/                     # Skills OpenClaw (Markdown + scripts)
│   ├── speed-to-lead/          # Skill principale: gestione lead rapida
│   │   ├── SKILL.md            # Definizione skill (YAML + istruzioni)
│   │   └── handlers.py         # Logica Python per webhook/Supabase
│   ├── email-skill/            # Gestione email automatica
│   │   ├── SKILL.md
│   │   └── email_handler.py
│   ├── calendar-book/          # Prenotazione appuntamenti
│   │   ├── SKILL.md
│   │   └── calendar_handler.py
│   ├── voice-bridge/           # Integrazione voce telefonica
│   │   └── SKILL.md
│   └── crm-sync/               # Sincronizzazione CRM
│       └── SKILL.md
│
├── config/                     # Configurazione OpenClaw
│   ├── openclaw.json           # Config gateway OpenClaw
│   ├── system-prompt.md        # System prompt italiano (template)
│   ├── client-template.json    # Template configurazione cliente
│   └── Caddyfile               # Reverse proxy config
│
├── voice-bridge/               # Servizio voce (Python/FastAPI)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # Entry point + Twilio webhook
│   ├── config.py               # Configurazione
│   ├── tts.py                  # Cartesia TTS integration
│   ├── llm.py                  # LLM per risposte vocali
│   └── webhook_receiver.py     # Webhook per lead intake
│
├── dashboard/                  # Next.js 15 Dashboard
│   ├── app/
│   │   ├── page.tsx            # Landing page pubblica
│   │   ├── dashboard/
│   │   │   ├── page.tsx        # Dashboard principale (lista lead)
│   │   │   └── leads/[id]/
│   │   │       └── page.tsx    # Dettaglio lead + conversazione
│   │   └── api/
│   │       ├── clients/route.ts      # CRUD clienti
│   │       ├── leads/route.ts        # CRUD lead + stats
│   │       └── voice-activate/route.ts # Attivazione Twilio
│   ├── lib/
│   │   ├── supabase.ts         # Client Supabase (browser + server)
│   │   └── types.ts            # TypeScript types
│   └── package.json
│
├── supabase/
│   └── schema.sql              # Schema database completo
│
├── scripts/
│   └── provision-client.sh     # Script per nuovo cliente
│
└── README.md                   # Questo file
```

---

## Skills OpenClaw

Le skills sono il cuore di SpeedLead AI. Sono file Markdown con YAML front matter, il formato nativo di OpenClaw.

| Skill | Funzione |
|-------|----------|
| **speed-to-lead** | Riceve lead da webhook, risponde su WhatsApp in < 20s, qualifica BANT, prenota |
| **email-skill** | Monitora inbox, risponde a email, invia materiale, follow-up automatici |
| **calendar-book** | Propone slot Cal.com/Google, conferma prenotazione, invia reminder |
| **voice-bridge** | Gestisce chiamate: Twilio -> Deepgram STT -> LLM -> Cartesia TTS |
| **crm-sync** | Sincronizza con HubSpot, Zoho, TeamSystem |

---

## Voice: Architettura e Costi

```
Chiamata +39 -> Twilio -> WebSocket -> Deepgram STT (real-time, IT)
                                            |
                                       Transcript
                                            |
                                    Claude Haiku (risposta breve)
                                            |
                                    Cartesia TTS (voce IT naturale)
                                            |
                              Twilio Media Stream <- Audio PCM
```

### Costi per Minuto

| Componente | Costo/min |
|------------|-----------|
| Twilio (numero IT + minuti) | ~0.010 EUR |
| Deepgram Nova-2 (STT) | ~0.005 EUR |
| Cartesia Sonic-2 (TTS) | ~0.015 EUR |
| Claude Haiku (LLM) | ~0.005 EUR |
| **Totale** | **~0.035 EUR/min** |

Target raggiunto: **< 0.05 EUR/min**

---

## Deploy in Produzione

### Opzione 1: VPS EU + Vercel (Consigliata)

**Server (OpenClaw + Voice)**:
- Hetzner CPX21 (4 vCPU, 8GB RAM): ~8 EUR/mese
- Supporta 3-5 clienti per server
- Caddy per HTTPS automatico

**Dashboard**:
- Vercel (free tier per iniziare)
- Supabase EU (free tier: 500MB, poi 25 EUR/mese)

**Costo infrastruttura per cliente**: ~15-25 EUR/mese

### Opzione 2: Railway

```bash
# OpenClaw + Voice Bridge
railway init
railway up

# Dashboard
cd dashboard
vercel
```

### Opzione 3: Full Self-Hosted

```bash
# Tutto su un VPS
docker compose up -d
```

---

## Prezzi da Vendere

| Piano | Setup | Mensile | Canali |
|-------|-------|---------|--------|
| **Starter** | 1.900 EUR | 490 EUR/mese | WhatsApp |
| **Professional** | 1.900 EUR | 690 EUR/mese | WhatsApp + Email + CRM |
| **Enterprise** | 2.900 EUR | 990 EUR/mese | WhatsApp + Email + Voce + CRM |

### Margini Stimati

| Voce | Costo Infra | Costo API (medio) | Totale Costi | Ricavo | Margine |
|------|-------------|--------------------|--------------| -------|---------|
| Starter | 15 EUR | 30 EUR | 45 EUR | 490 EUR | 91% |
| Professional | 20 EUR | 50 EUR | 70 EUR | 690 EUR | 90% |
| Enterprise | 25 EUR | 80 EUR | 105 EUR | 990 EUR | 89% |

---

## GDPR

- **Hosting EU**: Tutti i dati su server EU (Hetzner DE / Supabase EU)
- **RLS**: Row Level Security su Supabase per isolamento dati
- **DPA**: Template Data Processing Agreement incluso
- **Retention**: Configurabile per cliente (default 365 giorni)
- **Diritti**: Export e cancellazione dati supportati via API
- **No transfer US**: Nessun dato trasferito fuori EU (eccetto API calls a LLM)

### Nota su LLM e GDPR

Le chiamate API ad Anthropic (Claude) inviano il contenuto delle conversazioni ai server Anthropic. Per piena conformita GDPR:
- Anthropic offre DPA e SCCs per trasferimenti EU-US
- In alternativa, usare modelli locali via Ollama (nessun dato esce dal server)

---

## Comandi Utili

```bash
# Provisiona nuovo cliente
./scripts/provision-client.sh <client-id> "<nome azienda>" <settore>

# Avvia i servizi di un cliente
cd clients/<client-id> && docker compose up -d

# Vedi i log
docker compose logs -f openclaw

# Collega WhatsApp
docker compose exec openclaw openclaw channels login

# Restart
docker compose restart

# Stop
docker compose down

# Aggiorna OpenClaw
docker compose build --no-cache && docker compose up -d
```

---

## Sviluppo Locale

```bash
# Voice bridge (Python)
cd voice-bridge
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8765

# Dashboard (Next.js)
cd dashboard
npm install
npm run dev
```

---

## License

MIT
