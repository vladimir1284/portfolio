# Retrieval corpus and index

`/api/ask` answers questions about this site from this directory and nothing
else. Two files, both generated, both committed:

| File           | What it is                                                           |
| :------------- | :------------------------------------------------------------------- |
| `corpus.json`  | Chunks of what the site publishes, each with the URL that proves it. |
| `vectors.json` | Those chunks embedded with `@cf/baai/bge-m3`, L2-normalised, int8.   |

```bash
pnpm corpus          # rebuild corpus.json from src/data and src/i18n
pnpm corpus:check    # fail if corpus.json or vectors.json is stale (runs in `pnpm verify`)
python3 scripts/reindex_vectors.py   # rebuild vectors.json — see below
```

## Why the paper text is committed rather than re-extracted

`pdftotext` is not on the CI runner, and putting it there would be worse than
leaving it out: poppler versions disagree about whitespace, so the same PDF
extracts differently on two machines and `pnpm corpus:check` would fail over
nothing. The extracted text lives in `corpus.json`, and `papers.lock.json`
records the hash of the PDF it came from. Without `pdftotext` the build reuses
those chunks while the hashes match, and stops rather than guess when a PDF has
changed.

## Why there is no vector database

A hundred-odd chunks at 1024 dimensions is 108 KB of int8. The endpoint scores
the whole corpus with a dot product per row, which costs less than the network
round trip a managed index would add. Vectorize would be a dependency, a second
thing to keep in sync, and a permission the deploy token does not have.

## Why the index is built by the deployed site

Embedding needs Workers AI. The deploy token has `Cloudflare Pages: Edit` and
nothing else — on purpose, because it lives in GitHub Actions. Inside a Pages
Function the `AI` binding needs no token at all, so `/api/reindex` builds the
index and hands it back. Nothing has to be widened to rebuild the index.

That endpoint is closed unless `RAG_ADMIN_SECRET` is set on the project, and
production does not set it. `scripts/reindex_vectors.py` opens it for one run
and closes it again; read the docstring before running it, because Pages only
shows environment changes to _new_ deployments and the order matters.

## The rule

An answer carries a citation and a link, or it is not shown. The endpoint
drops a model response with no citation marker rather than present an
unverifiable paragraph, and the page falls back to questions answered from its
own copy — `src/components/ask/faq.ts`, which involves no model at all.

## Budget

On the Cloudflare free allowance of 10 000 neurons/day, at the published rates
for `@cf/meta/llama-3.1-8b-instruct-fp8-fast` (4119 neurons per million input
tokens, 34868 per million output), an answer of roughly 2000 input and 300
output tokens costs about 19 neurons — around 500 answers a day. Embedding the
question with `bge-m3` is 0.05 of one. Past the allowance Workers AI refuses,
`/api/ask` returns `ok: false`, and the page shows the fallback.

## What is not in the corpus

The thesis. It is in `_material/`, which is gitignored working material, and
whether the PDF is public has not been settled. Papers that ship under
`public/papers/` are included, because anyone can already open them.
