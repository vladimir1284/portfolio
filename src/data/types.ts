// Shapes for the JSON content files. These exist so that a currently-empty
// array (e.g. `positions`, pending real content) still type-checks at its
// intended shape instead of collapsing to `never[]`.

import type { Lang } from "../i18n/ui";

/** A field translated inline in the data file. */
export type Localized<T = string> = Record<Lang, T>;

export interface PositionLink {
  label: string;
  url: string;
}

/** A screenshot shipped as evidence for a claim made in prose. */
export interface Shot {
  src: string;
  width: number;
  height: number;
  /** Phone-shaped capture. Rendered narrow so it does not tower over a desktop one. */
  portrait?: boolean;
  /**
   * A plot or a diagram rather than a capture of a running screen.
   *
   * Square figures are the reason this exists: set full width, the runtime
   * plot is a thousand pixels of white taller than the prose beside it. It is
   * centred and capped instead — wide enough that the axis ticks still read,
   * which `portrait` would not be.
   */
  plot?: boolean;
  /**
   * Index card only — the case itself does not print it again.
   *
   * For the frame the hero already carries: printed in the hero, cropped on
   * the projects card and shown a third time inside the case, one screenshot
   * would be doing the same work three times on one page. Drop the flag as
   * soon as the case has a capture of its own.
   */
  coverOnly?: boolean;
  alt: Localized;
  caption: Localized;
}

/**
 * A portfolio case (`projects.json`).
 *
 * The file is imported as JSON, where entries that omit an optional key infer
 * a union whose members disagree about it; the interface is what lets the
 * component read `shots` or `note` on every entry instead of narrowing six
 * times. `shots` is a list because a case is argued with more than one
 * capture — the first one is also the image the index card carries.
 */
export interface Project {
  id: string;
  featured?: boolean;
  years: string;
  status: string;
  title: Localized;
  summary: Localized;
  /** Rendered with `set:html`. Folded away behind a disclosure. */
  body: Localized;
  stack: string[];
  links: { demo?: string; code?: string; docs?: string };
  repos?: { name: string; url: string }[];
  shots?: Shot[];
  note?: Localized;
  outOfScope?: Localized<string[]>;
}

/**
 * One bar on the Experience strip (`Timeline.astro`).
 *
 * `from`/`to` are the same dates the entry already states in prose — the
 * strip is drawn from them rather than from a second list of years, so a
 * corrected date cannot leave the chart behind. `to: null` means the span is
 * still running and the bar is drawn to the right edge of the axis.
 *
 * `short` is the name that fits in a chart row: the record below the strip
 * carries the full title, so the bar does not have to.
 */
export interface Span {
  short: Localized;
  from: number;
  to: number | null;
}

export interface Position extends Span {
  role: Localized;
  institution: string;
  place: Localized;
  dateLabel: Localized;
  /** Which lane of the Experience strip this role is drawn in. The teaching
   *  lane draws `ranks` instead of the chair itself, which would be one bar
   *  under all four of them. */
  lane: "engineering" | "teaching";
  /** Rendered with `set:html` — inline markup (<strong>, <em>) is allowed. */
  highlights?: Localized<string[]>;
  /**
   * One sentence saying what the job was, printed before everything else.
   *
   * The highlights are a record and read as one; a reader scanning four roles
   * needs each of them to state itself in a line first. It frames rather than
   * summarises — anything it would repeat verbatim is deleted from the
   * highlights instead of printed twice.
   */
  summary?: Localized;
  /**
   * Measured figures for this role, printed above the highlights.
   *
   * A role gets them only where the work produced a number that can be
   * defended (CLAUDE.md §7); the ones that produced direction rather than a
   * measurement carry none, and that is the honest reading. `method` is the
   * line under the figure, never optional — DESIGN.md §4.
   */
  figures?: { value: Localized; method: Localized }[];
  /**
   * Draws the "still in use" callout under the highlights.
   *
   * The years in it are counted from `to` at build time, so the claim ages by
   * itself instead of being a number somebody has to remember to bump.
   */
  stillRunning?: boolean;
  /** What the job actually ran on. Not a skills list — omit it when the
   *  highlights already name the tools. */
  stack?: string[];
  links?: PositionLink[];
  shots?: Shot[];
}

/**
 * A journal ranking, shown as a four-segment quartile strip.
 *
 * A quartile is a checkable number, so it ships with everything needed to
 * check it — the ranking system, the edition, and the category — or it does
 * not ship at all. The category is not optional padding: a quartile only
 * exists inside one. Pattern Recognition Letters is Q1 in Computer Vision and
 * Pattern Recognition and Q2 in Artificial Intelligence, Signal Processing and
 * Software in the same SJR edition, so "Q1" with no category named is a number
 * the reader cannot verify and a claim that picked its own ground.
 */
export interface Rank {
  quartile: 1 | 2 | 3 | 4;
  /** The ranking consulted — "SJR", "JCR". Rendered verbatim. */
  source: string;
  /** The edition the quartile was read from. Quartiles move between years. */
  year: number;
  /** The subject category the quartile is in. Rendered verbatim. */
  category: string;
}

/**
 * Citation counts, read off a Google Scholar profile.
 *
 * Unlike every other figure on the page, this one cannot be derived from the
 * repository — the site does not know who cites it. So it ships with the
 * source, the profile it was read from, and the date it was read, and the
 * component prints all three. A citation count with no as-of date is a number
 * that silently rots; one with no profile link is a number nobody can check.
 *
 * `total` is Scholar's own "Cited by / All", which is *not* the sum of
 * `perYear`: the per-year chart starts at 2015 and earlier citations are
 * counted in the total but drawn nowhere. The gap is real, so the caption
 * says the chart starts in 2015 rather than letting a reader add the bars and
 * come up short.
 *
 * Refresh by hand from the profile. Nothing automates it, so the date is the
 * only thing standing between this and a stale claim.
 */
export interface Citations {
  /** The service consulted. Rendered verbatim. */
  source: string;
  /** The profile the numbers were read from. Shown as the link that proves them. */
  url: string;
  /** ISO date the profile was read. Rendered in the caption. */
  asOf: string;
  /** Scholar's "Cited by / All". Not the sum of `perYear` — see above. */
  total: number;
  hIndex: number;
  i10Index: number;
  /** The per-year bars, oldest first. The last year is normally in progress. */
  perYear: { year: number; count: number }[];
}

export interface Publication {
  group: string;
  type: string;
  title: string;
  authors: string[];
  venue: string;
  detail?: string;
  year: number;
  doi?: string;
  pdf?: string;
  abstract: Localized;
  rank?: Rank;
  /**
   * First page, rendered to WebP by `scripts/paper_thumbs.py`. Written by that
   * script, not by hand: it only sets the field for a thumbnail it has actually
   * produced, so the entry cannot point at a file that is not there.
   */
  thumb?: string;
}
