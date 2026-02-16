---
name: speed-to-lead
description: >
  Riceve lead da webhook (sito web, fiere, landing page) e risponde immediatamente
  su WhatsApp in italiano. Qualifica il lead (budget, urgenza, decisore) e prenota
  appuntamento. Obiettivo: risposta in meno di 20 secondi.
metadata:
  openclaw:
    requires:
      env:
        - SUPABASE_URL
        - SUPABASE_SERVICE_KEY
      config:
        - whatsapp.enabled
    primaryEnv: SUPABASE_SERVICE_KEY
---

# Speed-to-Lead

Skill principale per la gestione rapida dei lead B2B in italiano.

## Quando Attivare

Attiva questa skill quando:
- Ricevi una notifica di nuovo lead da webhook
- Un nuovo contatto scrive su WhatsApp per la prima volta
- Arriva un'email da un potenziale cliente
- Viene segnalato un lead da una fiera o evento

## Processo

### 1. Ricezione Lead (< 5 secondi)
Quando arriva un nuovo lead:
- Registra immediatamente il lead su Supabase (tabella `leads`)
- Identifica il canale di arrivo (whatsapp, email, telefono, web_form)
- Recupera la configurazione del cliente (settore, prodotti, listino)

### 2. Primo Contatto (< 20 secondi dal ricevimento)
Invia subito un messaggio WhatsApp personalizzato:

```
Ciao [NOME]! 👋 Sono [NOME_AGENTE] di [AZIENDA].
Ho visto che hai [AZIONE - es: compilato il form / visitato lo stand / richiesto info su X].
Posso aiutarti subito! Di cosa hai bisogno esattamente?
```

### 3. Qualificazione (BANT Italiano)
Raccogli queste informazioni attraverso la conversazione naturale:
- **Budget**: "Per avere un'idea del range, avete già un budget definito per questo progetto?"
- **Autorità**: "Sei tu a gestire direttamente questo tipo di acquisti o c'è qualcun altro coinvolto?"
- **Necessità**: "Raccontami meglio cosa state cercando e perché ora"
- **Tempistica**: "Entro quando vi servirebbe? È urgente?"

Dopo ogni risposta, aggiorna il campo `qualification_score` del lead (0-100).

### 4. Classificazione Lead
- **HOT (score > 70)**: Budget confermato, decisore, urgente → Prenota subito appuntamento
- **WARM (score 40-70)**: Interesse reale ma mancano info → Continua qualificazione
- **COLD (score < 40)**: Solo curiosità → Invia materiale informativo e pianifica follow-up

### 5. Booking Appuntamento (per lead HOT)
Quando il lead è caldo:
- Usa la skill `calendar-book` per proporre slot disponibili
- Conferma data e ora
- Invia reminder su WhatsApp 1 ora prima
- Notifica il titolare/venditore umano via WhatsApp

### 6. Notifica Titolare
Per ogni lead HOT, invia notifica immediata al titolare:

```
🔥 LEAD CALDO - [NOME LEAD]
Azienda: [AZIENDA_LEAD]
Settore: [SETTORE]
Budget: [BUDGET]
Urgenza: [ALTA/MEDIA/BASSA]
Appuntamento: [DATA/ORA o "da fissare"]
Canale: [whatsapp/telefono/email]
```

## Gestione Obiezioni Comuni

- "Quanto costa?" → "Dipende dalle tue esigenze specifiche, per questo vorrei capire meglio cosa vi serve. Possiamo fare una call veloce di 15 minuti?"
- "Mandami un preventivo via email" → "Certo! Per farti un preventivo preciso ho bisogno di capire 2-3 cose. Posso farti qualche domanda veloce?"
- "Non sono il decisore" → "Capisco perfettamente. Chi è la persona che gestisce questo tipo di decisioni? Posso contattarlo direttamente o preferisci coinvolgerlo tu?"
- "Non ho tempo ora" → "Nessun problema! Quando ti farebbe comodo? Ti propongo [SLOT] - anche solo 10 minuti per capire se possiamo aiutarvi."
- "Sto valutando altri fornitori" → "Ottimo che stiate valutando bene! Proprio per questo vi conviene sentire anche la nostra proposta. Quando possiamo fare un confronto veloce?"

## Tono e Stile
- Italiano naturale, mai tradotto dall'inglese
- Professionale ma amichevole (dare del "tu" o del "Lei" in base al contesto)
- Diretto e orientato all'azione
- Mai aggressivo o insistente
- Usa il nome del lead sempre
- Emoji con moderazione (solo WhatsApp)

## Dati da Salvare su Supabase

Per ogni interazione, aggiorna:
- `leads.status` (new, contacted, qualifying, qualified, booked, lost)
- `leads.qualification_score` (0-100)
- `leads.qualification_data` (JSON con BANT)
- `conversations` (ogni messaggio scambiato)
- `leads.next_action` e `leads.next_action_at` (per follow-up programmati)

## Follow-up Automatici

Programma follow-up se il lead non risponde:
- Dopo 2 ore: "Ciao [NOME], tutto bene? Volevo solo assicurarmi che avessi ricevuto il mio messaggio 😊"
- Dopo 24 ore: "Buongiorno [NOME]! Ti riscrivo perché [MOTIVO ORIGINALE]. Hai avuto modo di pensarci?"
- Dopo 3 giorni: "Ciao [NOME], ultima volta che ti disturbo! Se cambi idea sai dove trovarmi 👋"
- Dopo 7 giorni: segna come COLD e smetti di contattare
