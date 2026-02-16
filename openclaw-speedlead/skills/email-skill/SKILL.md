---
name: email-skill
description: >
  Gestisce email in arrivo e in uscita per vendite B2B italiane.
  Monitora la casella email del cliente, risponde ai lead via email,
  invia preventivi e follow-up automatici.
metadata:
  openclaw:
    requires:
      env:
        - SMTP_HOST
        - SMTP_USER
        - SMTP_PASS
        - IMAP_HOST
        - IMAP_USER
        - IMAP_PASS
        - SUPABASE_URL
        - SUPABASE_SERVICE_KEY
    primaryEnv: SMTP_USER
---

# Email Skill - Vendite B2B Italia

Gestisce tutta la comunicazione email per i lead commerciali.

## Quando Attivare

- Quando arriva una nuova email nella casella vendite
- Quando serve inviare un follow-up a un lead
- Quando il lead chiede informazioni via email
- Quando serve inviare materiale commerciale o preventivi

## Funzionalità

### 1. Monitoraggio Inbox
Controlla periodicamente (ogni 60 secondi) la casella IMAP per nuove email.
Filtra le email rilevanti (ignora spam, newsletter, notifiche automatiche).

### 2. Risposta Automatica Email
Quando arriva un'email da un potenziale cliente:

**Oggetto**: Re: [OGGETTO ORIGINALE]

```
Gentile [NOME],

grazie per averci contattato! Ho ricevuto la sua richiesta riguardo [ARGOMENTO].

[RISPOSTA PERSONALIZZATA IN BASE AL CONTENUTO]

Per poterle fare una proposta mirata, mi servirebbe capire:
- Qual è il volume/quantità che vi interessa?
- Entro quando vi servirebbe?
- Avete un budget di riferimento?

Se preferisce, possiamo organizzare una call veloce di 15 minuti.
Le propongo: [SLOT DISPONIBILI]

Cordiali saluti,
[NOME_AGENTE]
[AZIENDA]
[TELEFONO]
```

### 3. Invio Materiale Commerciale
Quando il lead chiede brochure, listino o preventivo:
- Recupera i documenti dalla configurazione del cliente
- Allega il materiale corretto
- Personalizza il messaggio di accompagnamento

### 4. Follow-up Email
Tempi per follow-up via email (più formali rispetto a WhatsApp):
- Dopo 24 ore: email di cortesia
- Dopo 3 giorni: proposta di call
- Dopo 7 giorni: invio caso studio o referenza
- Dopo 14 giorni: ultimo tentativo
- Dopo 30 giorni: archivio come COLD

### 5. Template Email

#### Prima Risposta (Lead da Sito)
```
Oggetto: [AZIENDA] - Risposta alla sua richiesta

Gentile [NOME],

mi chiamo [AGENTE] e mi occupo dello sviluppo commerciale per [AZIENDA].

Ho ricevuto la sua richiesta dal nostro sito web e volevo risponderle
subito personalmente.

[CONTENUTO PERSONALIZZATO]

Sarebbe disponibile per una breve call conoscitiva questa settimana?

Cordiali saluti,
[FIRMA]
```

#### Follow-up Dopo Call
```
Oggetto: Re: Riepilogo della nostra conversazione

Gentile [NOME],

grazie per il tempo dedicato oggi. Come discusso, ecco un riepilogo:

[PUNTI CHIAVE DELLA CONVERSAZIONE]

I prossimi passi sono:
1. [AZIONE 1]
2. [AZIONE 2]

Resto a disposizione per qualsiasi chiarimento.

Cordiali saluti,
[FIRMA]
```

## Regole di Stile Email
- Usare il "Lei" per default nelle email (più formale di WhatsApp)
- Oggetto email chiaro e specifico (mai generico)
- Firma professionale completa
- Mai troppo lunghe: max 200 parole per email
- Allegati nominati correttamente (es: "Preventivo_AcmeSrl_2026.pdf")
- Rispettare orari lavorativi (8:00-19:00 CET, lunedì-venerdì)
