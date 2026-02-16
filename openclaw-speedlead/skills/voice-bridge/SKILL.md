---
name: voice-bridge
description: >
  Gestisce chiamate telefoniche in arrivo e in uscita tramite Twilio.
  Converte voce in testo con Deepgram, elabora con l'agente AI,
  e risponde con voce naturale italiana via Cartesia TTS.
metadata:
  openclaw:
    requires:
      env:
        - TWILIO_ACCOUNT_SID
        - TWILIO_AUTH_TOKEN
        - DEEPGRAM_API_KEY
        - CARTESIA_API_KEY
      bins:
        - python3
    primaryEnv: TWILIO_ACCOUNT_SID
---

# Voice Bridge - Chiamate Telefoniche AI

Gestisce il canale voce per SpeedLead AI. Collega Twilio (telefonia) con
Deepgram (speech-to-text), l'agente AI (per generare risposte), e
Cartesia (text-to-speech) per conversazioni telefoniche naturali in italiano.

## Quando Attivare

- Quando arriva una chiamata al numero Twilio +39
- Quando serve fare una chiamata in uscita a un lead
- Quando il lead chiede di essere richiamato

## Architettura

```
Chiamante → Twilio +39 → WebSocket → Deepgram STT (real-time)
                                          ↓
                                     Transcript IT
                                          ↓
                                    OpenClaw Agent (risposta)
                                          ↓
                                    Cartesia TTS (voce IT)
                                          ↓
                              Twilio Media Stream ← Audio
```

## Flusso Chiamata in Arrivo

### 1. Risposta Iniziale
Quando arriva una chiamata, rispondi entro 2 secondi con:
"Buongiorno! Sono [NOME_AGENTE] di [AZIENDA]. Come posso aiutarla?"

### 2. Conversazione
- Deepgram trascrive in tempo reale (modello `nova-2`, lingua `it`)
- Ogni frase completata viene inviata all'agente OpenClaw
- L'agente genera la risposta usando il contesto del lead (se noto)
- Cartesia converte in audio con voce italiana naturale
- L'audio viene inviato a Twilio come media stream

### 3. Fine Chiamata
- Salva la trascrizione completa su Supabase
- Aggiorna lo status del lead
- Se il lead è nuovo, crea il record in Supabase
- Genera un riepilogo della chiamata per il venditore

## Costi Previsti
- Twilio: ~0.01€/min (numero IT + minuti)
- Deepgram: ~0.005€/min (modello Nova-2)
- Cartesia: ~0.015€/min (voce streaming)
- LLM: ~0.005€/min (Claude Haiku per velocità)
- **Totale: ~0.035€/min** (sotto il target di 0.05€/min)

## Configurazione Voce Cartesia
- Modello: `sonic-2` (più veloce e naturale)
- Voce: scegliere tra voci italiane disponibili
- Velocità: 1.0x (naturale)
- Formato output: PCM 8kHz mono (Twilio requirement)

## Gestione Silenzi e Errori
- Se il chiamante non parla per 5 secondi: "Mi sente? Sono ancora qui."
- Se il chiamante non parla per 15 secondi: "Sembra che ci siano problemi di linea. La richiamo tra qualche minuto?"
- Se l'STT fallisce: fallback a risposta generica
- Se il TTS fallisce: invia messaggio WhatsApp con il contenuto

## Dati da Salvare (tabella `calls`)
- `lead_id`: ID del lead (se noto)
- `client_id`: ID del cliente
- `phone_number`: Numero chiamante
- `direction`: "inbound" | "outbound"
- `duration_seconds`: Durata chiamata
- `transcript`: Trascrizione completa
- `summary`: Riepilogo AI della chiamata
- `recording_url`: URL registrazione Twilio (se abilitata)
- `status`: "completed" | "missed" | "failed"
- `cost_eur`: Costo stimato della chiamata
