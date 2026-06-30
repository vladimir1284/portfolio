#!/usr/bin/env python3
"""optimize_images.py — convert raster images to WebP for the web.

Walks the given files/directories, encodes every JPG/JPEG/PNG it finds as a
sibling `.webp`, and reports the size saved. Optionally caps the largest
dimension (handy for avatars/thumbnails) and deletes the originals.

Usage:
    python3 scripts/optimize_images.py [paths...] [options]
    pnpm optimize:images public/assets/img/testimonials --max 256 --delete

Paths default to `public/` when none are given. Each path may be a single
image or a directory (directories are walked recursively).

Options:
    -q, --quality <1-100>  WebP quality (default: 80)
    -m, --max <px>         Downscale so the longest side is at most <px>
                           (never upscales; omit to keep original size)
    -d, --delete           Remove the source file after a successful encode
    -f, --force            Re-encode even if the .webp is newer than the source
    -n, --dry-run          Report what would happen; write nothing

Requires Pillow:  pip install Pillow
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SOURCE_EXT = {".jpg", ".jpeg", ".png"}
DEFAULT_PATHS = ["public"]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="optimize_images.py",
        description="Convert JPG/PNG images to WebP for the web.",
    )
    parser.add_argument(
        "paths", nargs="*", default=DEFAULT_PATHS,
        help='files or directories to process (default: "public")',
    )
    parser.add_argument("-q", "--quality", type=int, default=80, help="WebP quality 1-100 (default: 80)")
    parser.add_argument("-m", "--max", type=int, default=None, help="cap the longest side at <px> (never upscales)")
    parser.add_argument("-d", "--delete", action="store_true", help="delete the source after a successful encode")
    parser.add_argument("-f", "--force", action="store_true", help="re-encode even when the .webp is up to date")
    parser.add_argument("-n", "--dry-run", action="store_true", help="report only; write nothing")
    opts = parser.parse_args(argv)

    if not 1 <= opts.quality <= 100:
        parser.error(f"--quality must be between 1 and 100 (got {opts.quality})")
    if opts.max is not None and opts.max < 1:
        parser.error(f"--max must be a positive number (got {opts.max})")
    return opts


def collect(path: Path) -> list[Path]:
    """Recursively gather convertible image files from a path."""
    if path.is_dir():
        return sorted(
            p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in SOURCE_EXT
        )
    if path.suffix.lower() in SOURCE_EXT:
        return [path]
    return []


def up_to_date(src: Path, dest: Path) -> bool:
    """True when dest exists and is newer than src (so we can skip it)."""
    return dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime


def format_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


def main(argv: list[str]) -> int:
    opts = parse_args(argv)

    try:
        from PIL import Image
    except ImportError:
        print("Missing dependency 'Pillow'. Install it with: pip install Pillow", file=sys.stderr)
        return 1

    # Resolve, dedupe, and validate the requested paths up front.
    seen: set[Path] = set()
    files: list[Path] = []
    for raw in opts.paths:
        path = Path(raw)
        if not path.exists():
            print(f"Path not found: {raw}", file=sys.stderr)
            return 1
        for f in collect(path):
            if f not in seen:
                seen.add(f)
                files.append(f)

    if not files:
        print("No JPG/PNG images found.")
        return 0

    extras = []
    if opts.max:
        extras.append(f"max {opts.max}px")
    if opts.dry_run:
        extras.append("dry-run")
    suffix = f" ({', '.join(extras)})" if extras else ""
    print(f"Optimizing {len(files)} image(s) → WebP (quality {opts.quality}){suffix}\n")

    total_in = total_out = converted = skipped = 0

    for src in files:
        dest = src.with_suffix(".webp")
        if not opts.force and up_to_date(src, dest):
            skipped += 1
            print(f"  skip   {src} (webp up to date)")
            continue

        in_bytes = src.stat().st_size

        if opts.dry_run:
            print(f"  would  {src} → {dest}")
            total_in += in_bytes
            continue

        with Image.open(src) as im:
            # Drop alpha for opaque sources; keep it (RGBA) when the image has it.
            if im.mode in ("P", "LA", "RGBA"):
                im = im.convert("RGBA")
            elif im.mode != "RGB":
                im = im.convert("RGB")

            if opts.max and max(im.size) > opts.max:
                # thumbnail() preserves aspect ratio and never upscales.
                im.thumbnail((opts.max, opts.max), Image.LANCZOS)

            im.save(dest, "WEBP", quality=opts.quality, method=6)

        # Match the source mtime so subsequent runs can skip cleanly.
        os.utime(dest, (src.stat().st_atime, src.stat().st_mtime))

        out_bytes = dest.stat().st_size
        total_in += in_bytes
        total_out += out_bytes
        converted += 1
        pct = (in_bytes - out_bytes) / in_bytes * 100
        print(f"  ok     {src} → {dest}  {format_bytes(in_bytes)} → {format_bytes(out_bytes)} (-{pct:.0f}%)")

        if opts.delete:
            src.unlink()

    print()
    if opts.dry_run:
        print(f"Dry run: {len(files) - skipped} image(s) would be converted.")
    else:
        summary = f"Done: {converted} converted, {skipped} skipped."
        if converted:
            saved = (total_in - total_out) / total_in * 100
            summary += f"  {format_bytes(total_in)} → {format_bytes(total_out)} (-{saved:.0f}%)."
        print(summary)
        if opts.delete and converted:
            print("Source files deleted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
