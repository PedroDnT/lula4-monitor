// Cloudflare Pages Function: relays the latest Selic target (BCB SGS 432), which does not always send CORS headers.
const UPSTREAM = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json";

export async function onRequestGet() {
  const r = await fetch(UPSTREAM, { cf: { cacheTtl: 3600, cacheEverything: true } });
  if (!r.ok) return new Response(JSON.stringify({ error: "bcb " + r.status }), { status: 502, headers: { "Content-Type": "application/json" } });
  return new Response(r.body, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=3600" } });
}
