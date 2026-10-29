// Cloudflare Worker: serves the static site (ASSETS binding) and 3 small relays for sources
// that send no CORS headers. Each upstream URL is fixed, so none of them is an open proxy.
// wrangler.jsonc runs this worker first only for /api/*; every other path goes straight to the assets.

const YAHOO =
  "https://query1.finance.yahoo.com/v7/finance/spark?symbols=EWZ,BRL=X,%5EBVSP,XFIX11.SA,ITUB,PBR,VALE,BBD,ABEV,SBS,SUZ,EEM,DX-Y.NYB,MXN=X,ZAR=X,%5ETNX&range=1d&interval=15m&includePrePost=true";
const OBM = "https://obm.com.br/risco-pais";
const SELIC = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json";
const UA = { "User-Agent": "Mozilla/5.0 (compatible; lula4-monitor)" };

const json = (body, status, maxAge) =>
  new Response(typeof body === "string" ? body : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=" + maxAge },
  });

async function yahoo() {
  const r = await fetch(YAHOO, { headers: { ...UA, Accept: "application/json" }, cf: { cacheTtl: 60, cacheEverything: true } });
  if (!r.ok) return json({ error: "yahoo " + r.status }, 502, 0);
  return json(await r.text(), 200, 60);
}

// Brazil 5-year CDS row from the OBM risk page. Fails loudly if the table changes.
async function cds() {
  const r = await fetch(OBM, { headers: UA, cf: { cacheTtl: 900, cacheEverything: true } });
  if (!r.ok) return json({ error: "obm " + r.status }, 502, 0);
  const html = await r.text();
  const row = html.match(/CDS 5 Anos Brasil \(USD\)<\/a><\/div><\/td><td[^>]*>([\d.,]+)<\/td><td[^>]*>([+−\-\d.,]+)<\/td><td[^>]*>([\d.,]+%)<\/td>/);
  if (!row) return json({ error: "linha do Brasil não encontrada" }, 502, 0);
  const num = (s) => parseFloat(s.replace(/\./g, "").replace(",", ".").replace("−", "-"));
  const d = html.match(/Atualização<\/div><div[^>]*>(\d{2}\/\d{2}\/\d{4})<\/div>/);
  return json({ bp: num(row[1]), chg: num(row[2]), pd: row[3], date: d ? d[1] : null }, 200, 900);
}

async function selic() {
  const r = await fetch(SELIC, { cf: { cacheTtl: 3600, cacheEverything: true } });
  if (!r.ok) return json({ error: "bcb " + r.status }, 502, 0);
  return json(await r.text(), 200, 3600);
}

const ROUTES = { "/api/yahoo": yahoo, "/api/cds": cds, "/api/selic": selic };

export default {
  async fetch(request, env) {
    const handler = ROUTES[new URL(request.url).pathname];
    if (handler && request.method === "GET") {
      try { return await handler(); } catch (e) { return json({ error: String(e.message || e) }, 502, 0); }
    }
    return env.ASSETS.fetch(request);
  },
};
