# CP Knowledge Base

Holt täglich neue Beiträge aus ausgewählten Bereichen von CheckMates
(community.checkpoint.com), speichert sie in SQLite und fasst sie per
Sprachmodell zusammen: pro Tag, pro Woche, pro Monat. Daraus entsteht ein
HTML-Digest mit Übersichtsseite und Markdown-Download.

Quelle ist die öffentliche Khoros-API (`/api/2.0/search`, LiQL). Die Webseiten
selbst liegen hinter Cloudflare und werden nicht angefasst. Code nur mit der
Python-Standardbibliothek.

## Installation mit Podman

```bash
cp .env.example .env
vi .env                       # LLM_API_KEY, WEB_USERS, Pfade, Port
podman compose up -d --build  # oder: podman-compose up -d --build
```

Zwei Container:

| Container | Aufgabe |
| --- | --- |
| `app` | läuft dauerhaft, startet täglich um `CMK_UHRZEIT` den Lauf |
| `web` | Caddy, liefert den Digest mit Login (`WEB_USERS`) auf `CMK_WEB_PORT` aus |

Erster Abruf und Nachholen im laufenden Container:

```bash
podman compose exec app python3 checkmates.py nachholen 2026-09-01
podman compose exec app python3 checkmates.py lauf
podman compose logs -f app
```

## Installation ohne Container

```bash
cp .env.example .env && vi .env
python3 checkmates.py lauf
```

Täglich per cron, z. B. 07:00:

```
0 7 * * * cd /pfad/zu/cp-knowledge-base && /usr/bin/python3 checkmates.py lauf >> logs/lauf.log 2>&1
```

Ausliefern über ein vorhandenes nginx: `sudo deploy/einrichten.sh` (Pfade per
Umgebung anpassbar, siehe Kopf des Skripts), danach `CMK_WEB_DIR` in `.env`.

## Einstellungen

Vorgaben stehen in `config.toml`, alles Umgebungsspezifische in `.env`
(Vorlage mit allen Variablen: [.env.example](.env.example)).

| Variable | Bedeutung |
| --- | --- |
| `LLM_API_KEY` | API-Schlüssel (OpenRouter, OpenAI oder kompatibel) |
| `LLM_BASE_URL` | API-Basis, Standard `https://openrouter.ai/api/v1` |
| `LLM_MODELL` | Modell, Standard `anthropic/claude-sonnet-4` |
| `CMK_BEREICHE` | Bereich-IDs, kommagetrennt; leer = `config.toml` |
| `CMK_UHRZEIT` | Uhrzeit des täglichen Laufs im Container |
| `CMK_DATEN_DIR` / `CMK_WEB_DIR` | Datenordner und Webroot (ohne Container) |
| `CMK_DATEN_PFAD` / `CMK_WEB_PFAD` | Host-Ordner für die Volumes (Container) |
| `WEB_USERS` | Logins `name:passwort,name2:passwort2` |
| `CMK_UID` / `CMK_GID` | Nutzer, unter dem der App-Container läuft |
| `CMK_WEB_PORT` | Port der Webseite auf dem Host |
| `TEAMS_WEBHOOK_URL` | Teams-Workflows-Webhook; leer = kein Push |
| `TEAMS_PERIODEN` | `1` = montags Vorwoche, am 1. Vormonat zusätzlich schicken |
| `CMK_PUBLIC_URL` | Basis-URL des Digests für den Button in der Teams-Karte |

## Befehle

```bash
python3 checkmates.py lauf                   # abholen, Tag + Woche + Monat, Digest, Teams
python3 checkmates.py abholen                # nur abholen
python3 checkmates.py zusammenfassen 2026-10-08   # Vortag: 07.10. 00:00 bis 08.10. 00:00
python3 checkmates.py nachholen 2026-09-01   # ab Datum abholen, fehlende Tage zusammenfassen
python3 checkmates.py perioden               # Wochen-/Monatszusammenfassungen aktualisieren
python3 checkmates.py digest                 # HTML neu bauen
python3 checkmates.py teams 2026-10-07       # an Teams schicken (auch woche-2026-W40, monat-2026-09)
python3 checkmates.py teams 2026-10-07 --trocken   # nur Karte anzeigen
python3 checkmates.py bereiche               # alle Bereich-IDs
python3 checkmates.py dienst                 # Dauerbetrieb (Container)
```

## Ablage (unter `CMK_DATEN_DIR`)

| Pfad | Inhalt |
| --- | --- |
| `data/checkmates.db` | alle Beiträge, Abrufstand je Bereich |
| `zusammenfassungen/JJJJ-MM-TT.md` | Tageszusammenfassung |
| `zusammenfassungen/woche-JJJJ-Wnn.md`, `monat-JJJJ-MM.md` | Wochen- und Monatszusammenfassung |
| `digest/` | HTML-Seiten, `md/` mit den Markdown-Downloads |

## Teams

Ist `TEAMS_WEBHOOK_URL` gesetzt, schickt der tägliche Lauf die neue
Tageszusammenfassung als Karte in den Kanal: „Das Wichtigste“, die Bereiche und
ein Button auf die Tagesseite. Jeder Tag geht nur einmal raus (gemerkt in der
Datenbank); ein Fehler beim Senden bricht den Lauf nicht ab.

Webhook anlegen: im Teams-Kanal „Workflows“ → Vorlage „Post to a channel when a
webhook request is received“ → URL kopieren.

## Enhancements

- [001 Teams-Push der Tageszusammenfassung](docs/enhancements/001-teams-push.md) - Issue [#1](https://github.com/hanswurst1805/cp-knowledge-base/issues/1)
