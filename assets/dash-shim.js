/* Minimal stand-in for the claude.ai Dashboard runtime ("dash").
   It lets the dashboard pages run unchanged on a plain static host.
   Datasets: window.DATASETS = { id: {kind:"file", url} | {kind:"query", tool, args} }.
   Query datasets call the public SILO read API (schema api) with the publishable key. */
(function () {
  const SILO_URL = "https://zcjbtpxuhdekpwcxmepn.supabase.co/rest/v1/rpc/";
  const SILO_KEY = "sb_publishable__yfFQsykAglrvc9GS6_PYw_B24ex437";
  const defs = window.DATASETS || {};
  const state = new Map();      // id -> {status, data, columns, message, refreshing, meta}
  const loaders = new Map();
  const calcs = new Map();
  const listeners = [];
  let params = {};
  let timer = null;

  const palette = ["#2a78d6", "#d0612f", "#7a5fc4", "#0f7b4f", "#a15c00", "#c2398a", "#3a9d9d", "#8a8780"];
  const colors = palette.slice();

  const notify = () => { clearTimeout(timer); timer = setTimeout(() => listeners.forEach((f) => { try { f(); } catch (e) { console.error(e); } }), 30); };
  const cols = (rows) => (rows.length && typeof rows[0] === "object" ? Object.keys(rows[0]) : []);
  const toRows = (j) => Array.isArray(j) ? j : (j && (j.rows || j.data || j.results)) || [];
  const fill = (v) => typeof v === "string" ? v.replace(/\{\{(\w+)\}\}/g, (_, k) => (params[k] != null ? params[k] : "")) : v;

  function set(id, st) {
    state.set(id, Object.assign({ status: "loading", data: [], columns: [], message: "", refreshing: false, meta: [] }, st));
    calcs.forEach((c, cid) => { if (c.inputs.includes(id)) computeCalc(cid); });
    notify();
  }

  const paramsReady = window.PARAMS_URL
    ? fetch(window.PARAMS_URL, { cache: "no-cache" }).then((r) => r.json()).then((p) => { params = Object.assign({}, p, params); }).catch((e) => console.error("params", e))
    : Promise.resolve();

  async function load(id) {
    const d = defs[id];
    try {
      await paramsReady;
      let rows;
      if (d.kind === "file") {
        const r = await fetch(d.url, { cache: "no-cache" });
        if (!r.ok) throw new Error(d.url + " " + r.status);
        rows = toRows(await r.json());
      } else {
        const args = {}; Object.keys(d.args || {}).forEach((k) => { args[k] = fill(d.args[k]); });
        const r = await fetch(SILO_URL + d.tool, { method: "POST", headers: { apikey: SILO_KEY, "Accept-Profile": "api", "Content-Profile": "api", "Content-Type": "application/json" }, body: JSON.stringify(args) });
        const j = await r.json();
        if (!r.ok) throw new Error((j && (j.message || j.details)) || ("SILO " + r.status));
        rows = j;
        const L = loaders.get(id);
        if (L) rows = L.fn({ answer: j, call: null });
      }
      set(id, { status: "ok", data: rows, columns: cols(rows) });
    } catch (e) {
      console.error("dataset", id, e);
      set(id, { status: "error", message: String(e.message || e) });
    }
  }

  function computeCalc(id) {
    const c = calcs.get(id);
    const ins = c.inputs.map((i) => dash.data(i));
    if (ins.some((s) => s.status === "error")) return set(id, { status: "error", message: "input failed" });
    if (ins.some((s) => s.status !== "ok")) return set(id, { status: "loading" });
    try {
      const out = c.fn(...ins.map((s) => s.data));
      set(id, { status: "ok", data: out, columns: Array.isArray(out) ? cols(out) : [] });
    } catch (e) { console.error("calc", id, e); set(id, { status: "error", message: String(e.message || e) }); }
  }

  const dash = {
    colors,
    data(id) {
      if (!state.has(id)) {
        if (calcs.has(id)) { set(id, { status: "loading" }); queueMicrotask(() => computeCalc(id)); }
        else if (defs[id]) { set(id, { status: "loading" }); queueMicrotask(() => load(id)); }
        else return { status: "missing", data: [], columns: [], message: "unknown dataset " + id, refreshing: false, meta: [] };
      }
      return state.get(id);
    },
    onData(fn) {
      listeners.push(fn);
      let w = 0; new ResizeObserver(() => { const n = document.documentElement.clientWidth; if (n !== w) { w = n; notify(); } }).observe(document.documentElement);
      fn();
    },
    calc(id, spec) {
      calcs.set(id, spec);
      spec.inputs.forEach((i) => { if (!state.has(i)) dash.data(i); });
      queueMicrotask(() => computeCalc(id));
    },
    loader(id, spec) { loaders.set(id, spec); },
    params() { return Object.assign({}, params); },
    setParams(p) { params = Object.assign(params, p); },
    resetParams() { params = {}; },
    refresh(id) { if (defs[id]) load(id); },
    setLink(name) { const el = document.getElementById(name); if (el) el.scrollIntoView({ behavior: "smooth" }); },
  };
  window.dash = dash;
})();
