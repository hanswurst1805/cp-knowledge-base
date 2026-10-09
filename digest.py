"""HTML-Digest aus den Tageszusammenfassungen: eine Seite pro Tag plus Übersicht.

Liest zusammenfassungen/JJJJ-MM-TT.md und schreibt digest/JJJJ-MM-TT.html und
digest/index.html. Wird bei jedem Lauf komplett neu gebaut.
"""

import datetime as dt
import html
import re
from pathlib import Path

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

CSS = """
:root{--bg:#F5F9F6;--surface:#FFFFFF;--sunken:#EEF4F0;--border:#DBE6DF;--text:#121712;
--text2:#56635B;--muted:#8A968E;--green:#176B41;--green-h:#1E8A54;--green-100:#E2F1E7;
--green-050:#EFF7F1;--code:#EEF4F0;--shadow:0 1px 2px rgba(18,23,18,.05),0 4px 14px rgba(18,23,18,.05)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0D1310;--surface:#141B16;
--sunken:#101613;--border:#263029;--text:#E9F1EB;--text2:#A3B0A6;--muted:#77857B;--green:#4CC886;
--green-h:#3FBE7C;--green-100:#1B3226;--green-050:#16261C;--code:#1B231E;--shadow:none}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text2);font:14px/1.6 Arial,"Helvetica Neue",Helvetica,sans-serif}
.wrap{max-width:860px;margin:0 auto;padding:32px 16px 64px}
a{color:var(--green);text-decoration:none}a:hover{color:var(--green-h);text-decoration:underline}
.label{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font-size:34px;font-weight:900;letter-spacing:-.01em;color:var(--text);margin:6px 0 4px;line-height:1.15}
h2{font-size:21px;font-weight:800;color:var(--text);margin:0 0 12px}
h3{font-size:16px;font-weight:700;color:var(--text);margin:16px 0 8px}
strong{color:var(--text)}
code{background:var(--code);border-radius:6px;padding:1px 5px;font-size:13px;font-family:Menlo,Consolas,monospace}
.meta{color:var(--muted);margin-bottom:24px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;box-shadow:var(--shadow);
padding:20px 24px;margin:0 0 16px;overflow-wrap:anywhere}
.card.top{background:var(--green-050);border-color:var(--green-100)}
ul,ol{padding-left:20px;margin:6px 0}li{margin:4px 0}li>ul,li>ol{margin:4px 0 8px}
p{margin:8px 0}
nav.tage{display:flex;justify-content:space-between;gap:12px;margin:0 0 20px;flex-wrap:wrap}
nav.tage a{border:1px solid var(--border);background:var(--surface);border-radius:8px;padding:6px 12px}
.liste{list-style:none;padding:0;margin:0}
.liste li{margin:0 0 12px}
.liste a.tag{display:block;background:var(--surface);border:1px solid var(--border);border-radius:14px;
box-shadow:var(--shadow);padding:16px 20px;color:var(--text2)}
.liste a.tag:hover{text-decoration:none;border-color:var(--green);background:var(--green-050)}
.liste .datum{font-size:16px;font-weight:700;color:var(--text)}
.liste .zahl{float:right;font-size:12px;color:var(--muted)}
.liste ul{margin:6px 0 0;padding-left:18px}
.leer{color:var(--muted)}
h2.abschnitt{margin:28px 0 12px}
.raster{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,360px),1fr));gap:16px;margin-bottom:16px}
.raster.liste li{margin:0}.raster>.card{margin:0}
.kurz{list-style:none;padding:0;margin:0}.kurz li{margin:0 0 6px}.kurz span{color:var(--muted);font-size:12px}
"""


def inline(text):
    teile = re.split(r"(`[^`]+`)", text)
    aus = []
    for t in teile:
        if t.startswith("`") and t.endswith("`") and len(t) > 1:
            aus.append(f"<code>{html.escape(t[1:-1])}</code>")
            continue
        t = html.escape(t, quote=False)
        t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                   lambda m: f'<a href="{html.escape(m[2])}" target="_blank" rel="noopener">{m[1]}</a>', t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        aus.append(t)
    return "".join(aus)


def markdown(md):
    """Kleiner Markdown-Konverter für genau das, was die Zusammenfassung liefert."""
    aus, stapel, absatz = [], [], []  # stapel: [(einrueckung, "ul"/"ol")]

    def absatz_schliessen():
        if absatz:
            aus.append(f"<p>{inline(' '.join(absatz))}</p>")
            absatz.clear()

    def listen_schliessen(bis=-1):
        while stapel and stapel[-1][0] > bis:
            aus.append(f"</li></{stapel.pop()[1]}>")

    for zeile in md.splitlines():
        if not zeile.strip():
            absatz_schliessen()
            continue
        m = re.match(r"^( *)([-*]|\d+\.) +(.*)$", zeile)
        if m:
            absatz_schliessen()
            tiefe, art = len(m[1]), "ol" if m[2][0].isdigit() else "ul"
            listen_schliessen(tiefe)
            if stapel and stapel[-1][0] == tiefe:
                aus.append("</li><li>")
            else:
                stapel.append((tiefe, art))
                aus.append(f"<{art}><li>")
            aus.append(inline(m[3]))
            continue
        h = re.match(r"^(#{1,4}) +(.*)$", zeile)
        if h:
            absatz_schliessen()
            listen_schliessen()
            n = len(h[1])
            aus.append(f"<h{n}>{inline(h[2])}</h{n}>")
            continue
        if stapel:
            if zeile.startswith(" "):  # eingerückter Absatz gehört zum aktuellen Listenpunkt
                aus.append(f"<p>{inline(zeile.strip())}</p>")
                continue
            listen_schliessen()
        absatz.append(zeile.strip())
    absatz_schliessen()
    listen_schliessen()
    return "\n".join(aus)


def zerlegen(md):
    """-> (meta_zeile, [(überschrift, markdown_abschnitt)])"""
    zeilen = md.splitlines()
    meta = next((z for z in zeilen[1:] if z.strip() and not z.startswith("#")), "")
    abschnitte, aktuell = [], None
    for z in zeilen:
        if z.startswith("## "):
            aktuell = [z[3:].strip(), []]
            abschnitte.append(aktuell)
        elif aktuell:
            aktuell[1].append(z)
    return meta, [(t, "\n".join(r)) for t, r in abschnitte]


def schoenes_datum(tag):
    d = dt.date.fromisoformat(tag)
    return f"{WOCHENTAGE[d.weekday()]}, {d:%d.%m.%Y}"


def seite(titel, inhalt):
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(titel)}</title><style>{CSS}</style></head>
<body><div class="wrap">
{inhalt}
</div></body></html>
"""


def kernpunkte(abschnitt_md, n=3):
    punkte = []
    for z in abschnitt_md.splitlines():
        m = re.match(r"^[-*] +(.*)$", z)
        if m:
            fett = re.match(r"\*\*(.+?)\*\*", m[1])
            punkte.append(fett[1].rstrip(" :.") if fett else re.sub(r"\[[^\]]+\]\([^)]+\)", "", m[1])[:140])
    return punkte[:n]


HERVORGEHOBEN = ("das wichtigste", "trends")


def titel_aus(md, fallback):
    erste = md.splitlines()[0] if md else ""
    return erste[2:].replace("CheckMates ", "").strip() if erste.startswith("# ") else fallback


def detailseiten(eintraege, ziel, anzeige, label):
    """eintraege: [(schluessel, md)] aufsteigend -> schreibt Seiten, liefert Index-Daten."""
    daten = []
    (ziel / "md").mkdir(exist_ok=True)
    for i, (key, md) in enumerate(eintraege):
        (ziel / "md" / f"{key}.md").write_text(re.sub(r"<!-- (tage: .*?|zwischenstand) -->\n\n", "", md), encoding="utf-8")
        meta, abschnitte = zerlegen(md)
        name = anzeige(key, md)
        vor = eintraege[i - 1][0] if i > 0 else None
        nach = eintraege[i + 1][0] if i + 1 < len(eintraege) else None
        nav = ['<nav class="tage">',
               f'<a href="{vor}.html">← {anzeige(vor, eintraege[i-1][1])}</a>' if vor else "<span></span>",
               '<a href="index.html">Übersicht</a>',
               f'<a href="{nach}.html">{anzeige(nach, eintraege[i+1][1])} →</a>' if nach else "<span></span>",
               "</nav>"]
        karten = []
        for titel, inhalt in abschnitte:
            klasse = "card top" if titel.lower().startswith(HERVORGEHOBEN) else "card"
            karten.append(f'<section class="{klasse}"><h2>{inline(titel)}</h2>{markdown(inhalt)}</section>')
        (ziel / f"{key}.html").write_text(seite(
            f"CheckMates {name}",
            f'<div class="label">CheckMates {label}</div><h1>{html.escape(name)}</h1>'
            f'<div class="meta">{html.escape(meta)} · '
            f'<a href="md/{key}.md" download="checkmates-{key}.md">Markdown herunterladen</a></div>'
            + "\n".join(nav) + "\n" + "\n".join(karten)),
            encoding="utf-8")
        wichtig = next((a for t, a in abschnitte if t.lower().startswith("das wichtigste")), "")
        bereiche = [t for t, _ in abschnitte if not t.lower().startswith(HERVORGEHOBEN + ("offen geblieben",))]
        daten.append((key, name, meta, kernpunkte(wichtig), bereiche))
    return daten


def karte(key, name, meta, punkte, bereiche, label=None):
    oben = f'<div class="label">{html.escape(label)}</div>' if label else ""
    return (f'<li><a class="tag" href="{key}.html">{oben}<span class="zahl">{html.escape(meta.split(",")[0])}</span>'
            f'<span class="datum">{html.escape(name)}</span>'
            f'<div class="label">{html.escape(" · ".join(bereiche))}</div>'
            f'<ul>{"".join(f"<li>{inline(p)}</li>" for p in punkte)}</ul></a></li>')


def kurzliste(daten):
    return '<ul class="kurz">' + "".join(
        f'<li><a href="{k}.html"><strong>{html.escape(n)}</strong></a> <span>{html.escape(m)}</span></li>'
        for k, n, m, _, _ in reversed(daten)) + "</ul>"


def bauen(quelle: Path, ziel: Path):
    ziel.mkdir(exist_ok=True)
    lesen = lambda muster: sorted((p.stem, p.read_text(encoding="utf-8")) for p in quelle.glob(muster))
    tage = detailseiten(lesen("????-??-??.md"), ziel, lambda k, md: schoenes_datum(k), "Tag")
    wochen = detailseiten(lesen("woche-*.md"), ziel, lambda k, md: titel_aus(md, k), "Woche")
    monate = detailseiten(lesen("monat-*.md"), ziel, lambda k, md: titel_aus(md, k), "Monat")

    teile = []
    aktuell = []
    if monate:
        aktuell.append(karte(*monate[-1], label="Monat"))
    if wochen:
        aktuell.append(karte(*wochen[-1], label="Woche"))
    if aktuell:
        teile.append(f'<h2 class="abschnitt">Aktuell</h2><ul class="liste raster">{"".join(aktuell)}</ul>')
    if len(wochen) > 1 or len(monate) > 1:
        teile.append('<div class="raster">'
                     + (f'<section class="card"><h2>Wochen</h2>{kurzliste(wochen)}</section>' if wochen else "")
                     + (f'<section class="card"><h2>Monate</h2>{kurzliste(monate)}</section>' if monate else "")
                     + "</div>")
    if tage:
        teile.append('<h2 class="abschnitt">Tage</h2><ul class="liste">'
                     + "\n".join(karte(*d) for d in reversed(tage)) + "</ul>")
    else:
        teile.append('<p class="leer">Noch keine Zusammenfassungen.</p>')
    (ziel / "index.html").write_text(seite(
        "CheckMates Digest",
        f'<div class="label">CP Knowledge Base</div><h1>CheckMates Digest</h1>'
        f'<div class="meta">{len(tage)} {"Tag" if len(tage) == 1 else "Tage"}, {len(wochen)} Wochen, '
        f'{len(monate)} {"Monat" if len(monate) == 1 else "Monate"}</div>' + "\n".join(teile)), encoding="utf-8")
    print(f"Digest: {ziel / 'index.html'} ({len(tage)} Tage, {len(wochen)} Wochen, {len(monate)} Monate)")
