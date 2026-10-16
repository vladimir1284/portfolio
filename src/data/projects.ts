// The project list, typed, plus the one place that decides where a case lives.
//
// Each case is its own page (`/projects/<id>/`), not an anchor on the home
// page: six cases at full depth made the home document 130 KB, most of which
// no visitor read. The home section keeps the index; the argument moved.
//
// `projectRoute` returns a LOCALE-AGNOSTIC route — no leading slash, no
// locale prefix — which is what `getRelativeLocaleUrl` / `getAbsoluteLocaleUrl`
// expect. Both locales serve the same path under their own prefix, so the
// hreflang pair for a case is the same route twice and the language switcher
// stays on the case the reader is reading.

import type { Project } from "./types";
import projectsData from "./projects.json";

export const projects = projectsData as Project[];

export const projectsRoute = "projects/";

export function projectRoute(id: string): string {
  return `${projectsRoute}${id}/`;
}

/** Previous and next case in file order — the order the index prints. */
export function neighbours(id: string): { prev?: Project; next?: Project } {
  const i = projects.findIndex((p) => p.id === id);
  return { prev: projects[i - 1], next: projects[i + 1] };
}
