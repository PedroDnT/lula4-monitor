import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../worker.js", import.meta.url), "utf8");
const worker = (await import("data:text/javascript;base64," + Buffer.from(source).toString("base64"))).default;
const assets = { fetch: () => new Response("asset", { status: 200 }) };
const request = (body) => new Request("https://monitor.test/api/silo", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

{
  const response = await worker.fetch(request({ operation: "future_series", args: {} }), { ASSETS: assets });
  assert.equal(response.status, 503);
}

{
  const response = await worker.fetch(request({ operation: "unknown", args: {} }), { ASSETS: assets, SILO_USER_JWT: "jwt" });
  assert.equal(response.status, 400);
}

{
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url: String(url), options });
    return new Response(JSON.stringify({ data: [{ trade_date: "2026-11-03" }], meta: {} }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };
  try {
    const response = await worker.fetch(request({
      operation: "future_series",
      args: { p_ticker: "DI1F29", p_from: "2026-10-23" },
    }), { ASSETS: assets, SILO_USER_JWT: "jwt" });
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), [{ trade_date: "2026-11-03" }]);
    assert.equal(calls.length, 1);
    assert.equal(calls[0].options.headers.Authorization, "Bearer jwt");
    const url = new URL(calls[0].url);
    assert.equal(url.pathname.endsWith("/v2/derivatives"), true);
    assert.equal(url.searchParams.get("kind"), "futures");
    assert.equal(url.searchParams.get("id"), "DI1F29");
  } finally { globalThis.fetch = original; }
}

{
  const original = globalThis.fetch;
  const cases = [
    ["curve_history", { p_curve: "PRE", p_tenor_days: 720, p_from: "2026-01-01" }, "curves", "history"],
    ["macro_series", { p_series: "DBGG_PIB", p_from: "2026-01-01" }, "macro", "series"],
    ["focus_expectations", { p_endpoint: "ExpectativasMercadoAnuais", p_indicator: "IPCA", p_horizon: "2027", p_from: "2026-01-01" }, "macro", "expectations"],
    ["focus_expectations", { p_endpoint: "ExpectativasMercadoSelic", p_horizon: "R1/2027", p_from: "2026-01-01" }, "macro", "expectations"],
    ["ptax_daily", { p_currency: "USD", p_from: "2026-01-01" }, "macro", "fx"],
    ["investor_flow", { p_investor_type: "Investidor Estrangeiro" }, "positioning", "investor_flow"],
  ];
  try {
    for (const [operation, args, resource, kind] of cases) {
      let called;
      globalThis.fetch = async (url) => {
        called = new URL(String(url));
        return new Response(JSON.stringify({ data: [], meta: {} }), { status: 200, headers: { "Content-Type": "application/json" } });
      };
      const response = await worker.fetch(request({ operation, args }), { ASSETS: assets, SILO_USER_JWT: "jwt" });
      assert.equal(response.status, 200, operation);
      assert.equal(called.pathname.endsWith("/v2/" + resource), true, operation);
      assert.equal(called.searchParams.get("kind"), kind, operation);
    }
  } finally { globalThis.fetch = original; }
}

{
  const original = globalThis.fetch;
  let page = 0;
  globalThis.fetch = async (url) => {
    page += 1;
    const next = "https://zcjbtpxuhdekpwcxmepn.supabase.co/functions/v1/silo-api/v2/derivatives?cursor=opaque";
    return new Response(JSON.stringify(page === 1
      ? { data: [{ trade_date: "2026-11-03" }], meta: {}, next_page_url: next }
      : { data: [{ trade_date: "2026-11-04" }], meta: {} }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };
  try {
    const response = await worker.fetch(request({
      operation: "future_series",
      args: { p_ticker: "DI1F29", p_from: "2026-10-23" },
    }), { ASSETS: assets, SILO_USER_JWT: "jwt" });
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), [
      { trade_date: "2026-11-03" },
      { trade_date: "2026-11-04" },
    ]);
    assert.equal(page, 2);
  } finally { globalThis.fetch = original; }
}

console.log("worker SILO relay tests passed");
