// Cloudflare Pages Function: relays one fixed Yahoo Finance spark request.
// The browser cannot call Yahoo directly (no CORS). The URL is fixed, so this is not an open proxy.
const UPSTREAM =
  "https://query1.finance.yahoo.com/v7/finance/spark?symbols=EWZ,BRL=X,%5EBVSP,XFIX11.SA,ITUB,PBR,VALE,MXN=X,ZAR=X,%5ETNX&range=1d&interval=15m&includePrePost=true";

export async function onRequestGet() {
  const r = await fetch(UPSTREAM, {
    headers: { "User-Agent": "Mozilla/5.0 (compatible; lula4-monitor)", Accept: "application/json" },
    cf: { cacheTtl: 60, cacheEverything: true },
  });
  if (!r.ok) return new Response(JSON.stringify({ error: "yahoo " + r.status }), { status: 502, headers: { "Content-Type": "application/json" } });
  return new Response(r.body, { headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=60" } });
}
