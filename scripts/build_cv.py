#!/usr/bin/env python3
"""Render the CV PDF from the same JSON the site renders from.

`public/cv.pdf` is a build artefact, not a hand-maintained document: everything
in it comes from `src/data/*.json`, so the download and the page can never
disagree. Run after changing any of those files.

    python3 scripts/build_cv.py              # English -> public/cv.pdf
    python3 scripts/build_cv.py --lang es -o public/cv.es.pdf

Needs `weasyprint` on PATH (pip install weasyprint).
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data"
I18N = ROOT / "src" / "i18n"


def site_origin() -> str:
    """The deployed origin, read from `astro.config.mjs` so there is one copy.

    Self-hosted papers are stored as site-relative paths (`/papers/x.pdf`),
    which a PDF reader cannot resolve. They are absolutised against this.
    """
    config = (ROOT / "astro.config.mjs").read_text(encoding="utf-8")
    match = re.search(r"""site:\s*["']([^"']+)["']""", config)
    if not match:
        sys.exit("astro.config.mjs: no `site` declared; cannot absolutise links")
    return match.group(1).rstrip("/")


SITE = site_origin()


def ui_string(lang: str, key: str) -> str:
    """One UI string out of the site's own dictionary.

    The CV keeps its section headings in LABELS below, but a sentence the page
    also prints belongs in `src/i18n/` and nowhere else — two copies of it
    would drift the day one of them is edited.
    """
    strings = json.loads((I18N / f"{lang}.json").read_text(encoding="utf-8"))
    if key not in strings:
        sys.exit(f"src/i18n/{lang}.json: missing key {key!r}")
    return strings[key]


LABELS = {
    "en": {
        "roles": "Experience",
        "education": "Education",
        "teaching": "Teaching",
        "courses": "Courses taught",
        "publications": "Publications",
        "training": "Advanced training",
        "languages": "Languages",
        "groups": {
            "core": "Reduct computation",
            "radar": "Radar data processing",
            "teaching": "Engineering education",
        },
    },
    "es": {
        "roles": "Trayectoria",
        "education": "Formación",
        "teaching": "Docencia",
        "courses": "Asignaturas impartidas",
        "publications": "Publicaciones",
        "training": "Formación avanzada",
        "languages": "Idiomas",
        "groups": {
            "core": "Cómputo de reductos",
            "radar": "Procesamiento de datos de radar",
            "teaching": "Docencia en ingeniería",
        },
    },
}

CSS = """
@page { size: A4; margin: 16mm 15mm 14mm; }
* { box-sizing: border-box; }
body { font-family: "Inter", "DejaVu Sans", sans-serif; font-size: 9.2pt;
       line-height: 1.42; color: #15191c; margin: 0; }
h1 { font-size: 19pt; margin: 0; letter-spacing: -0.02em; }
.headline { font-size: 10pt; color: #4a5560; margin: 2px 0 0; }
.meta { font-size: 8pt; color: #4a5560; margin: 6px 0 0; }
.meta a { color: #0a7d5a; text-decoration: none; }
h2 { font-size: 8.4pt; text-transform: uppercase; letter-spacing: 0.12em;
     color: #0a7d5a; border-bottom: 0.6pt solid #c9d2d8;
     padding-bottom: 3px; margin: 16px 0 8px; }
.entry { margin: 0 0 9px; page-break-inside: avoid; }
.entry-head { display: flex; justify-content: space-between; gap: 10px; }
.role { font-weight: 600; }
.when { font-family: "JetBrains Mono", "DejaVu Sans Mono", monospace;
        font-size: 7.8pt; color: #4a5560; white-space: nowrap; }
.where { color: #4a5560; font-size: 8.6pt; margin: 1px 0 0; }
ul { margin: 4px 0 0; padding-left: 13px; }
li { margin: 0 0 2px; }
.note { color: #4a5560; font-size: 8.6pt; margin: 2px 0 0; }
.tags { font-size: 8.6pt; color: #30383f; margin: 0; }
.group { font-size: 8pt; font-weight: 600; color: #30383f; margin: 9px 0 4px; }
.pub { margin: 0 0 6px; page-break-inside: avoid; }
.pub .title { font-weight: 600; }
.pub .src { color: #4a5560; font-size: 8.4pt; }
a { color: #0a7d5a; }
"""


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def build(lang: str) -> str:
    L = LABELS[lang]
    profile = load("profile.json")
    exp = load("experience.json")
    pubs = load("publications.json")
    training = load("training.json")

    out: list[str] = []
    add = out.append

    add(f"<h1>{esc(profile['name'])}</h1>")
    add(f"<p class='headline'>{esc(profile['headline'][lang])}</p>")
    contact = [esc(profile["location"][lang]), f"<a href='mailto:{profile['email']}'>{profile['email']}</a>"]
    contact += [f"<a href='{l['url']}'>{esc(l['label'])}</a>" for l in profile["links"]]
    add("<p class='meta'>" + " · ".join(contact) + "</p>")

    add(f"<h2>{L['roles']}</h2>")
    for p in exp["positions"]:
        add("<div class='entry'>")
        add(
            "<div class='entry-head'><span class='role'>"
            f"{esc(p['role'][lang])}</span><span class='when'>{esc(p['dateLabel'][lang])}</span></div>"
        )
        add(f"<p class='where'>{esc(p['institution'])} · {esc(p['place'][lang])}</p>")
        # Figures first, then the prose, then the callout — the order the page
        # prints them in. Each of the three is optional and the list is only
        # opened if something went into it.
        bullets = [
            f"<li><strong>{esc(f['value'][lang])}</strong> — {esc(f['method'][lang])}</li>"
            for f in p.get("figures", [])
        ]
        bullets += [f"<li>{h}</li>" for h in p.get("highlights", {}).get(lang, [])]
        if p.get("stillRunning"):
            years = date.today().year - (p.get("to") or date.today().year)
            since = ui_string(lang, "experience.stillRunning.since").replace("{years}", str(years))
            claim = ui_string(lang, "experience.stillRunning")
            bullets.append(f"<li><strong>{esc(claim)}</strong> {esc(since)}</li>")
        if bullets:
            add("<ul>" + "".join(bullets) + "</ul>")
        add("</div>")

    add(f"<h2>{L['education']}</h2>")
    for e in exp["education"]:
        add("<div class='entry'>")
        add(
            "<div class='entry-head'><span class='role'>"
            f"{esc(e['degree'][lang])}</span><span class='when'>{esc(e['dateLabel'][lang])}</span></div>"
        )
        where = f"{esc(e['institution'])} · {esc(e['place'][lang])}"
        if e["field"][lang]:
            where += f" · {esc(e['field'][lang])}"
        add(f"<p class='where'>{where}</p>")
        if e["note"][lang]:
            add(f"<p class='note'>{e['note'][lang]}</p>")
        add("</div>")

    add(f"<h2>{L['teaching']}</h2>")
    courses = ", ".join(
        esc(c[lang]) + (f" ({esc(c['level'][lang])})" if c["level"][lang] else "")
        for c in exp["courses"]
    )
    add(f"<p class='tags'><strong>{L['courses']}:</strong> {courses}</p>")
    for h in exp["teachingHighlights"]:
        add("<div class='entry' style='margin-top:7px'>")
        add(
            "<div class='entry-head'><span class='role'>"
            f"{esc(h['course'][lang])}</span><span class='when'>{esc(h['dateLabel'][lang])}</span></div>"
        )
        add(f"<p class='where'>{esc(h['institution'])} · {esc(h['unit'][lang])}</p>")
        add(f"<p class='note'>{esc(h['detail'][lang])}</p>")
        add("<ul>" + "".join(f"<li>{esc(f[lang])}</li>" for f in h["facts"]) + "</ul>")
        add("</div>")

    add(f"<h2>{L['publications']}</h2>")
    for gid, glabel in L["groups"].items():
        items = sorted((p for p in pubs if p["group"] == gid), key=lambda p: -p["year"])
        if not items:
            continue
        add(f"<p class='group'>{glabel}</p>")
        for p in items:
            link = p["doi"] or p["pdf"]
            if link.startswith("/"):
                link = SITE + link
            title = f"<a href='{link}'>{esc(p['title'])}</a>" if link else esc(p["title"])
            src = f"<em>{esc(p['venue'])}</em>"
            if p["detail"]:
                src += f", {esc(p['detail'])}"
            add(
                f"<p class='pub'><span class='title'>{title}</span><br>"
                f"<span class='src'>{esc(', '.join(p['authors']))} — {src}, {p['year']}.</span></p>"
            )

    add(f"<h2>{L['training']}</h2><ul>")
    for c in training:
        add(f"<li>{esc(c['title'][lang])} — {esc(c['org'])}, {esc(c['place'][lang])}, {c['year']}.</li>")
    add("</ul>")

    add(f"<h2>{L['languages']}</h2><p class='tags'>{esc(profile['languageNote'][lang])}</p>")

    body = "\n".join(out)
    return (
        f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'>"
        f"<title>{esc(profile['name'])} — CV</title><style>{CSS}</style></head>"
        f"<body>{body}</body></html>"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lang", choices=("en", "es"), default="en")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()

    out = Path(args.out) if args.out else ROOT / "public" / "cv.pdf"
    doc = build(args.lang)
    tmp = out.with_suffix(".html")
    tmp.write_text(doc, encoding="utf-8")
    try:
        subprocess.run(["weasyprint", str(tmp), str(out)], check=True)
    except FileNotFoundError:
        print("weasyprint not found on PATH — pip install weasyprint", file=sys.stderr)
        return 1
    finally:
        tmp.unlink(missing_ok=True)
    print(f"{out} written ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
