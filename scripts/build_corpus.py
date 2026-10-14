#!/usr/bin/env python3
"""Build the retrieval corpus from what the site already publishes.

The rule the whole RAG hangs on is that an answer carries a citation and a
link, so a chunk that cannot be pointed at is useless. Every chunk here
therefore records the URL a reader can open to check it: a section anchor on
the site, or a PDF under /papers/. Nothing is extracted from `_material/`,
which is gitignored working material and not public.

Output: rag/corpus.json — committed, because it is derived from published
content and the Pages Function serves it from the bundle.

    python3 scripts/build_corpus.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data"
I18N = ROOT / "src" / "i18n"
PAPERS = ROOT / "public" / "papers"
OUT = ROOT / "rag" / "corpus.json"

LANGS = ("en", "es")

# Where each i18n key prefix lives on the page. A prefix that is not here is
# chrome (nav labels, button text) and is not worth retrieving.
ANCHORS = {
    "hero": "top",
    "about": "about",
    "research": "research",
    "system": "system",
    "projects": "projects",
    "experience": "experience",
    "contact": "contact",
}

# Chunks shorter than this are labels, not prose.
MIN_CHARS = 140
# A single i18n value shorter than this is a button or a column heading.
MIN_SENTENCE = 70
# Paper text is split into windows of this many characters, overlapping, so a
# passage that straddles a boundary is still retrievable whole from one side.
PAPER_WINDOW = 1400
PAPER_OVERLAP = 200


def plain(value: str) -> str:
    """Strip the inline markup the copy carries for `set:html`."""
    text = re.sub(r"<[^>]+>", " ", value)
    text = text.replace("&amp;", "&").replace("&nbsp;", " ")
    text = text.replace("&#215;", "x").replace("&rarr;", "->")
    return re.sub(r"\s+", " ", text).strip()


def url_for(lang: str, anchor: str) -> str:
    base = "/" if lang == "en" else "/es/"
    return f"{base}#{anchor}" if anchor else base


def localized(value, lang: str) -> str:
    """Read a `{en, es}` field, or pass a plain string through."""
    if isinstance(value, dict):
        return plain(str(value.get(lang, value.get("en", ""))))
    return plain(str(value))


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def i18n_chunks() -> list[dict]:
    """One chunk per key group: `system.stage.rf.*` together, `hero.*` together.

    Button and column labels live in the same namespace as the prose — a group
    swept up whole ends up containing the words "Source" and "Documentation" as
    if they were content, and a model will happily cite them as such. Only
    values long enough to be a sentence are kept; the group's heading is taken
    from its `.title` or `.name` key and used as the chunk title.
    """
    chunks: list[dict] = []
    for lang in LANGS:
        strings = json.loads((I18N / f"{lang}.json").read_text(encoding="utf-8"))
        groups: dict[str, dict[str, str]] = {}
        for key, value in strings.items():
            prefix = key.split(".")[0]
            if prefix not in ANCHORS:
                continue
            # Stages are substantial enough to retrieve one by one.
            group = ".".join(key.split(".")[:3]) if key.startswith("system.stage.") else prefix
            groups.setdefault(group, {})[key] = plain(value)

        for group, values in groups.items():
            heading = next(
                (v for k, v in values.items() if k.endswith((".title", ".name"))),
                group,
            )
            prose = [v for k, v in values.items() if len(v) >= MIN_SENTENCE]
            text = " ".join(prose)
            if len(text) < MIN_CHARS:
                continue
            chunks.append(
                {
                    "id": f"ui-{group}-{lang}",
                    "lang": lang,
                    "kind": "section",
                    "title": heading[:90],
                    "url": url_for(lang, ANCHORS[group.split(".")[0]]),
                    "text": f"{heading}. {text}",
                }
            )
    return chunks


def project_chunks() -> list[dict]:
    chunks = []
    for project in load("projects.json"):
        for lang in LANGS:
            parts = [
                localized(project["summary"], lang),
                localized(project["body"], lang),
            ]
            if project.get("note"):
                parts.append(localized(project["note"], lang))
            if project.get("outOfScope"):
                scope = project["outOfScope"].get(lang) or []
                parts.append("Out of scope: " + "; ".join(plain(s) for s in scope))
            parts.append("Stack: " + ", ".join(project["stack"]))
            parts.append(f"Years: {project['years']}. Status: {project['status']}.")
            chunks.append(
                {
                    "id": f"project-{project['id']}-{lang}",
                    "lang": lang,
                    "kind": "project",
                    "title": localized(project["title"], lang),
                    "url": url_for(lang, f"project-{project['id']}"),
                    "text": " ".join(p for p in parts if p),
                }
            )
    return chunks


def publication_chunks() -> list[dict]:
    chunks = []
    for i, pub in enumerate(load("publications.json")):
        link = pub.get("doi") or pub.get("pdf") or ""
        for lang in LANGS:
            parts = [
                localized(pub["title"], lang),
                ", ".join(pub.get("authors", [])),
                localized(pub.get("venue", ""), lang),
                str(pub.get("year", "")),
                localized(pub.get("abstract", ""), lang),
                localized(pub.get("detail", ""), lang),
            ]
            text = ". ".join(p for p in parts if p)
            if len(text) < MIN_CHARS:
                continue
            chunks.append(
                {
                    "id": f"pub-{i}-{lang}",
                    "lang": lang,
                    "kind": "publication",
                    "title": localized(pub["title"], lang),
                    "url": link or url_for(lang, "research"),
                    "text": text,
                }
            )
    return chunks


def experience_chunks() -> list[dict]:
    experience = load("experience.json")
    chunks = []
    for lang in LANGS:
        for i, item in enumerate(experience.get("education", [])):
            text = ". ".join(
                p
                for p in (
                    localized(item.get("degree", ""), lang),
                    localized(item.get("field", ""), lang),
                    item.get("institution", ""),
                    localized(item.get("place", ""), lang),
                    localized(item.get("dateLabel", ""), lang),
                    localized(item.get("note", ""), lang),
                )
                if p
            )
            chunks.append(
                {
                    "id": f"edu-{i}-{lang}",
                    "lang": lang,
                    "kind": "education",
                    "title": localized(item.get("degree", ""), lang),
                    "url": url_for(lang, "experience"),
                    "text": text,
                }
            )
        for i, pos in enumerate(experience.get("positions", [])):
            highlights = pos.get("highlights", {}).get(lang) or []
            text = ". ".join(
                p
                for p in (
                    localized(pos.get("role", ""), lang),
                    pos.get("institution", ""),
                    localized(pos.get("place", ""), lang),
                    localized(pos.get("dateLabel", ""), lang),
                    " ".join(plain(h) for h in highlights),
                )
                if p
            )
            chunks.append(
                {
                    "id": f"pos-{i}-{lang}",
                    "lang": lang,
                    "kind": "position",
                    "title": localized(pos.get("role", ""), lang),
                    "url": url_for(lang, "experience"),
                    "text": text,
                }
            )
        courses = experience.get("courses", [])
        if courses:
            text = " ".join(plain(str(c.get(lang, ""))) for c in courses)
            chunks.append(
                {
                    "id": f"courses-{lang}",
                    "lang": lang,
                    "kind": "teaching",
                    "title": "Courses taught" if lang == "en" else "Asignaturas impartidas",
                    "url": url_for(lang, "experience"),
                    "text": text,
                }
            )
        for i, item in enumerate(experience.get("teachingHighlights", [])):
            facts = item.get("facts") or []
            text = ". ".join(
                p
                for p in (
                    localized(item.get("course", ""), lang),
                    item.get("institution", ""),
                    localized(item.get("unit", ""), lang),
                    localized(item.get("dateLabel", ""), lang),
                    localized(item.get("detail", ""), lang),
                    " ".join(localized(f, lang) for f in facts),
                )
                if p
            )
            chunks.append(
                {
                    "id": f"teach-{i}-{lang}",
                    "lang": lang,
                    "kind": "teaching",
                    "title": localized(item.get("course", ""), lang),
                    "url": url_for(lang, "experience"),
                    "text": text,
                }
            )
    return [c for c in chunks if len(c["text"]) >= MIN_CHARS]


def profile_chunks() -> list[dict]:
    profile = load("profile.json")
    training = load("training.json")
    chunks = []
    for lang in LANGS:
        parts = [
            profile["name"],
            localized(profile["headline"], lang),
            localized(profile["location"], lang),
            profile["email"],
            localized(profile.get("languageNote", ""), lang),
            ". ".join(
                f"{localized(t['title'], lang)} ({t['org']}, {localized(t['place'], lang)}, {t['year']})"
                for t in training
            ),
        ]
        chunks.append(
            {
                "id": f"profile-{lang}",
                "lang": lang,
                "kind": "profile",
                "title": profile["name"],
                "url": url_for(lang, "contact"),
                "text": ". ".join(p for p in parts if p),
            }
        )
    return chunks


EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")


def redact(text: str) -> str:
    """Strip addresses out of paper text.

    A published paper prints its authors' institutional emails, so these are
    not secret — but a corpus an endpoint can recite from is a different thing
    from page 30 of a 2009 journal, and one of those addresses belongs to a
    co-author who did not sign up for it. The site's own contact address lives
    in the profile chunk, where it is deliberate.
    """
    return EMAIL.sub("[email removed]", text)


def guess_lang(text: str) -> str:
    es = sum(text.lower().count(w) for w in (" de ", " la ", " que ", " los ", " para "))
    en = sum(text.lower().count(w) for w in (" the ", " of ", " and ", " that ", " for "))
    return "es" if es > en else "en"


def paper_chunks() -> list[dict]:
    """Published PDFs only — the two under public/papers/, which anyone can open."""
    chunks = []
    for pdf in sorted(PAPERS.glob("*.pdf")):
        try:
            raw = subprocess.run(
                ["pdftotext", "-q", str(pdf), "-"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError) as err:
            print(f"  ! skipped {pdf.name}: {err}", file=sys.stderr)
            continue
        text = redact(re.sub(r"\s+", " ", raw).strip())
        lang = guess_lang(text)
        step = PAPER_WINDOW - PAPER_OVERLAP
        for i, start in enumerate(range(0, len(text), step)):
            window = text[start : start + PAPER_WINDOW]
            if len(window) < MIN_CHARS:
                continue
            chunks.append(
                {
                    "id": f"paper-{pdf.stem[:40]}-{i}",
                    # A paper is citable from either language of the site.
                    "lang": "*",
                    "kind": "paper",
                    "title": pdf.stem.replace("-", " "),
                    "url": f"/papers/{pdf.name}",
                    "text": window,
                }
            )
    return chunks


def check(chunks: list[dict]) -> int:
    """Fail if the committed corpus or index no longer matches the content.

    A corpus rebuilt without re-running the index would shift every row and
    make answers cite the wrong passage. The endpoint refuses the matrix when
    it detects that, so the damage is a dead feature rather than a wrong
    citation — but the place to catch it is here, before the push.
    """
    status = 0
    on_disk = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    if [c["id"] for c in on_disk] != [c["id"] for c in chunks] or on_disk != chunks:
        print("  corpus is stale — run: python3 scripts/build_corpus.py", file=sys.stderr)
        status = 1

    vectors_path = OUT.parent / "vectors.json"
    vectors = json.loads(vectors_path.read_text(encoding="utf-8")) if vectors_path.exists() else {}
    if vectors.get("ids") != [c["id"] for c in chunks]:
        print(
            "  index does not match the corpus — re-run POST /api/reindex (see rag/README.md)",
            file=sys.stderr,
        )
        status = 1
    if status == 0:
        print(f"  corpus and index agree: {len(chunks)} chunks")
    return status


def main() -> int:
    chunks: list[dict] = []
    for name, fn in (
        ("sections", i18n_chunks),
        ("projects", project_chunks),
        ("publications", publication_chunks),
        ("experience", experience_chunks),
        ("profile", profile_chunks),
        ("papers", paper_chunks),
    ):
        produced = fn()
        print(f"  {name:<14} {len(produced):>4}")
        chunks.extend(produced)

    if "--check" in sys.argv:
        return check(chunks)

    seen = {c["id"] for c in chunks}
    if len(seen) != len(chunks):
        print("duplicate chunk ids", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    total = sum(len(c["text"]) for c in chunks)
    print(f"  {'total':<14} {len(chunks):>4} chunks, {total / 1000:.0f}k chars -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
