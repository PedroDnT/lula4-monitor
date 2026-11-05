// Cloudflare Worker: serves the static site, relays sources without CORS and is the
// only holder of the SILO user JWT. Every SILO operation and parameter is allowlisted.
// wrangler.jsonc runs this worker first only for /api/*; every other path goes straight to the assets.

const YAHOO =
  "https://query1.finance.yahoo.com/v7/finance/spark?symbols=EWZ,BRL=X,%5EBVSP,XFIX11.SA,BBAS3.SA,ITUB,PBR,VALE,BBD,ABEV,SBS,SUZ,EEM,DX-Y.NYB,MXN=X,ZAR=X,%5ETNX&range=1d&interval=15m&includePrePost=true";
const OBM = "https://obm.com.br/risco-pais";
const SELIC = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json";
const SILO_V2 = "https://zcjbtpxuhdekpwcxmepn.supabase.co/functions/v1/silo-api/v2";
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

const iso = (value) => typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);
const oneOf = (value, choices) => choices.includes(value);
const optional = (value, check) => value == null || check(value);
const str = (value) => typeof value === "string" && value.length > 0 && value.length <= 80;

const SILO_OPERATIONS = {
  future_curve(args) {
    if (!oneOf(args.p_root, ["DI1", "DOL", "WDO"]) || !optional(args.p_trade_date, iso)) return null;
    return ["derivatives", { kind: "futures_curve", id: args.p_root, date: args.p_trade_date }];
  },
  future_series(args) {
    if (!str(args.p_ticker) || !/^((DI1)|(DOL)|(WDO))[A-Z]\d{2}$/.test(args.p_ticker) || !iso(args.p_from)) return null;
    return ["derivatives", { kind: "futures", id: args.p_ticker, from: args.p_from }];
  },
  curve_history(args) {
    if (!oneOf(args.p_curve, ["PRE", "DPL"]) || !oneOf(args.p_tenor_days, [720, 1800]) || !iso(args.p_from)) return null;
    return ["curves", { kind: "history", curve: args.p_curve, tenor: args.p_tenor_days, from: args.p_from }];
  },
  macro_series(args) {
    const ids = ["DBGG_PIB", "NFSP_NOMINAL_12M", "NFSP_PRIMARIO_12M", "PIB"];
    if (!oneOf(args.p_series, ids) || !iso(args.p_from)) return null;
    return ["macro", { kind: "series", id: args.p_series, from: args.p_from }];
  },
  focus_expectations(args) {
    const families = { ExpectativasMercadoAnuais: "annual", ExpectativasMercadoSelic: "selic" };
    const indicator = args.p_indicator || (args.p_endpoint === "ExpectativasMercadoSelic" ? "Selic" : null);
    if (!families[args.p_endpoint] || !oneOf(indicator, ["IPCA", "Selic"]) || !str(args.p_horizon) || !iso(args.p_from)) return null;
    return ["macro", { kind: "expectations", family: families[args.p_endpoint], id: indicator, horizon: args.p_horizon, from: args.p_from }];
  },
  ptax_daily(args) {
    if (!oneOf(args.p_currency, ["USD"]) || !iso(args.p_from)) return null;
    return ["macro", { kind: "fx", currency: args.p_currency, from: args.p_from }];
  },
  investor_flow(args) {
    if (!oneOf(args.p_investor_type, ["Investidor Estrangeiro"]) || !optional(args.p_from, iso)) return null;
    return ["positioning", { kind: "investor_flow", investor_type: args.p_investor_type, from: args.p_from }];
  },
};

function siloUrl(resource, params) {
  const url = new URL(SILO_V2 + "/" + resource);
  for (const [key, value] of Object.entries(params)) if (value != null) url.searchParams.set(key, String(value));
  url.searchParams.set("limit", "100");
  return url;
}

async function siloPage(url, token) {
  const r = await fetch(url, {
    headers: { ...UA, Accept: "application/json", Authorization: "Bearer " + token },
    cf: { cacheTtl: 300, cacheEverything: true },
  });
  const body = await r.json().catch(() => null);
  if (!r.ok || !body || !Array.isArray(body.data)) {
    const code = body && body.error && body.error.code;
    throw new Error("silo " + (code || r.status));
  }
  return body;
}

async function silo(request, env) {
  if (!env.SILO_USER_JWT) return json({ error: "silo auth not configured" }, 503, 0);
  let input;
  try { input = await request.json(); } catch (_) { return json({ error: "invalid json" }, 400, 0); }
  const map = input && SILO_OPERATIONS[input.operation];
  const mapped = map && map(input.args || {});
  if (!mapped) return json({ error: "operation or arguments not allowed" }, 400, 0);

  const [resource, params] = mapped;
  let url = siloUrl(resource, params), rows = [];
  for (let page = 0; page < 10; page++) {
    const body = await siloPage(url, env.SILO_USER_JWT);
    rows.push(...body.data);
    if (!body.next_page_url) return json(rows, 200, 300);
    const next = new URL(body.next_page_url, SILO_V2 + "/");
    if (next.origin !== new URL(SILO_V2).origin || !next.pathname.startsWith(new URL(SILO_V2).pathname + "/")) throw new Error("silo invalid cursor url");
    url = next;
  }
  throw new Error("silo pagination limit");
}

const ROUTES = { "/api/yahoo": yahoo, "/api/cds": cds, "/api/selic": selic };

export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    if (path === "/api/silo" && request.method === "POST") {
      try { return await silo(request, env); } catch (e) { return json({ error: String(e.message || e) }, 502, 0); }
    }
    const handler = ROUTES[path];
    if (handler && request.method === "GET") {
      try { return await handler(); } catch (e) { return json({ error: String(e.message || e) }, 502, 0); }
    }
    return env.ASSETS.fetch(request);
  },
};
