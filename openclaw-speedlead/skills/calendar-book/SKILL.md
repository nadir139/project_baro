---
name: calendar-book
description: >
  Prenota appuntamenti sul calendario per i lead qualificati.
  Supporta Cal.com e Google Calendar. Propone slot disponibili,
  conferma la prenotazione e invia reminder.
metadata:
  openclaw:
    requires:
      env:
        - CALCOM_API_KEY
      config: []
    primaryEnv: CALCOM_API_KEY
---

# Calendar Booking - Prenotazione Appuntamenti

Gestisce la prenotazione di appuntamenti commerciali per lead qualificati.

## Quando Attivare

- Quando un lead HOT è pronto per un appuntamento
- Quando il lead chiede "quando possiamo sentirci?"
- Quando serve proporre slot disponibili
- Quando bisogna confermare, modificare o cancellare un appuntamento

## Processo di Prenotazione

### 1. Verifica Disponibilità
Controlla i prossimi 5 giorni lavorativi per slot disponibili.
Orari preferiti: 9:00-12:30 e 14:00-18:00 (CET), lunedì-venerdì.

### 2. Proponi Slot
Proponi 3 opzioni al lead:

```
Perfetto [NOME]! Ecco quando possiamo organizzare una call:

📅 Opzione 1: [GIORNO] alle [ORA]
📅 Opzione 2: [GIORNO] alle [ORA]
📅 Opzione 3: [GIORNO] alle [ORA]

Quale preferisci? O se hai un altro orario in mente, dimmi pure!
```

### 3. Conferma Prenotazione
Dopo la scelta del lead:

```
Perfetto! Ho prenotato:
📅 [GIORNO] [DATA] alle [ORA]
⏱ Durata: 30 minuti
📍 Call su [Google Meet / Teams / telefono]

Ti invio il link e un reminder 1 ora prima. A presto! 💪
```

### 4. Notifica al Venditore Umano
Invia messaggio WhatsApp al titolare/venditore:

```
📅 NUOVO APPUNTAMENTO
Lead: [NOME] ([AZIENDA])
Data: [DATA] alle [ORA]
Score: [SCORE]/100
Note: [RIEPILOGO QUALIFICAZIONE]
Canale originale: [whatsapp/email/telefono]
```

### 5. Reminder Automatici
- 24 ore prima: reminder via email
- 1 ora prima: reminder via WhatsApp
- 5 minuti prima: reminder al venditore umano

## Integrazione Cal.com

Usa l'API Cal.com per:
- `GET /availability` - Controlla slot disponibili
- `POST /bookings` - Crea prenotazione
- `PATCH /bookings/:id` - Modifica prenotazione
- `DELETE /bookings/:id` - Cancella prenotazione

## Integrazione Google Calendar (alternativa)

Se configurato con Google Calendar:
- Usa Google Calendar API v3
- Service account per accesso server-side
- Crea evento con Google Meet link automatico

## Gestione Modifiche

Se il lead vuole spostare:
```
Nessun problema! Ecco le alternative disponibili:
[NUOVI SLOT]
```

Se il lead vuole cancellare:
```
Capisco, nessun problema. Se cambi idea o vuoi riprogrammare,
scrivimi pure! Resto a disposizione.
```

## Dati da Salvare

Per ogni appuntamento, salva in Supabase (tabella `bookings`):
- `lead_id`: ID del lead
- `client_id`: ID del cliente
- `scheduled_at`: Data/ora appuntamento
- `duration_minutes`: Durata (default 30)
- `meeting_type`: "call" | "video" | "in_person"
- `meeting_url`: Link alla videochiamata
- `status`: "confirmed" | "rescheduled" | "cancelled" | "completed"
- `notes`: Note per il venditore
- `external_id`: ID su Cal.com o Google Calendar
