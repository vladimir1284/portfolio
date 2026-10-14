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

# Quality gate — run before committing/pushing
pnpm verify       # lint + format check + astro check + build + internal link crawl
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
│   └── lamula/stages.ts      # LAMULA processing chain, as data (System.astro)
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
_material/                    # gitignored working material (CV, thesis, reference code)
```

Both page routes import the **same component set**; they differ only by locale. Keep in sync — if you add/remove a section, update **both** `index.astro` files.

---

## 3. Sections / Content

Single-page layout, sections in order:

| Section    | Component          | Content                                                                                   |
| :--------- | :----------------- | :---------------------------------------------------------------------------------------- |
| Hero       | `Hero.astro`       | Name, tagline, short bio, CTAs, radar still + link to the live viewer.                    |
| System     | `System.astro`     | Interactive walkthrough of the LAMULA radar chain. Data in `components/lamula/stages.ts`. |
| About      | `About.astro`      | Photo, extended bio, current role/institution, research interests.                        |
| Research   | `Research.astro`   | Research lines, key publications (from `data/publications.json`).                         |
| Projects   | `Projects.astro`   | Cards from `data/projects.json`: title, stack tags, links (demo/GitHub).                  |
| Experience | `Experience.astro` | Timeline: positions, institutions, dates.                                                 |
| Contact    | `Contact.astro`    | Email + social links from `data/profile.json`. No form backend.                           |
| Header     | `Header.astro`     | Fixed nav: name/logo, section anchors, theme toggle, language switcher.                   |
| Footer     | `Footer.astro`     | Copyright, social icons.                                                                  |

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

| Component          | Responsibility                                                                           |
| :----------------- | :--------------------------------------------------------------------------------------- |
| `Layout.astro`     | `<head>`: title/description, canonical + hreflang, OG/Twitter tags, fonts, theme script. |
| `Header.astro`     | Fixed nav: name, section anchors, theme toggle, language switcher.                       |
| `Hero.astro`       | Name, tagline, bio summary, CV download, radar still linking out to the live viewer.     |
| `System.astro`     | LAMULA chain walkthrough. CSS-driven (radio + peer), JS only adds arrow-key navigation.  |
| `About.astro`      | Photo, extended bio, research interests, current affiliation.                            |
| `Research.astro`   | Research lines + key publications from `data/publications.json`.                         |
| `Projects.astro`   | Cards from `data/projects.json` with stack tags and links.                               |
| `Experience.astro` | Vertical timeline of roles and institutions.                                             |
| `Contact.astro`    | Email + social links from `data/profile.json`. No form backend.                          |
| `Footer.astro`     | Copyright, social icons.                                                                 |

---

## 7. Known Stubs & Gotchas

### Blocking before deploy

- **DNS for `vladimir.ladetec.com`** is not pointing anywhere yet. `astro.config.mjs` already declares it as `site`, so canonical, hreflang, `og:url` and the sitemap are all built against it.
- **One publication ships without a link** — _Software para el procesamiento de los ensayos de la máquina sincrónica_ (Ingeniería Energética XXX(1), 2009). Neither Crossref, Dialnet nor Redalyc indexes it. Self-host it like the ERAD paper: drop the PDF in `public/papers/` and point the entry's `pdf` field at `/papers/<file>.pdf`. `scripts/build_cv.py` absolutises such paths against `site` from `astro.config.mjs`, so a site-relative link still works inside the CV PDF. Flagged in `PREGUNTAS.md`.

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

---

## 8. Quality Gate (`pnpm verify`)

Run locally before pushing. CI enforces it on every push/PR.

| Step | Command             | Catches                                              |
| :--- | :------------------ | :--------------------------------------------------- |
| 1    | `pnpm lint`         | ESLint errors.                                       |
| 2    | `pnpm format:check` | Unformatted files. Fix: `pnpm format`.               |
| 3    | `pnpm check`        | `.astro`/TS errors, i18n key-parity guard.           |
| 4    | `pnpm build`        | Broken pages, bad imports, missing assets.           |
| 5    | `pnpm verify:links` | Broken internal links (needs `dist/` already built). |

`pnpm verify:full` additionally validates external links. Its config skips
`vladimir.ladetec.com` (not resolving yet) and `researchgate.net` (403s every bot),
and caps concurrency at 4 — Dialnet drops parallel requests and reports them as `[0]`.

---

## 9. Deployment

Static output to **Cloudflare Pages**, published by the `deploy` job in
`.github/workflows/verify.yml`. That job hangs off `needs: verify`, so the tree
that ships is the tree the gate passed, and it only fires on a push to `master`.

It needs two repository secrets — `CLOUDFLARE_API_TOKEN` (scope: `Cloudflare
Pages: Edit`) and `CLOUDFLARE_ACCOUNT_ID` — and a Pages project named
`vladimir-portfolio`. First-time setup, which needs a browser for the OAuth and
so cannot be done by an agent:

```bash
pnpm dlx wrangler login
pnpm dlx wrangler whoami                      # prints the account ID
pnpm dlx wrangler pages project create vladimir-portfolio --production-branch master
pnpm build && pnpm dlx wrangler pages deploy dist --project-name vladimir-portfolio
```

The custom domain `vladimir.ladetec.com` can only be attached from Pages if the
`ladetec.com` zone lives in the same Cloudflare account.

**Wrangler is deliberately not a dependency.** It pulls ~500 packages and a
`workerd` binary; CI uses `cloudflare/wrangler-action`, which brings its own, and
the setup above is a one-off. Run it with `pnpm dlx`, not `pnpm add`.

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
