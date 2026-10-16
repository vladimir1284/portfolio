# DESIGN.md — Visual rules

Owner of all visual/design decisions for this site. Stack, structure, i18n and
workflow live in [CLAUDE.md](./CLAUDE.md). Read both before editing.

---

## 1. Direction: scientific instrument

The site should _feel_ like measurement equipment, not like a marketing page.
That is not decoration — it is the argument. The work on display is a weather
radar rebuilt from the FPGA receiver up; the interface should read as the
console of that system.

Concretely:

- Near-black ground, one phosphor accent, generous negative space.
- **Every number is monospaced.** Dates, versions, counts, measurements, stack
  tags, equations. Prose is Inter; data is IBM Plex Mono. This single rule does
  most of the visual work.
- Rules and hairlines over boxes and shadows. Instruments have etched panels,
  not floating cards.
- Restraint. One accent colour, used sparingly, means it still signals
  something when it appears.

**Anti-goal:** the default dark-slate + indigo palette that every AI-generated
portfolio ships with. If the site could be mistaken for a template, the design
has failed.

---

## 2. Colour tokens

All colour goes through semantic tokens in `src/styles/global.css`. **Never
hardcode a raw colour in a component.** Dark is the default (`<html class="dark">`);
`html.light` overrides.

| Token                  | Dark      | Light     | Use                                                     |
| :--------------------- | :-------- | :-------- | :------------------------------------------------------ |
| `--color-bg`           | `#07090b` | `#f7f9f8` | Page ground                                             |
| `--color-surface`      | `#0e1216` | `#ffffff` | Raised panels, cards                                    |
| `--color-border`       | `#1d262c` | `#dde5e2` | Hairlines, dividers, outlines                           |
| `--color-text`         | `#e3ecea` | `#0c1613` | Body copy, headings                                     |
| `--color-muted`        | `#8fa3a0` | `#536b66` | Secondary copy, labels, captions                        |
| `--color-accent`       | `#35e0a1` | `#06795a` | Links, active state, focus ring, key figures            |
| `--color-accent-hover` | `#5febba` | `#045c44` | Hover/active on accent                                  |
| `--color-warn`         | `#f5a524` | `#9a5b00` | Caveats, "early scaffolding" badges, out-of-scope notes |

### Contrast is verified, not assumed

Every foreground token clears **WCAG AA (≥ 4.5:1)** against both `--color-bg`
and `--color-surface` in both themes; most clear AAA. Measured:

| Pair (on `bg`) |  Dark | Light |
| :------------- | ----: | ----: |
| `text`         | 16.57 | 17.42 |
| `muted`        |  7.52 |  5.42 |
| `accent`       | 11.71 |  5.11 |
| `warn`         |  9.77 |  5.13 |

**If you change a colour token, re-run the check.** Never ship a token pair
that drops below 4.5:1 on `bg` or `surface`. `--color-border` is for hairlines
only — do not put text on it.

### Documented exception: the dBZ colormap

Radar reflectivity is rendered with the **standard NWS dBZ colour scale**, and
velocity with a diverging scale. These are _scientific data encodings, not
brand decisions_ — a radar meteorologist reads them by memory, and recolouring
them to match the site would make the output wrong.

They therefore live as typed constants in TypeScript (`src/components/lamula/`),
**not** as CSS tokens, and they are exempt from the "no hardcoded colours" rule.
No other exception exists.

---

## 3. Typography

### Self-hosted, and only the `latin` slice

Both families ship from `dist/`. They come from the `@fontsource-variable/inter`
and `@fontsource/ibm-plex-mono` packages, which pin the version and are the
source of the files; `src/styles/global.css` writes the three `@font-face`
rules by hand and `Layout.astro` preloads the three woff2.

Three decisions worth not relitigating:

- **Not from Google.** The `<link rel="stylesheet">` to `fonts.googleapis.com`
  is render-blocking on a second origin, and the woff2 it names can only be
  discovered once it parses, on a third. Served locally and preloaded, the
  faces start in parallel with the site's own stylesheet — measured in the
  browser, all three begin at 118–124 ms alongside the CSS at 124 ms. It also
  takes the only two third-party hosts out of the CSP (CLAUDE.md §9) and means
  no visitor request reaches Google.
- **`@font-face` written out rather than imported.** The fontsource entry
  points declare every subset the family ships and Vite emits a file for each,
  which put 170 KB of Cyrillic, Greek and Vietnamese in `dist/` that no visitor
  would ever fetch. Three rules, three files.
- **The `wght` axis of Inter, not `standard`.** 48 KB against 71 KB, and
  nothing on the page varies optical size.

Self-hosting costs about 9 KB more than Google's build — Google subsets IBM
Plex Mono harder — and **no end-to-end speed-up has been measured.** Over six
and four Lighthouse runs per build under applied 4G throttling, median FCP/LCP
came out 3219 ms against 3230 ms: indistinguishable, with run-to-run spread of
2.7–7.1 s dominated by CPU contention in the dev container. Lighthouse here
cannot resolve a 250 ms effect. The change rests on the structural argument and
on the CSP, not on a number.

**`→` (U+2192) is in neither `latin` subset** — not fontsource's and not
Google's, so this is not a regression. The three arrows in the fact band
(`2008 →`) therefore render in the fallback, beside digits that are IBM Plex
Mono. Either swap them for a character the subset has (`›`, U+203A, already
used in the hero list) or accept the mismatch; do not add a second font file
for three glyphs.

| Role                                                              | Family            | Weights               |
| :---------------------------------------------------------------- | :---------------- | :-------------------- |
| Prose, headings, UI labels                                        | **Inter**         | 400 / 500 / 600 / 700 |
| All numerals, stack tags, code, equations, section indices, dates | **IBM Plex Mono** | 400 / 500             |

Scale (fluid, `clamp()` between mobile and desktop):

| Step      | Size                                                 | Use                           |
| :-------- | :--------------------------------------------------- | :---------------------------- |
| `display` | `clamp(2.5rem, 7vw, 4.5rem)`                         | Hero name only                |
| `h1`      | `clamp(2rem, 4vw, 3rem)`                             | Page title                    |
| `h2`      | `clamp(1.5rem, 2.5vw, 2rem)`                         | Section headings              |
| `h3`      | `1.25rem`                                            | Card and entry titles         |
| `body`    | `1rem` / `1.0625rem`                                 | Prose; line-height `1.7`      |
| `small`   | `0.875rem`                                           | Captions, metadata            |
| `label`   | `0.75rem`, mono, `letter-spacing: 0.08em`, uppercase | Section eyebrows, data labels |

Measure: cap prose at **68ch**. Never full-bleed body text.

---

## 4. Layout

- Content column `max-width: 72rem`, centred, **16px minimum side gutter** on phones.
- Vertical rhythm between sections: `clamp(5rem, 10vw, 8rem)`.
- Sections are separated by a 1px `--color-border` rule, not by background shifts.
- Breakpoints: Tailwind defaults. Design mobile-first; every interactive piece
  must work at 360px wide with no horizontal page scroll.

### Measured figures and the fact band

A figure set large is a claim, so **`.figure-n` never appears without a
`.figure-method` line under it** saying how it was arrived at (CLAUDE.md §7).
`~300` keeps its tilde; an estimate that hides being an estimate is worse than
no figure at all.

The band under the hero (`Facts.astro`) is an **etched grid** — a 1px gap over
a border-coloured ground, cells painted in the page ground — not six floating
cards (§1). Half of its figures are counted from `publications.json` at build
time instead of typed in, so the band cannot drift from the sections below it.

Charts obey the same rule. The output-per-year plot in `Research.astro` is
built from the same array the list under it renders, carries **no script**, and
publishes its numbers as a visually hidden `<table>` with the bars marked
`aria-hidden` — a bar chart's readable form is a table anyway. Empty years stay
in the plot: the thin stretch while the doctorate was the priority is part of
the measurement, and dropping those columns would make the shape decoration.

### The Experience strip

`Timeline.astro` draws the lede of that section rather than restating it. Three
lanes — teaching, engineering, education — on one axis from 2003 to the current
year, so "two careers in parallel since 2008" is something the reader sees
instead of something they assemble from dates.

It obeys the same rule the citation chart does: **every bar comes from the
`from`/`to` the entry already carries**, the same numbers the record below
prints as prose. There is no second list of years to drift. The right edge of
the axis is the current year, computed at build, so a role with no end date
reaches it without anyone remembering to extend the axis in January — and the
edge carries its own tick, because a bar that runs off the end only means
"still running" if the end is labelled.

**One row per item, not bars packed onto three lanes.** Packed is the compact
drawing and it cannot be made to work here: a one-year rank, or a degree
defended inside a single year, is narrower than its own label at every width
the page is read at, so the label either clips or runs over the bar beside it.
A row each costs vertical space and buys a chart with no unreadable state.

The three lanes differ in **fill, not hue** — accent, muted, outline. They have
to separate on a monochrome print and for a reader who does not separate
colours, and a second accent would spend the one the rest of the site saves
(§1, §2). The accent goes to the engineering lane, where the site points.

Geometry is generated into an inline `<style>`, not written as `style`
attributes: the CSP carries no `'unsafe-hashes'` and would drop them silently
(CLAUDE.md §9). No script runs — the strip is as correct with JavaScript off as
with it on. Under `sm` the name moves above its own track, which gives the axis
the full width of the card; side by side at 360px, a name column wide enough to
read leaves about 150px for twenty-three years and the chart has to be scrolled
before it says anything. Above `sm` the two-column layout returns and the box,
not the page, scrolls.

Bars are `aria-hidden`; each row carries its span as visually hidden text after
the name, so a screen reader gets "Associate, 2012–2025" and not a list of
empty boxes. The scroll container is focusable, with the ring set inward — an
outward offset is clipped on `y` by the `x` scroll.

### The publication list is clamped, not truncated

Each tab in `Research.astro` shows its three most recent entries and scrolls
for the rest. The hint that there is more is the fourth entry itself, half
visible under a gradient to the page ground — not a chevron, not a "show more"
button that hides how much more there is. The fade goes to zero at the bottom
of the scroll: a gradient promising more where there is none reads as a bug.

The height is **measured**, by the script in `Research.astro`, from where the
fourth entry starts. A number of rem typed in would be right at one width only:
an entry is a card on a phone and a row on a desktop, and an opened abstract
changes it again. It is capped at `85vh` on top of that, because three cards on
a phone are 1486 px — a scroll box twice the height of the screen is the page
again, with its own hint off-screen. On a phone the cap wins and about one and
a half entries show; on a desktop the measurement wins and exactly three do.

Nothing is hidden from anyone who cannot run the clamp: with JavaScript off the
list is simply long, and in the print stylesheet the clamp and the fade both
come off.

### The projects front page

`Projects.astro` is an index on the home page and nothing more: the lead case
takes a 16:9 cover, the next two a thumbnail each, and a link under them leads
to `/projects/`, where every case is listed. Covers and thumbnails are cropped
(`object-fit: cover`, anchored to the top — a screenshot carries its subject
under the title bar). Cropping is only acceptable because the index is a
pointer: the same capture is printed whole, with its caption, on the case page.

**The cases themselves are pages, not anchors.** Six cases at full depth on the
home page were four to five paragraphs each plus every capture, folded into
disclosures, inside a document every visitor downloaded whole — about 29 KB of
the 130 KB. Each case now serves at `/projects/<id>/` in both locales, and the
home document is 100 KB. The fold went with them: a reader who opened one case
chose it, so the argument prints open and the captures come first.

A case with no capture yet gets an etched panel carrying its index and
`projects.shot.pending`, not a stand-in image. The empty panel is the honest
state and it is meant to be temporary.

A capture marked `coverOnly` is the index image and nothing else, for the case
where the same frame is already printed elsewhere — one screenshot doing the
same work twice reads as padding. No shot carries the flag today: the LAMULA
case held it while it borrowed the hero's frame, and lost it when the hero
moved to the loop and the case gained a velocity capture of its own.

A `plot` is the opposite problem: a chart or a block diagram is not a capture of
a running screen, and a square one set full width is a thousand pixels of white
taller than the prose beside it. It is centred and capped at `max-w-xl` instead
— wide enough that the axis ticks still read, which the narrower `portrait`
treatment would not be.

Under `lg` both the home index and `/projects/` are one column, and the column
rule disappears.

A case page ends with the way out of it — back to the index, then the previous
and next case in the order `projects.json` holds, which is the order the index
prints. Without it a case is a leaf and the only route onward is the back
button.

---

## 5. Motion

Motion must look like _instrument response_ — fast, linear, purposeful — never
like decoration.

- Durations: `120ms` (state change), `200ms` (reveal). Nothing above `300ms`.
- Easing: `cubic-bezier(0.2, 0, 0, 1)`. No bounce, no spring, no parallax.
- No scroll-jacking. No entrance animation on text — content is readable the
  instant it paints.

**`prefers-reduced-motion: reduce` is a first-class path, not an afterthought:**
all transitions collapse to `0ms`, the live hero falls back to a static image,
and any looping or auto-playing visual stops. Test it on every change.

---

## 6. Focus and interaction

- Visible focus ring on **every** interactive element:
  `outline: 2px solid var(--color-accent); outline-offset: 2px`. Never
  `outline: none` without an equivalent replacement.
- Hit targets ≥ 44×44px.
- Links in prose: underlined with `text-underline-offset: 0.2em`. Accent colour
  alone is not sufficient signal.
- Every interactive control reachable and operable by keyboard, in a sane tab order.

---

## 7. Performance budget

| Metric                                      | Budget                                                       |
| :------------------------------------------ | :----------------------------------------------------------- |
| LCP (simulated 4G)                          | < 1.5 s                                                      |
| Self-authored JS (LAMULA diagram, DSP demo) | < 40 KB gzip                                                 |
| Any third-party map library                 | lazy, via `IntersectionObserver`, never in the critical path |

**The site must communicate its full thesis with JavaScript disabled.** Every
interactive piece degrades to a static WebP plus its explanatory text. If a
section becomes meaningless without JS, it is designed wrong.

Raster assets ship as **WebP** via `pnpm optimize:images` (see CLAUDE.md §9).

---

## 8. Checklist before committing visual changes

1. `pnpm verify` clean.
2. Both themes, both locales (`/` and `/es/`), 360px and 1440px.
3. Keyboard-only pass over any new interactive element.
4. `prefers-reduced-motion: reduce` honoured.
5. No raw colour literals outside the dBZ colormap constants.
6. No prose line longer than 68ch.
