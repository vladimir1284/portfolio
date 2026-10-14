// POST /api/reindex  →  { count, dims, b64 }
//
// Embeds the corpus with the `AI` binding and hands back the quantised matrix,
// which is then committed as rag/vectors.json and redeployed. It exists
// because the deploy token deliberately has no Workers AI permission: the
// binding needs none, so nothing has to be widened to build the index.
//
// Closed unless RAG_ADMIN_SECRET is set on the environment. Production never
// sets it; the staging project does, for the one-shot.

import { CHUNKS, DIMS, type Handler, embed, json } from "./_rag";

/** bge-m3 is happy with batches this size and it keeps each call short. */
const BATCH = 16;

export const onRequestPost: Handler = async (ctx) => {
  const secret = ctx.env.RAG_ADMIN_SECRET;
  if (!secret) return json({ error: "closed" }, 404);

  const offered = ctx.request.headers.get("authorization") ?? "";
  if (offered !== `Bearer ${secret}`) return json({ error: "unauthorised" }, 401);

  const matrix = new Int8Array(CHUNKS.length * DIMS);
  for (let start = 0; start < CHUNKS.length; start += BATCH) {
    const batch = CHUNKS.slice(start, start + BATCH);
    const vectors = await embed(
      ctx.env,
      batch.map((c) => `${c.title}\n${c.text}`)
    );
    if (vectors.length !== batch.length) {
      return json({ error: "short batch", at: start, got: vectors.length }, 500);
    }
    vectors.forEach((vector, i) => {
      const base = (start + i) * DIMS;
      for (let d = 0; d < DIMS; d++) {
        // Already L2-normalised, so every component is within [-1, 1] and
        // 127 is the whole usable range. Rounding error at 1024 dimensions is
        // far below the gap between a relevant passage and an irrelevant one.
        matrix[base + d] = Math.max(-127, Math.min(127, Math.round(vector[d] * 127)));
      }
    });
  }

  let binary = "";
  const bytes = new Uint8Array(matrix.buffer);
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);

  return json({
    count: CHUNKS.length,
    dims: DIMS,
    ids: CHUNKS.map((c) => c.id),
    b64: btoa(binary),
  });
};
