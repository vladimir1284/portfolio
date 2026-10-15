# Developer & AI Agent Instructions — Personal Portfolio

Personal portfolio site for Vladímir Rodríguez — developer, researcher, PhD in Computer Science. Read fully before editing. Visual/design rules live in [DESIGN.md](./DESIGN.md); this file owns stack, structure, i18n, and workflow.

Repo: `https://github.com/vladimir1284/portfolio` · single-package Astro site, static output.

---

## 1. Stack & Environment

| Tool         | Required                                                    |
| :----------- | :---------------------------------------------------------- |
| Node.js      | `>=22.12.0` (see `package.json` → `engines`)                |
| pnpm         | active package manager                                      |
| Astro        | `^6.4.6`                                                    |
| Tailwind CSS | `^4.3.1`, via `@tailwindcss/vite` (no `tailwind.config.js`) |

- **Package manager is `pnpm`** — do not introduce `npm`/`yarn` lockfiles. Commit `pnpm-lock.yaml`.

**Commands** (from repo root):

```bash
pnpm install      # install deps
pnpm dev          # dev server → http://localhost:4321
pnpm build        # production build → ./dist/
pnpm preview      # serve built ./dist/ locally
pnpm astro ...    # CLI, e.g. `pnpm astro check`
pnpm optimize:images [paths] [--max <px>] [--delete]   # convert raster assets to WebP (see §10)
pnpm build:cv     # regenerate public/cv.pdf and public/cv.es.pdf from src/data/
pnpm corpus       # rebuild rag/corpus.json from src/data and src/i18n (see §11)

# Quality gate — run before committing/pushing
pnpm verify       # lint + format check + astro check + corpus check + build + internal link crawl
pnpm verify:full  # same, but also validates external links (slow, flaky)
```

`astro.config.mjs` declares **no `output`** and **no adapter** — fully static output to `dist/`.

---

## 2. Project Structure

```
src/
├── layouts/Layout.astro      # <html>/<head>, SEO+i18n head, fonts, theme flash, <slot/>
├── pages/
│   ├── index.astro           # English route  →  /  (default locale, unprefixed)
│   ├── 404.astro             # redirects unknown routes to /
│   └── es/index.astro        # Spanish route  →  /es/
├── i18n/
│   ├── en.json               # English UI strings
│   ├── es.json               # Spanish UI strings (same keys as en.json)
│   ├── ui.ts                 # i18n config + UIKey type + parity guard
│   └── utils.ts              # resolveLang, useTranslations, otherLang, getRouteFromPathname
├── components/               # section components (see §5)
│   ├── lamula/stages.ts      # LAMULA processing chain, as data (System.astro)
│   └── ask/faq.ts            # fallback questions for the Ask section (see §11)
├── data/
│   ├── projects.json         # portfolio projects / case studies
│   ├── publications.json     # academic publications (grouped: core | radar | teaching)
│   ├── experience.json       # education, courses, professional positions
│   ├── training.json         # ICTP workshops and advanced training
│   ├── profile.json          # name, headline, location, email, social links
│   └── types.ts              # shapes for the JSON files
└── styles/global.css         # Tailwind import + design tokens + custom classes
public/                       # static assets (favicon, avatar, radar still as .webp, cv.pdf)
scripts/optimize_images.py    # JPG/PNG → WebP converter (see §10)
scripts/build_cv.py           # src/data/*.json → public/cv{,.es}.pdf (`pnpm build:cv`)
scripts/build_headers.py      # dist/_headers for Cloudflare Pages — CSP hashes (see §9)
scripts/build_corpus.py       # src/data + src/i18n → rag/corpus.json (`pnpm corpus`)
scripts/reindex_vectors.py    # rebuild rag/vectors.json through the deployed site (§11)
functions/_middleware.ts      # 301s the pages.dev hostname to the custom domain (§9)
functions/api/                # Pages Functions — /api/ask, /api/reindex (see §11)
rag/                          # generated corpus + vector index (see rag/README.md)
wrangler.toml                 # Pages config — output dir and the `AI` binding
_material/                    # gitignored working material (CV, thesis, reference code)
```

Both page routes import the **same component set**; they differ only by locale. Keep in sync — if you add/remove a section, update **both** `index.astro` files.

---

## 3. Sections / Content

Single-page layout, sections in order:

| Section    | Component          | Content                                                                                                                           |
| :--------- | :----------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| Hero       | `Hero.astro`       | Name, tagline, short bio, CTAs, radar still + link to the live viewer.                                                            |
| Facts      | `Facts.astro`      | Six figures under the hero, each with the method that makes it defensible.                                                        |
| System     | `System.astro`     | Tabbed walkthrough of the LAMULA radar chain, autoplaying until the reader clicks a stage. Data in `components/lamula/stages.ts`. |
| About      | `About.astro`      | Photo, extended bio, current role/institution, research interests.                                                                |
| Research   | `Research.astro`   | Research lines, key publications (from `data/publications.json`).                                                                 |
| Projects   | `Projects.astro`   | Cards from `data/projects.json`: title, stack tags, links (demo/GitHub).                                                          |
| Experience | `Experience.astro` | Timeline: positions, institutions, dates.                                                                                         |
| Ask        | `Ask.astro`        | Retrieval over the site's own content. Degrades to a static question list (§11).                                                  |
| Contact    | `Contact.astro`    | Email + social links from `data/profile.json`. No form backend.                                                                   |
| Header     | `Header.astro`     | Fixed nav: name/logo, section anchors, theme toggle, language switcher.                                                           |
| Footer     | `Footer.astro`     | Copyright, social icons.                                                                                                          |

---

## 4. Internationalization (EN / ES)

Routing is **Astro's built-in i18n**, configured in `astro.config.mjs`:

```js
site: 'https://YOUR_DOMAIN_HERE', // update before deploy
i18n: {
  defaultLocale: 'en',
  locales: ['en', 'es'],
  routing: { prefixDefaultLocale: false }, // / = English, /es/ = Spanish
},
```

### Rules

- **Never** put literal copy in components — all UI strings go in `en.json` / `es.json`.
- **Never** use inline ternaries (`locale === 'es' ? … : …`) for copy.
- `t(key)` falls back to the default-locale value if a key is missing.
- The parity guard (`es satisfies Record<UIKey, string>` in `ui.ts`) fails `astro check` if `es.json` is missing a key.
- Every new user-facing string gets a key in **both** `en.json` and `es.json`.

**Consume strings** in any component:

```astro
---
import { resolveLang, useTranslations } from "../i18n/utils";
const lang = resolveLang(Astro.currentLocale);
const t = useTranslations(lang);
---

<h1>{t("hero.name")}</h1>
```

Rich text (inline `<strong>` etc.) → store as HTML string, render with `set:html`.

### Data-driven content

`data/projects.json` and `data/publications.json` hold structured data. For bilingual field values, use a `{ en, es }` object per field:

```json
{ "title": { "en": "My Project", "es": "Mi Proyecto" }, "year": 2024 }
```

Components index into `title[lang]`.

---

## 5. Theme & Flash Prevention

- Dark by default: `Layout.astro` renders `<html lang={lang} class="dark">`.
- An **inline `is:inline` script** in `<head>` reads `localStorage.theme` and toggles `.dark` before paint. Do not move, defer, or remove it.
- Theme toggle lives in `Header.astro`.
- All color decisions go through semantic tokens in `styles/global.css`. Never hardcode raw colors.

---

## 6. Components Reference

All components: `resolveLang(Astro.currentLocale)` → `useTranslations(lang)` → `t('key')`. No literal strings in markup.

| Component          | Responsibility                                                                            |
| :----------------- | :---------------------------------------------------------------------------------------- |
| `Layout.astro`     | `<head>`: title/description, canonical + hreflang, OG/Twitter tags, fonts, theme script.  |
| `Header.astro`     | Fixed nav: name, section anchors, theme toggle, language switcher.                        |
| `Hero.astro`       | Name, tagline, bio summary, CV download, radar still linking out to the live viewer.      |
| `Facts.astro`      | Etched fact band. Counts what it can from `publications.json`; see DESIGN.md §4.          |
| `System.astro`     | LAMULA chain walkthrough. CSS-driven (radio + `:has()`); JS only autoplays the selection. |
| `About.astro`      | Photo, extended bio, research interests, current affiliation.                             |
| `Research.astro`   | Research lines + key publications from `data/publications.json`.                          |
| `Projects.astro`   | Cards from `data/projects.json` with stack tags and links.                                |
| `Experience.astro` | Vertical timeline of roles and institutions.                                              |
| `Contact.astro`    | Email + social links from `data/profile.json`. No form backend.                           |
| `Footer.astro`     | Copyright, social icons.                                                                  |

---

## 7. Known Stubs & Gotchas

### Standing rules

- **Every figure needs a method.** No metric ships unless it can be defended in an interview. `~/Documents/cv.md` is LLM-generated and is **not** a content source.
- **`public/cv.pdf` and `public/cv.es.pdf` are build artefacts**, not documents. `pnpm build:cv` regenerates both from `src/data/*.json`, so the download can never contradict the page. Never edit them by hand; never hand-maintain a parallel CV.
- **Contact details live in `src/data/profile.json`** — one source for `Contact.astro` and the CV generator.
- **Contact section has no form** — just links. No backend needed.
- **No unit-test suite.** Run `pnpm verify` + manual pass over `/` and `/es/` (light and dark) before pushing.
- Both `pages/index.astro` and `pages/es/index.astro` must stay in sync.
- `_material/` is gitignored reference material, and is excluded from `tsconfig.json`, Prettier and ESLint. Do not publish anything from it without the licence check in `_material/radar-hero/{LICENSE,NOTICE,TRADEMARKS.md}`.
- **Documentation sites belong to stages, repositories to projects.** The six published mkdocs sites live in `components/lamula/stages.ts` as `docs`, rendered by hostname, so they must stay under `ladetec.com`. Old code (Meteorología, the Nitza `gestor` and VoIP repos) is described but never linked — Vladímir's call.
- **A screenshot is evidence, so it carries the same burden as a figure.** Client pricing, margins, names and contact details are blurred before the image is converted, and the untouched original stays in `_material/originales/capturas/`. The caption says what was obscured and why — hiding the redaction would be worse than not shipping the screenshot. Seeded or demo data is not evidence and does not ship at all.
- **Nothing carrying a phone number or a third party's personal data goes in the repo root** — it is published. `_material/originales/` holds the sources Vladímir supplied.

### Pending

- **`pnpm optimize:images` does not run in the dev container.** Pillow is not
  installed and pip refuses to install it (PEP 668, externally managed). The
  WebP conversions shipped so far were done with ImageMagick
  (`convert <in> -resize 1600x1600\> -quality 80 <out>`), which is equivalent
  for static images. Fix by adding Pillow to `ghcr.io/vladimir1284/vscode-swarm-env`
  rather than by rewriting the script.
- **`public/img/radar-loop.gif` is unoptimised** — 2.0 MB, 960×484, 12 frames,
  and it is the hero's eager image, so it is the LCP (DESIGN.md §7 budget:
  < 1.5 s on simulated 4G). Two things to do when the toolchain is back:
  re-export the loop at ~1600 px wide, and convert it to animated WebP
  (`cwebp`/`img2webp`, not ImageMagick, which rebuilds the animation badly).
  The reduced-motion fallback `radar-loop-still.webp` is the GIF's last frame
  and already carries the right dimensions; update `Hero.astro` when the path
  changes.
- **The legend of the runtime-vs-density plot is wrong, and stays wrong.** The
  figure is `public/img/projects/reducts-runtime-density.webp` (Figure 5.1 of the
  thesis, chapter 5, page 61). Its legend spells `CGreduct`; the correct name is
  **`GCreduct`**, as the thesis body, the site and `publications.json` all have
  it. Confirmed by Vladímir as an error in the figure. It ships as defended and
  the caption says the legend is wrong — repainting a defended figure to look
  tidier would be the worse of the two options.

---

## 8. Quality Gate (`pnpm verify`)

Run locally before pushing. CI enforces it on every push/PR.

| Step | Command             | Catches                                              |
| :--- | :------------------ | :--------------------------------------------------- |
| 1    | `pnpm lint`         | ESLint errors.                                       |
| 2    | `pnpm format:check` | Unformatted files. Fix: `pnpm format`.               |
| 3    | `pnpm check`        | `.astro`/TS errors, i18n key-parity guard.           |
| 4    | `pnpm corpus:check` | A retrieval corpus or vector index gone stale (§11). |
| 5    | `pnpm build`        | Broken pages, bad imports, missing assets.           |
| 6    | `pnpm verify:links` | Broken internal links (needs `dist/` already built). |

`pnpm verify:full` additionally validates external links and caps concurrency at
4 — Dialnet drops parallel requests and reports them as `[0]`. Its config skips
two hosts, both measured rather than assumed:

- `researchgate.net` — 403s every bot.
- `repositorioinstitucional.buap.mx` — the thesis record. Measured 2026-10-14:
  the item page does return 200, but takes over 45 s with a browser user agent
  and never answers at all with curl's default one, and the repository root
  answers 502. The link is kept because it is the official record and there is
  no alternative; if BUAP's repository stays this slow, that is worth revisiting.

`vladimir.ladetec.com` used to be skipped too, because it did not resolve; it
does now, so the site's own canonical and hreflang targets are checked like any
other link.

---

## 9. Deployment

Static output to **Cloudflare Pages**, published by the `deploy` job in
`.github/workflows/verify.yml`. That job hangs off `needs: verify`, so the tree
that ships is the tree the gate passed, and it only fires on a push to `master`.

It needs two repository secrets — `CLOUDFLARE_API_TOKEN` (scope: `Cloudflare
Pages: Edit`) and `CLOUDFLARE_ACCOUNT_ID` — and a Pages project named
`vladimir-portfolio`. Until both secrets exist the job's first step stops it
with a `::notice` instead of failing: a push should not go red over a setup step
that is known to be pending. The `secrets` context is not readable from a
job-level `if`, which is why the gate is a step and not a condition on the job.

Both secrets are set, the project exists, and CI has published to it — the first
production deployment is `0db825f`. The setup below is recorded for a rebuild, not
because it is pending.

An **account-owned** API token is rejected by `GET /user/tokens/verify` with
`Invalid API Token` even when it is valid; verify it against
`/accounts/<id>/pages/projects` instead. `wrangler login` needs a browser and so
cannot be driven by an agent, but it is not required: one API token covers both the
CI secret and any local wrangler call.

```bash
# with CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID exported
wrangler pages project create vladimir-portfolio --production-branch master
pnpm build && wrangler pages deploy dist --project-name vladimir-portfolio
```

### The custom domain

`vladimir.ladetec.com` is attached and serving, and `astro.config.mjs` declares it
as `site`, so canonical, hreflang, `og:url` and the sitemap all point at it.

Attaching it from Pages works because the `ladetec.com` zone lives in the same
Cloudflare account — six other Pages projects already serve subdomains of it. The
API call that attaches a domain does **not** write the DNS record, though, and the
deploy token has no DNS permission by design, so the `CNAME` to
`vladimir-portfolio.pages.dev` was created by hand in the dashboard. Leave the
token as `Cloudflare Pages: Edit` — it lives in GitHub Actions.

`vladimir-portfolio.pages.dev` still answers, and `functions/_middleware.ts`
redirects it to the custom domain with a 301 so only one hostname is canonical.
Pages' `_redirects` file cannot do this: it matches paths, not hostnames. The
match is the project hostname exactly, which leaves per-deployment hostnames
(`<hash>.vladimir-portfolio.pages.dev`) reachable for inspecting one deployment;
Cloudflare already serves those with `x-robots-tag: noindex`.

Root middleware runs for static assets as well as for `/api/*`, so every request
is now a Functions invocation — 100 000 a day on the free plan. Verified on a
throwaway project before it shipped: `_headers` is still applied to what `next()`
returns, so the CSP is not lost.

One thing the orange cloud adds: Cloudflare injects its own inline challenge
script (`window.__CF$cv$params`) into proxied HTML. It carries a per-request ray
id, so no static hash can ever match it and the CSP blocks it. Nothing on the
page depends on it — all five of the site's own inline scripts match their
hashes — but it is why the console shows one CSP violation on a proxied origin
and none on `.pages.dev`.

**Wrangler is deliberately not a dependency.** It pulls ~500 packages and a
`workerd` binary; CI uses `cloudflare/wrangler-action`, which brings its own, and
the setup above is a one-off. Run it with `pnpm dlx`, not `pnpm add`.

### Response headers

`dist/_headers` is **generated**, by `scripts/build_headers.py`, as the last
step of `pnpm build`. Cloudflare Pages reads that file and serves what it says.

It carries a Content-Security-Policy with **sha256 hashes of every inline
`<script>` and `<style>` in the built output** — the theme-flash script in
`Layout.astro` has to run before paint, so it cannot be externalised, and
`'unsafe-inline'` would have made the policy decorative. The hashes are
recomputed from `dist/` on every build, which is exactly why the file is not
hand-written in `public/`: a stale hash blocks the script that prevents the
flash, and nothing on the page would say so.

The policy allows `fonts.googleapis.com` (stylesheet) and `fonts.gstatic.com`
(font files), and nothing else off-origin. **`connect-src` is `'self'`** — the
Phase 5 RAG endpoint will need its origin added there before any fetch works.

Verified against the live origin: `vladimir-portfolio.pages.dev` serves the
policy, and the sha256 hashes in it match the inline scripts in the HTML Pages
actually returns, so the theme-flash script runs rather than being silently
blocked. Re-check the browser console after any change to an inline script.

`packageManager` in `package.json` pins pnpm, and the workflow's
`pnpm/action-setup` steps read it rather than hardcoding a version — CI and the
working copy must run the same package manager. `pnpm.onlyBuiltDependencies`
lists `esbuild` and `sharp`, the two dependencies that legitimately need an
install script; pnpm 10+ errors out instead of ignoring them silently.

---

## 10. Image Optimization

Raster assets in `public/` ship as **WebP**. Converter: `scripts/optimize_images.py` (Python 3 + Pillow).

```bash
pnpm optimize:images                            # everything under public/
pnpm optimize:images public/img/projects --max 1200 --delete
pnpm optimize:images public/img/avatar --max 512 --delete
```

- `--quality <1-100>` (default 80), `--max <px>` downscales (never upscales), `--delete` removes source.
- **References not rewritten automatically** — update `data/*.json` paths after converting.

---

## 11. Ask — retrieval over the site's own content

`Ask.astro` puts a question box between Experience and Contact. It posts to
`/api/ask`, a **Cloudflare Pages Function** in `functions/api/`, which embeds
the question, scores it against `rag/vectors.json`, and asks a model to answer
from the passages it found.

**It is a Pages Function and not a separate Worker on purpose.** Same origin
means the CSP stays `connect-src 'self'`, there is no CORS, and no second
hostname has to be attached or kept in sync with the custom domain. It deploys
with the site, from the same `wrangler pages deploy`.

**The rule, which is the whole feature:** an answer carries a citation and a
link, or it is not shown. `/api/ask` rejects a model response with no citation
marker, retries once with a correction, and then gives up. Every failure path
returns `ok: false` with a reason, never an error status, and the page shows
the questions in `src/components/ask/faq.ts` — answered from the page itself,
with no model involved. A visitor never sees a stack trace.

The model is told not to compute figures. This is not a style preference: an
earlier prompt let it turn "teaching since 2008" into "about 15 years", which
is both wrong and exactly the kind of undefendable number §7 bans.

### Keeping it honest

- **The corpus is generated**, by `scripts/build_corpus.py`, from `src/data/`
  and the two i18n dictionaries. Every chunk carries the URL that proves it.
  Edit content, then run `pnpm corpus`; `pnpm verify` fails if you forget.
- **The index must be rebuilt with the corpus.** `rag/vectors.json` is row-
  aligned to `rag/corpus.json`; a corpus rebuilt alone would shift every row
  and make answers cite the wrong passage. `_rag.ts` compares the id lists at
  startup and refuses the matrix if they disagree, which degrades to the
  fallback instead of citing wrongly. `pnpm corpus:check` catches it earlier,
  and also compares a sha256 over the ids **and** the text: editing the copy
  behind an id leaves the rows lined up perfectly while the vectors describe
  wording that is no longer on the page, which no id comparison can see.
- **Rebuilding the index needs no new permission.** Workers AI is reached
  through the `AI` binding declared in `wrangler.toml`, which needs no token
  at all — the deploy token has `Cloudflare Pages: Edit` and nothing else, and
  it should stay that way. `/api/reindex` is closed unless `RAG_ADMIN_SECRET`
  is set on the project; production does not set it. Run
  `python3 scripts/reindex_vectors.py` and read its docstring first: Pages
  only shows environment changes to _new_ deployments, so the order matters.
- **Paper text is committed, not re-extracted.** `pdftotext` is not on the CI
  runner and should not be: poppler versions disagree about whitespace, so the
  same PDF would extract differently on two machines and the check would fail
  over nothing. `rag/papers.lock.json` holds each PDF's sha256; without
  `pdftotext` the build reuses the committed chunks while the hashes match, and
  stops rather than guess when one has changed.
- **Everything under `public/papers/` is in the corpus, the thesis included.**
  That is three PDFs and 148 of the 228 chunks, 126 of them the thesis — it
  ships, so it is indexed, and `/api/ask` cites it by page. Nothing in
  `_material/` is ever indexed: it does not ship, so a citation into it would
  point at a file no reader can open.

### Budget, on the free allowance

10 000 neurons/day. At the published rates for
`@cf/meta/llama-3.1-8b-instruct-fp8-fast` (4119 neurons per million input
tokens, 34868 per million output), an answer of roughly 2000 input and 300
output tokens costs about **19 neurons — around 500 answers a day**. Embedding
the question with `@cf/baai/bge-m3` costs 0.05 of one. There is no Vectorize
usage at all: 102 chunks at 1024 dimensions are 108 KB of int8 scored with a
dot product per row, which is cheaper than the round trip to a managed index.

Past the allowance Workers AI refuses, `/api/ask` answers `ok: false`, and the
page shows the fallback. A per-IP limit of 10 questions a minute sits in front,
on the Cache API; it races by construction and is there for casual hammering,
not for a determined attacker.
