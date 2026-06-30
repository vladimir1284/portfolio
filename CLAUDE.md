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
pnpm optimize:images [paths] [--max <px>] [--delete]   # convert raster assets to WebP (see §8)

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
├── data/
│   ├── projects.json         # portfolio projects list
│   └── publications.json     # academic publications list
└── styles/global.css         # Tailwind import + design tokens + custom classes
public/                       # static assets (favicon, avatar, screenshots as .webp, cv.pdf)
scripts/optimize_images.py    # JPG/PNG → WebP converter (see §8)
```

Both page routes import the **same component set**; they differ only by locale. Keep in sync — if you add/remove a section, update **both** `index.astro` files.

---

## 3. Sections / Content

Single-page layout, sections in order:

| Section    | Component          | Content                                                                              |
| :--------- | :----------------- | :----------------------------------------------------------------------------------- |
| Hero       | `Hero.astro`       | Name, tagline, short bio, CTAs (CV download + contact anchor).                       |
| About      | `About.astro`      | Photo, extended bio, current role/institution, research interests.                   |
| Research   | `Research.astro`   | Research lines, key publications (from `data/publications.json`).                    |
| Projects   | `Projects.astro`   | Cards from `data/projects.json`: title, stack tags, links (demo/GitHub).             |
| Experience | `Experience.astro` | Timeline: positions, institutions, dates.                                            |
| Contact    | `Contact.astro`    | Email + social links (GitHub, LinkedIn, Google Scholar, ORCID). No form backend.     |
| Header     | `Header.astro`     | Fixed nav: name/logo, section anchors, theme toggle, language switcher.              |
| Footer     | `Footer.astro`     | Copyright, social icons.                                                             |

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

| Component          | Responsibility                                                                             |
| :----------------- | :----------------------------------------------------------------------------------------- |
| `Layout.astro`     | `<head>`: title/description, canonical + hreflang, OG/Twitter tags, fonts, theme script.  |
| `Header.astro`     | Fixed nav: name, section anchors, theme toggle, language switcher.                        |
| `Hero.astro`       | Name, tagline, bio summary, CV download link, contact CTA.                                |
| `About.astro`      | Photo, extended bio, research interests, current affiliation.                             |
| `Research.astro`   | Research lines + key publications from `data/publications.json`.                          |
| `Projects.astro`   | Cards from `data/projects.json` with stack tags and links.                                |
| `Experience.astro` | Vertical timeline of roles and institutions.                                              |
| `Contact.astro`    | Email + social links (GitHub, LinkedIn, Google Scholar, ORCID). No form backend.          |
| `Footer.astro`     | Copyright, social icons.                                                                  |

---

## 7. Known Stubs & Gotchas

- **`site` in `astro.config.mjs`** must be the real production domain before deploy — canonical, hreflang, `og:url`, and sitemap all derive from it.
- **CV download**: `Hero.astro` links to `public/cv.pdf` — keep updated.
- **Contact section has no form** — just links. No backend needed.
- **No unit-test suite.** Run `pnpm verify` + manual pass over `/` and `/es/` (light and dark) before pushing.
- Both `pages/index.astro` and `pages/es/index.astro` must stay in sync.

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

---

## 9. Image Optimization

Raster assets in `public/` ship as **WebP**. Converter: `scripts/optimize_images.py` (Python 3 + Pillow).

```bash
pnpm optimize:images                            # everything under public/
pnpm optimize:images public/img/projects --max 1200 --delete
pnpm optimize:images public/img/avatar --max 512 --delete
```

- `--quality <1-100>` (default 80), `--max <px>` downscales (never upscales), `--delete` removes source.
- **References not rewritten automatically** — update `data/*.json` paths after converting.
