# Enhancement 001: Tägliche Zusammenfassung in einen Teams-Kanal pushen

Status: umgesetzt, Test im echten Kanal steht aus · Angelegt: 2026-10-08 · Issue: https://github.com/hanswurst1805/cp-knowledge-base/issues/1

## Ziel

Nach dem täglichen Lauf landet die Tageszusammenfassung automatisch in einem
Microsoft-Teams-Kanal. Wer im Kanal ist, sieht das Wichtigste, ohne die Seite
zu öffnen, und kommt mit einem Klick zur vollen Tagesseite.

## Umfang

- Nach `lauf` (nur wenn eine neue Tageszusammenfassung entstanden ist) eine
  Nachricht an den Kanal schicken.
- Inhalt: Datum, Zahl der Beiträge, die Punkte aus „Das Wichtigste“ mit ihren
  Links, ein Button „Ganze Zusammenfassung“ auf die Tagesseite.
- Optional, per Schalter: montags zusätzlich die Wochenzusammenfassung, am
  Monatsersten die Monatszusammenfassung.

## Technik

- Teams-Eingang über einen **Workflows-Webhook** (Power Automate, Vorlage
  „Post to a channel when a webhook request is received“). Die alten
  Office-365-Connector-Webhooks sind abgekündigt, also nicht dafür bauen.
- Payload: Adaptive Card (Version 1.4), verpackt als
  `{"type": "message", "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", "content": {...}}]}`.
- Markdown der Zusammenfassung auf die Teile reduzieren, die Adaptive Cards
  können (fett, Links, Listen). Ganze Tagesseite nicht in die Karte, die hat
  ein Größenlimit (~28 KB).
- Nur Standardbibliothek (`urllib`), wie der Rest.

## Konfiguration

| Variable | Bedeutung |
| --- | --- |
| `TEAMS_WEBHOOK_URL` | Workflows-Webhook des Kanals; leer = kein Push |
| `CMK_PUBLIC_URL` | Basis-URL des Digests für die Links, z. B. `https://daily.horstcase.de/checkmates` |
| `TEAMS_PERIODEN` | `1` = Wochen-/Monatszusammenfassung zusätzlich pushen |

## Fertig, wenn

- Ein Testlauf `python3 checkmates.py teams 2026-10-07` postet die Karte in
  einen Testkanal.
- Der tägliche Lauf postet genau einmal pro Tag, auch wenn er wiederholt wird
  (gemerkt in der Datenbank).
- Ein Fehler beim Push bricht den Lauf nicht ab, sondern steht im Log.
