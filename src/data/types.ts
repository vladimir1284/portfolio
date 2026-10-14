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
  links?: PositionLink[];
  shot?: Shot;
}
