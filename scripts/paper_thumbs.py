#!/usr/bin/env python3
"""paper_thumbs.py — render the first page of each paper as a WebP thumbnail.

A publication list is a list of claims; the first page of the paper is the
cheapest evidence there is, and it gives the section something to look at.
This renders page 1 of every paper in `src/data/publications.json` for which a
source is known, writes `public/img/papers/<slug>.webp`, and records the path
back on the entry as `thumb`.

    python3 scripts/paper_thumbs.py            # render what is missing
    pnpm papers:thumbs --force                 # re-render everything
    pnpm papers:thumbs --dry-run

Sources live in SOURCES below, keyed by the publication title. Most of them are
author manuscripts under `_material/`, which is gitignored: the PDFs are not in
the repo, the rendered thumbnails are. That is the same deal as the CV and the
corpus — the artefact is committed, the material it came from is not. Re-running
this on a clean checkout without `_material/` will skip those entries and say so
rather than fail.

Open-access sources may be given as a URL. They are downloaded into a fresh
directory and passed to `pdftoppm` by path; nothing is executed from it.

Requires poppler (`pdftoppm`) and Pillow. Neither runs in CI by design — see
CLAUDE.md §11 on why poppler is not a build dependency.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "data" / "publications.json"
OUT_DIR = ROOT / "public" / "img" / "papers"
PUBLIC_PREFIX = "/img/papers"

# Render well above display size, then downsample — a page of 9pt text turned
# into 320px by the PDF rasteriser directly is mush.
RENDER_DPI = 150
TARGET_WIDTH = 320
QUALITY = 78

# Fetching an open-access PDF; a default urllib agent is refused by some hosts.
USER_AGENT = "Mozilla/5.0 (compatible; paper-thumbs/1.0; +https://vladimir.ladetec.com)"

# title -> (slug, source) or (slug, source, page). Source is a repo-relative
# path or an http(s) URL; page defaults to 1. Redalyc prepends a cover sheet
# carrying the authors' institutional e-mail addresses, so those entries ask for
# page 2 — the thumbnail should show the paper, and a co-author's address is not
# ours to republish (CLAUDE.md §7).
SOURCES: dict[str, tuple[str, str] | tuple[str, str, int]] = {
    "MinReduct: A new algorithm for computing the shortest reducts": (
        "rodriguez-2020-patrec-minreduct",
        "_material/doctorado/JCR/shortest_rg.pdf",
    ),
    "A new algorithm for reduct computation based on gap elimination and attribute contribution": (
        "rodriguez-2018-infsci-gcreduct",
        "_material/doctorado/JCR/GCreduct_researchgate.pdf",
    ),
    "A fast hardware software platform for computing irreducible testors": (
        "rodriguez-2015-eswa-hw-sw-testors",
        "_material/doctorado/JCR/eswa.pdf",
    ),
    "A Comparative Study of Two Algorithms for Computing the Shortest Reducts: MiLIT and MinReduct": (
        "rodriguez-2021-mcpr-milit-minreduct",
        "_material/doctorado/Congress/MCPR2021_paper_44.pdf",
    ),
    "The Impact of Basic Matrix Dimension on the Performance of Algorithms for Computing Typical Testors": (
        "rodriguez-2018-mcpr-basic-matrix",
        "_material/doctorado/Congress/MCPR2018_paper_20.pdf",
    ),
    "Fast-BR vs. Fast-CT_EXT: An Empirical Performance Study": (
        "rodriguez-2017-mcpr-fastbr-fastctext",
        "_material/doctorado/Congress/MCPR_2017_paper_35.pdf",
    ),
    "A hardware architecture for filtering irreducible testors": (
        "rodriguez-2014-reconfig-filtering-testors",
        "_material/doctorado/Congress/ReConFig_2014_submission_15.pdf",
    ),
    "Simulador de radar meteorológico basado en modelo de reflectividades en el espacio": (
        "rodriguez-2012-energetica-simulador-radar",
        "https://dialnet.unirioja.es/descarga/articulo/3961094.pdf",
    ),
    "Data processing in weather radars revisited": (
        "rodriguez-2010-erad-data-processing-weather-radars",
        "public/papers/rodriguez-2010-erad-data-processing-weather-radars.pdf",
    ),
    "Instrumento virtual con acceso local y remoto para prácticas de Ingeniería del Control": (
        "rodriguez-2015-rielac-instrumento-virtual",
        "https://dialnet.unirioja.es/descarga/articulo/5695796.pdf",
    ),
    "Automatización integral del proceso de secado de bioproductos": (
        "rodriguez-2015-rielac-secado-bioproductos",
        "https://dialnet.unirioja.es/descarga/articulo/5695784.pdf",
    ),
    "Aplicación de algoritmos de control clásico, adaptable y robusto a sistemas dinámicos de parámetros variables": (
        "rodriguez-2012-energetica-control-parametros-variables",
        "https://www.redalyc.org/pdf/3291/329127751002.pdf",
        2,
    ),
    "Software para el procesamiento de los ensayos de la máquina sincrónica": (
        "rodriguez-2009-energetica-ensayos-maquina-sincronica",
        "public/papers/rodriguez-2009-energetica-ensayos-maquina-sincronica.pdf",
    ),
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="paper_thumbs.py",
        description="Render the first page of each publication as a WebP thumbnail.",
    )
    parser.add_argument(
        "-f", "--force", action="store_true",
        help="re-render thumbnails that already exist",
    )
    parser.add_argument(
        "-n", "--dry-run", action="store_true",
        help="report what would happen; write nothing",
    )
    parser.add_argument(
        "-w", "--width", type=int, default=TARGET_WIDTH,
        help=f"thumbnail width in px (default: {TARGET_WIDTH})",
    )
    return parser.parse_args(argv)


def fetch(url: str, into: Path) -> Path:
    """Download `url` into its own empty directory and return the file path."""
    target = into / "source.pdf"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        head = response.read(5)
        if head != b"%PDF-":
            raise ValueError(f"not a PDF (starts with {head!r})")
        with target.open("wb") as handle:
            handle.write(head)
            shutil.copyfileobj(response, handle)
    return target


def render(pdf: Path, out: Path, width: int, page_no: int = 1) -> tuple[int, int]:
    """Rasterise one page of `pdf` and write `out` as WebP. Returns (w, h)."""
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "page"
        subprocess.run(
            ["pdftoppm", "-f", str(page_no), "-l", str(page_no), "-r", str(RENDER_DPI),
             "-png", "-singlefile", str(pdf), str(prefix)],
            check=True, capture_output=True,
        )
        with Image.open(prefix.with_suffix(".png")) as page:
            page = page.convert("RGB")
            height = round(page.height * width / page.width)
            page = page.resize((width, height), Image.LANCZOS)
            out.parent.mkdir(parents=True, exist_ok=True)
            page.save(out, "WEBP", quality=QUALITY, method=6)
            return width, height


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if shutil.which("pdftoppm") is None:
        print("error: pdftoppm not found — install poppler-utils", file=sys.stderr)
        return 1

    publications = json.loads(DATA.read_text(encoding="utf-8"))
    rendered = skipped = missing = 0

    for entry in publications:
        known = SOURCES.get(entry["title"])
        if known is None:
            continue
        slug, source, page_no = (*known, 1)[:3]
        out = OUT_DIR / f"{slug}.webp"
        entry["thumb"] = f"{PUBLIC_PREFIX}/{slug}.webp"

        if out.exists() and not args.force:
            skipped += 1
            continue

        if args.dry_run:
            print(f"would render  {source}  ->  {out.relative_to(ROOT)}")
            rendered += 1
            continue

        try:
            if source.startswith(("http://", "https://")):
                with tempfile.TemporaryDirectory() as download_dir:
                    pdf = fetch(source, Path(download_dir))
                    size = render(pdf, out, args.width, page_no)
            else:
                pdf = ROOT / source
                if not pdf.exists():
                    print(f"missing      {source}  (source not on this machine)")
                    missing += 1
                    continue
                size = render(pdf, out, args.width, page_no)
        except Exception as error:  # noqa: BLE001 — report and keep going
            print(f"failed       {source}: {error}", file=sys.stderr)
            missing += 1
            continue

        print(f"rendered     {out.relative_to(ROOT)}  {size[0]}x{size[1]}  "
              f"{out.stat().st_size / 1024:.0f} KB")
        rendered += 1

    # Only write back the entries whose thumbnail actually exists, so a run on a
    # machine without `_material/` cannot point the site at a file it has not got.
    for entry in publications:
        thumb = entry.get("thumb")
        if thumb and not (ROOT / "public" / thumb.lstrip("/")).exists():
            del entry["thumb"]

    if not args.dry_run:
        DATA.write_text(
            json.dumps(publications, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"\n{rendered} rendered, {skipped} already present, {missing} unavailable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
