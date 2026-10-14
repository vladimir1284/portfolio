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
  tags, equations. Prose is Inter; data is JetBrains Mono. This single rule does
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

Both families are already loaded in `src/layouts/Layout.astro`.

| Role                                                              | Family             | Weights               |
| :---------------------------------------------------------------- | :----------------- | :-------------------- |
| Prose, headings, UI labels                                        | **Inter**          | 400 / 500 / 600 / 700 |
| All numerals, stack tags, code, equations, section indices, dates | **JetBrains Mono** | 400 / 500             |

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
