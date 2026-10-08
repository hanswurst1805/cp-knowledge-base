"""Zusammenfassung als Adaptive Card an einen Teams-Kanal schicken.

Eingang ist ein Teams-Workflows-Webhook ("Post to a channel when a webhook
request is received"). Die Karte enthält "Das Wichtigste" (bei Wochen und
Monaten zusätzlich "Trends") und einen Button auf die ganze Seite.
"""

import json
import re
import urllib.request

MAX_BYTES = 25_000  # Teams-Limit liegt bei ~28 KB pro Nachricht


def _abschnitt(md, name):
    m = re.search(rf"^## {name}\s*\n(.*?)(?=^## |\Z)", md, re.M | re.S | re.I)
    return m[1] if m else ""


def _punkte(abschnitt):
    """Oberste Listenpunkte eines Abschnitts, für Teams-Markdown bereinigt."""
    punkte = []
    for zeile in abschnitt.splitlines():
        m = re.match(r"^[-*] +(.*)$", zeile)
        if m:
            punkte.append(m[1].replace("`", "").strip())
    return punkte


def karte(md, titel, seiten_url=None):
    zeilen = md.splitlines()
    meta = next((z for z in zeilen[1:] if z.strip() and not z.startswith(("#", "<!--"))), "")
    body = [
        {"type": "TextBlock", "text": "CheckMates Digest", "size": "Small", "weight": "Bolder",
         "color": "Good", "spacing": "None"},
        {"type": "TextBlock", "text": titel, "size": "Large", "weight": "Bolder", "wrap": True,
         "spacing": "Small"},
        {"type": "TextBlock", "text": meta, "isSubtle": True, "wrap": True, "spacing": "None"},
    ]
    for name in ("Das Wichtigste", "Trends"):
        punkte = _punkte(_abschnitt(md, name))
        if not punkte:
            continue
        body.append({"type": "TextBlock", "text": name, "weight": "Bolder", "spacing": "Medium",
                     "separator": True})
        body += [{"type": "TextBlock", "text": f"• {p}", "wrap": True, "spacing": "Small"}
                 for p in punkte]
    bereiche = [t for t in re.findall(r"^## (.+)$", md, re.M)
                if t.lower() not in ("das wichtigste", "trends", "offen geblieben")]
    if bereiche:
        body.append({"type": "TextBlock", "text": "Bereiche: " + " · ".join(bereiche),
                     "isSubtle": True, "wrap": True, "size": "Small", "spacing": "Medium"})
    inhalt = {"$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
              "type": "AdaptiveCard", "version": "1.4", "msteams": {"width": "Full"}, "body": body}
    if seiten_url:
        inhalt["actions"] = [{"type": "Action.OpenUrl", "title": "Ganze Zusammenfassung",
                              "url": seiten_url}]
    nachricht = {"type": "message", "attachments": [
        {"contentType": "application/vnd.microsoft.card.adaptive", "contentUrl": None, "content": inhalt}]}
    # zu groß: von hinten Punkte weglassen, bis es passt
    while len(json.dumps(nachricht).encode()) > MAX_BYTES:
        punkte = [i for i, b in enumerate(body) if b["text"].startswith("• ")]
        if not punkte:
            break
        body.pop(punkte[-1])
    return nachricht


def senden(webhook_url, nachricht):
    req = urllib.request.Request(webhook_url, data=json.dumps(nachricht).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        if r.status >= 300:
            raise RuntimeError(f"Teams-Webhook: HTTP {r.status}")
        return r.status
