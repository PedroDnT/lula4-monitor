// Cloudflare Pages Function: reads the Brazil 5-year CDS row from the OBM risk page and returns JSON.
// Shape matches what the page expects: {bp, chg, pd, date}. Fails loudly if the table changes.
const UPSTREAM = "https://obm.com.br/risco-pais";

export async function onRequestGet() {
  const r = await fetch(UPSTREAM, { headers: { "User-Agent": "Mozilla/5.0 (compatible; lula4-monitor)" }, cf: { cacheTtl: 900, cacheEverything: true } });
  if (!r.ok) return json({ error: "obm " + r.status }, 502);
  const html = await r.text();
  const row = html.match(/CDS 5 Anos Brasil \(USD\)<\/a><\/div><\/td><td[^>]*>([\d.,]+)<\/td><td[^>]*>([+−\-\d.,]+)<\/td><td[^>]*>([\d.,]+%)<\/td>/);
  if (!row) return json({ error: "linha do Brasil não encontrada" }, 502);
  const num = (s) => parseFloat(s.replace(/\./g, "").replace(",", ".").replace("−", "-"));
  const d = html.match(/Atualização<\/div><div[^>]*>(\d{2}\/\d{2}\/\d{4})<\/div>/);
  return json({ bp: num(row[1]), chg: num(row[2]), pd: row[3], date: d ? d[1] : null }, 200);
}

const json = (o, status) => new Response(JSON.stringify(o), { status, headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=900" } });
