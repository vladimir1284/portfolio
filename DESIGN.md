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

**A role carries figures only where the work produced one.** The band under
the hero is the case for the whole page; `.role-figures` is the case for one
job, set smaller and printed above the prose. Two rules keep it from turning
into a stat row. A figure never restates a sentence left standing under it —
the chair's `6` and `~20` exist because the two highlights that said them in
words were deleted, and the figure is now the only place they are said. And a
role whose output was direction rather than measurement carries none at all:
an empty row there is the honest reading, not a gap to fill. The group is a
hairline and nothing else, because inside a list already divided by hairlines
a box would be a box inside a box (§1).

**"Still in use" gets the accent.** Software still running years after the
contract ended is the strongest thing an engineering role can claim, so it is
drawn as a callout against a 2px accent rule rather than as one more line of
muted prose — the one place in the record where the colour the rest of the
site saves is spent on a claim instead of on a control. It counts its own
years from the end date in the record, so it ages without anyone bumping a
number; the count is a separate sentence and is deliberately kept out of the
retrieval corpus, which that arithmetic would otherwise rewrite every January
(CLAUDE.md §11).

**A quote is drawn as words.** `Recommendations.astro` prints the quote at
reading size with the attribution under it as the chronology's eyebrow — a
48px portrait, name as the link to the profile, then role, then the date in
mono beside how the signer knows him. Where the page language is not the one
it was written in, the original follows in a muted block against a 1px rule,
small, labelled with its language. The translation never stands alone, and the
original is never hidden behind a disclosure: evidence that has to be clicked
open is evidence the page is asking to be taken on trust.

The eyebrow comes after the words here, not before them, which is the one
place on the site it does. In a role the date and the institution are the
context you need before the claim; in a quote the sentence is the claim and
the attribution is what makes it checkable.

The photos are LinkedIn's, and LinkedIn serves them at 100x100. So the
portrait is drawn at 48px and the data file's comment says why: an upscaled
face is a worse portrait than no portrait, and the entry renders without one.
Its `alt` is empty on purpose — the name sits beside it as text, and a screen
reader reading "photo of X" straight into "X" says the same thing twice.

### The carousel is a scroll container, not a slideshow

One quote per view, in a `scroll-snap` track. Every slide is laid out and in
the DOM at all times; with the script blocked the section is a row of quotes
you swipe, which is the whole content. A carousel that mounts its slides, or
hides them with `display: none`, would take the quotes off the page the same
way the LinkedIn widget would — and these are the one section whose content is
someone else's words, which makes that worse here than anywhere else.

The two arrows and the dots are the only part that needs the script, so they
are drawn by `.rec[data-live]`, the attribute the script sets: a previous/next
pair that does nothing is worse than no pair. One switch rather than three
`hidden` attributes, because `.rec-arrow` sets `display` and would beat the
user-agent rule behind `hidden`. The dots are the chronology's two states —
filled for the slide on screen, outlined for the rest — each inside a 44px
target around an 8px mark. At either end the arrow is disabled rather than
removed; a control that vanishes as you use it is a moving target.

**The controls sit above the quote, and the arrows beside it where there is
room.** The dots are a row under the lede at every width, so what the reader
meets before the first quote is how many there are and which one they are on.
The arrows ride that row below 640px and move to the sides of the card above
it: two 44px targets flanking a 360px screen would leave a 216px card and
about 37ch of prose, and §4 owns the measure. Beside the card they are set
level with the first line of the quote, not the middle of the track — the
track is as tall as the tallest card and the four cards measure 274px to
582px, so a centred arrow would float level with the bottom edge of the short
ones.

**Nothing autoplays.** Text that slides away while it is being read is a quote
the reader cannot finish — and §5 would stop the motion under
`prefers-reduced-motion` anyway, which would leave the feature existing only
for readers who did not ask not to have it. The same preference is read in the
script, because the stylesheet cannot reach a programmatic `scrollTo`: the
jump is instant where motion is refused and smooth where it is not.

The card keeps its 68ch prose column, so on a wide screen the text does not
fill the box. That is the measure doing its job, the same as every lede on the
site; a quote set to 1084px would be a quote nobody finishes a line of.

Charts obey the same rule. The output-per-year plot in `Research.astro` is
built from the same array the list under it renders, carries **no script**, and
publishes its numbers as a visually hidden `<table>` with the bars marked
`aria-hidden` — a bar chart's readable form is a table anyway. Empty years stay
in the plot: the thin stretch while the doctorate was the priority is part of
the measurement, and dropping those columns would make the shape decoration.

### The profile chronology

`About.astro` is five dated nodes on a hairline spine, not four paragraphs. The
copy is the same copy — what changed is that the years are set above the prose
instead of buried in it, so the shape of the career is read rather than
assembled.

**The dates are not written in the component.** Every eyebrow is the `from`/`to`
of an entry in `experience.json` — the same numbers the strip below draws its
bars from — and the doctorate node, which spans three entries, takes the outer
bound of the three. A node whose span is still open prints the strip's own word
for "present" and therefore ages by itself. Entries are looked up by the name
they carry, not by index, so renaming one stops the build instead of printing a
blank eyebrow.

Nitza Develop and LADETEC are **two nodes, not one**: they start a year apart
and both are still running, and a single node labelled with one company and
dated from the other's start year is simply wrong. The dot says which: filled
where the span is open, outlined where it closed — three of five are filled,
which is the parallel careers the strip draws, said in an 8px mark.

The eyebrow splits on §3 rather than setting the whole line in one face: the
years are `.data`, the institution is not. A date is a measurement; the name of
a university is prose.

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

**Bars are packed, and that is what makes the ranks read as a progression.**
Within a lane a bar takes the first track whose last bar has already ended, so
the four academic ranks — mutually exclusive, one straight after another — sit
on a single line, and a lane only grows a second track where two things
genuinely overlapped. Nothing is drawn twice: the chair itself is not a bar
next to the ranks that make it up, and a course is not a position, so the
Arduino elective stays in the panel below where it is argued properly.

**Packing only works if every bar says what it is**, so each one carries its
name, and the plot is sized backwards from that: a name goes inside its bar
when it fits and immediately beside it when it does not, and the chart's
`min-width` is the width at which the narrowest bar that must hold a name can
hold it. A bar with no end date reaches the right edge, where a name set beside
it would have nowhere to go, so the plot gives up that much width as a
right-hand margin. Below that `min-width` the box scrolls rather than
compressing the chart past the point where it can be read — a phone sees part
of a readable chart instead of all of an unreadable one.

The sizes behind that are constants in the component, in pixels, and they are
only as good as what they describe: `LABEL_COL` is the lane-name column in the
stylesheet, and `CHAR` is IBM Plex Mono's 0.6em advance at the label size.
Change either in one place and the labels start lying about whether they fit;
the bars clip rather than spill, so a wider fallback face cuts a name instead
of printing it over the bar beside it.

The three lanes differ in **fill, not hue** — accent, muted, outline. They have
to separate on a monochrome print and for a reader who does not separate
colours, and a second accent would spend the one the rest of the site saves
(§1, §2). The accent goes to the engineering lane, where the site points. A
name set on a filled bar is the ground colour, a name beside a bar is muted
like every other small label.

Geometry is generated into an inline `<style>`, not written as `style`
attributes: the CSP carries no `'unsafe-hashes'` and would drop them silently
(CLAUDE.md §9). No script runs — the strip is as correct with JavaScript off as
with it on.

The bars are `aria-hidden`; each lane carries its items as visually hidden
text, in order, so a screen reader gets "Associate, 2012–2025" and not a list
of empty boxes. The scroll container is focusable, with the ring set inward —
an outward offset is clipped on `y` by the `x` scroll.

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
