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
  alt: Localized;
  caption: Localized;
}

export interface Position {
  role: Localized;
  institution: string;
  place: Localized;
  dateLabel: Localized;
  /** Rendered with `set:html` — inline markup (<strong>, <em>) is allowed. */
  highlights?: Localized<string[]>;
  /** What the job actually ran on. Not a skills list — omit it when the
   *  highlights already name the tools. */
  stack?: string[];
  links?: PositionLink[];
  shots?: Shot[];
}

/**
 * A journal ranking, shown as a four-segment quartile strip.
 *
 * It is optional and deliberately unpopulated: a quartile is a checkable
 * number, so it ships with the ranking system and the year it was taken
 * (`SJR`, `2020`) or it does not ship at all. Fill `rank` on an entry in
 * `publications.json` and the strip appears on that entry alone.
 */
export interface Rank {
  quartile: 1 | 2 | 3 | 4;
  /** The ranking consulted — "SJR", "JCR". Rendered verbatim. */
  source: string;
  /** The edition the quartile was read from. Quartiles move between years. */
  year: number;
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
}
