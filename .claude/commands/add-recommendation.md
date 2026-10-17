---
description: Add a recommendation someone wrote to the Recommendations section, from pasted LinkedIn text.
---

Add one recommendation to `src/data/recommendations.json` and ship it.

The pasted block is in `$ARGUMENTS` — normally copied straight off LinkedIn,
so it looks like: the person's name, a connection degree, their headline, a
line such as `21 de septiembre de 2021, X asesoró a Vladímir`, then the text.
If `$ARGUMENTS` is empty, ask for the paste before doing anything else.

Read CLAUDE.md §3.2 first — it owns the rules this command carries out.

## What to do

1. **Get the profile URL.** It is not in the pasted block and it is not
   optional: the link is what makes the quote checkable. Ask for it if it was
   not given. One recommendation, one URL.

2. **Append an entry** to `src/data/recommendations.json`:

   - `id` — the signer's surname, kebab-case. It is the retrieval chunk id, so
     renaming one later moves a citation.
   - `lang` — the language the text was **written** in, not the page's. The
     `quote` member under this key is verbatim.
   - `quote.en` / `quote.es` — the original under `lang`, your translation
     under the other. **Verbatim means verbatim**: keep the typos, the odd
     accents, the spelling of Vladímir's name as that person wrote it. You are
     quoting someone, not editing them.
   - `name` — as the person signs it, except where they are already a
     co-author in `src/data/publications.json`: use the form that file carries,
     so the same person is one person across the page. Check before deciding.
   - `role` — a factual compression of their LinkedIn headline, in both
     locales. Headlines are often marketing copy; keep the degree, the field
     and the institution, drop the adjectives. Never invent an affiliation,
     a title or a year the paste does not contain.
   - `relation` — `advised` or `fellow`. A new kind needs three edits that
     belong together: the union in `src/data/types.ts`, and
     `recommendations.relation.<kind>` in **both** `src/i18n/en.json` and
     `src/i18n/es.json`. `Recommendations.astro` throws at build time if the
     key is missing, so a half-done addition fails the build instead of
     rendering a blank line.
   - `date` — ISO, from the line LinkedIn prints above the text.
   - `url` — the profile.
   - `photo` — optional, `/img/recommendations/<id>.webp`. Omit the key if
     there is no photo; the entry renders without one.

3. **Add the photo, if there is one.** Save their LinkedIn avatar to the repo
   root, then:

   ```bash
   mv <downloaded file> public/img/recommendations/<id>.jpeg
   pnpm optimize:images public/img/recommendations --max 100 --delete
   ```

   LinkedIn serves avatars at 100x100 and the page draws them at 48px, so
   `--max 100` costs nothing and the original never ships. The file is named
   after the entry's `id`. Do not enlarge it anywhere: an upscaled face reads
   worse than no face.

   If you cannot tell which photo belongs to which person, say so and ask —
   the wrong face over someone's words is a worse error than a missing one.

4. **Rebuild the corpus**: `pnpm corpus`. Then `pnpm verify`.

   `corpus:check` will fail with "the index is stale". That is expected and is
   step 5 — every other step of the gate must pass. A change that touches only
   `photo` leaves the corpus byte-identical, since the portrait is not indexed;
   in that case the gate is green in one pass and steps 5 and the `chore(rag)`
   commit do not apply.

5. **Reindex the vectors**, which requires a deploy: `python3
   scripts/reindex_vectors.py` (read its docstring; CLAUDE.md §11 explains why
   it cannot run locally). **Ask before running it** — it deploys the current
   working tree to the live site. Afterwards `pnpm verify` must be fully green.

6. **Commit and push only if asked.** Two commits, as the section was built:
   `feat(recommendations): …` for the content, `chore(rag): reindex vectors …`
   for `rag/vectors.json`. CI deploys from `master`.

   Until `rag/vectors.json` ships, production serves a corpus the index does
   not match, `_rag.ts` refuses the matrix and `/api/ask` degrades to the
   static question list. That is by design — it would rather answer nothing
   than cite the wrong passage — but it means the push is part of the job,
   not an afterthought.

## Check before you call it done

- Both locales render: the page in the original's language shows the quote
  once, the other shows the translation with the original underneath it.
- The carousel still shows one quote per view at 360px with no page scroll,
  the new dot appears, and the arrows disable at the ends.
- The quote is not a figure and carries no number you added.
- Nothing in the entry is something the signer did not actually say or claim.
