// Simulador da dívida com todos os canais: pacote (PLP 299/2026), Selic e inflação.
// One script for Panorama fiscal and Projeção PLP 299/2026, so both pages show the same numbers.
// Usage: <div class="fs" data-sim></div><script src="assets/sim.js" defer></script>
(function () {
const SILO = "https://zcjbtpxuhdekpwcxmepn.supabase.co/rest/v1/rpc/";
const HDR = { apikey: "sb_publishable__yfFQsykAglrvc9GS6_PYw_B24ex437", "Accept-Profile": "api", "Content-Profile": "api", "Content-Type": "application/json" };
// Per 1 p.p. for 12 months (data/dominancia/canais.json; NTN-B unrounded as on Panorama fiscal).
const K = { ipca_ntnb: 3.162, inpc_benef: 13.5, ipca_teto: 23.9, ploa_ipca: 3.6 };
const nf = (d) => new Intl.NumberFormat("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
const sg = (v, d = 1) => (Math.abs(v) < 0.5 * Math.pow(10, -d) ? "" : v > 0 ? "+" : "−") + nf(d).format(Math.abs(v));
const bi = (v) => (v < 0 ? "− " : "") + "R$ " + nf(1).format(Math.abs(v)) + " bi";
const dmy = (iso) => iso.slice(0, 10).split("-").reverse().join("/");
const monthName = (m) => ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][Number(m.slice(5, 7)) - 1] + "/" + m.slice(0, 4);
const rpc = (tool, args) => fetch(SILO + tool, { method: "POST", headers: HDR, body: JSON.stringify(args) }).then((r) => { if (!r.ok) throw new Error("SILO " + r.status); return r.json(); });
const file = (u) => fetch(u, { cache: "no-cache" }).then((r) => { if (!r.ok) throw new Error(u + " " + r.status); return r.json(); });
const series = (s) => rpc("macro_series", { p_series: s, p_from: "2023-01-01" }).then((rows) => new Map(rows.filter((r) => r.value !== null).map((r) => [r.reference_date.slice(0, 7), Number(r.value)])));
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt !== undefined) e.textContent = txt; return e; };
function back(m, k) { const [y, mo] = m.split("-").map(Number); const t = y * 12 + mo - 1 - k; return `${Math.floor(t / 12)}-${String(t % 12 + 1).padStart(2, "0")}`; }
// The same debt arithmetic as Panorama fiscal: r = net interest 12m / average gross debt, g = nominal GDP 12m growth.
function debtNow(D, P, N, Y) {
  const gdp12 = (m) => { let s = 0; for (let k = 0; k < 12; k++) { const v = Y.get(back(m, k)); if (v === undefined) return null; s += v; } return s; };
  const months = [...D.keys()].filter((m) => P.has(m) && N.has(m) && D.has(back(m, 12)) && gdp12(m) && gdp12(back(m, 12))).sort();
  if (!months.length) return null;
  const m = months[months.length - 1], d = D.get(m), d0 = D.get(back(m, 12)), p = P.get(m), n = N.get(m);
  return { month: m, d, r: (n - p) / ((d + d0) / 2) * 100, g: (gdp12(m) / gdp12(back(m, 12)) - 1) * 100, primary: -p };
}
function path(d0, r, g, prim) { const out = [d0]; let d = d0; for (const p of prim) { d = d * (1 + r / 100) / (1 + g / 100) - p; out.push(d); } return out; }

const CSS = `
.fs-say { font-size: 16.5px; line-height: 1.5; margin: 0 0 12px; max-width: 72ch; }
.fs-grid { display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 7fr); gap: 20px; align-items: start; }
.fs-ctl fieldset { border: 0; border-top: 1px solid var(--color-border-line); padding: 10px 0 2px; margin: 0 0 6px; display: grid; gap: 12px; }
.fs-ctl legend { font-size: 12px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; color: var(--color-fg-muted); padding: 0 8px 0 0; }
.fs-ctl label { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 2px 10px; font-size: 14.5px; align-items: baseline; }
.fs-ctl output { font-weight: 600; font-variant-numeric: tabular-nums; }
.fs-ctl small { grid-column: 1 / -1; color: var(--color-fg-muted); font-size: 12.5px; line-height: 1.45; }
.fs-ctl input[type=range] { grid-column: 1 / -1; width: 100%; min-height: 28px; accent-color: var(--color-accent); }
.fs-ctl button { font: inherit; font-size: 13px; padding: 4px 12px; border-radius: 999px; border: 1px solid var(--color-border); background: var(--color-panel); color: var(--color-fg); cursor: pointer; }
.fs-ctl button:disabled { opacity: .5; cursor: default; }
.fs-fig svg { width: 100%; height: auto; display: block; overflow: visible; }
.fs-fig text { font-size: 12px; fill: var(--color-fg-muted); font-family: var(--font-anthropic-sans); font-variant-numeric: tabular-nums; }
.fs-fig .lbl { fill: var(--color-fg); }
.fs-key { display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: 13px; margin: 6px 0 0; }
.fs-key i { display: inline-block; width: 14px; height: 3px; border-radius: 2px; vertical-align: middle; margin-right: 6px; }
.fs h3 { font-size: 15px; margin: 18px 0 4px; }
.fs .fs-note { font-size: 14px; margin: 4px 0 6px; max-width: 80ch; }
.fs-tbl { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; font-size: 14px; margin: 10px 0 4px; }
.fs-tbl th { text-align: left; font-size: 12px; font-weight: 600; color: var(--color-fg-muted); padding: 6px 8px 6px 0; border-bottom: 1px solid var(--color-border-line); }
.fs-tbl td { padding: 7px 8px 7px 0; border-bottom: 1px solid var(--color-border-line); }
.fs-tbl tr:last-child td { border-bottom: 0; }
.fs-tbl .n { text-align: right; white-space: nowrap; padding-right: 0; padding-left: 10px; }
.fs-tbl .sw { display: inline-block; width: 10px; height: 3px; border-radius: 2px; vertical-align: middle; margin-right: 6px; }
.fs-src { font-size: 12.5px; color: var(--color-fg-muted); margin: 10px 0 0; max-width: 100ch; line-height: 1.55; }
.fs-na { color: var(--color-fg-muted); }
@media (max-width: 860px) { .fs-grid { grid-template-columns: minmax(0, 1fr); } }
`;
const COL = { base: "var(--color-bad)", sim: "var(--color-accent)", comp: "var(--color-ok)", plp: "var(--color-accent)", selic: "var(--color-warn)", ipca: "var(--color-sim)" };

function svg(W, H, label) {
  const NS = "http://www.w3.org/2000/svg", s = document.createElementNS(NS, "svg");
  s.setAttribute("viewBox", `0 0 ${W} ${H}`); s.setAttribute("role", "img"); s.setAttribute("aria-label", label);
  s.add = (tag, at, txt) => { const e = document.createElementNS(NS, tag); Object.entries(at).forEach(([k, v]) => e.setAttribute(k, v)); if (txt !== undefined) e.textContent = txt; s.append(e); return e; };
  return s;
}

function mount(root) {
  if (!document.getElementById("fs-css")) { const st = el("style"); st.id = "fs-css"; st.textContent = CSS; document.head.append(st); }
  root.replaceChildren(el("p", "fs-say fs-na", "Carregando as séries do BCB pelo SILO…"));
  Promise.all([file("data/plano/medidas.json"), file("data/dominancia/budget.json"), file("data/dominancia/lft.json"), file("data/dominancia/rolagem.json"),
    file("data/dominancia/scenarios.json"), file("data/relatorio/pesos.json"),
    Promise.all(["DBGG_PIB", "NFSP_PRIMARIO_12M", "NFSP_NOMINAL_12M", "PIB"].map(series)),
    rpc("macro_series", { p_series: "SELIC_META", p_from: new Date(Date.now() - 20 * 864e5).toISOString().slice(0, 10) }),
    rpc("inflation", { p_series: "IPCA_12M", p_from: new Date(Date.now() - 200 * 864e5).toISOString().slice(0, 10) }),
    rpc("focus_expectations", { p_endpoint: "ExpectativasMercadoAnuais", p_horizon: String(new Date().getFullYear() + 1), p_indicator: "IPCA", p_from: new Date(Date.now() - 40 * 864e5).toISOString().slice(0, 10) })])
    .then(([P, B, lft, rol, sc, pw, s, selic, ipca, focus]) => build(root, { P, B: Object.fromEntries(B.map((r) => [r.id, r])), lft, rol, sc, pw, f: debtNow(...s), selic, ipca, focus }))
    .catch((e) => { root.replaceChildren(el("p", "fs-say fs-na", "O simulador não carregou agora (" + e.message + ").")); });
}

function build(root, X) {
  const { P, B, f } = X;
  if (!f) { root.replaceChildren(el("p", "fs-say fs-na", "As séries da dívida não carregaram agora.")); return; }
  const last = (a) => a[a.length - 1];
  const pib = B.meta_centro.valor_bi / (B.meta_centro.pct_pib / 100);
  // Share of the debt whose rate changes within a year: floating (LFT) + the fixed part maturing in 12 months, spread evenly.
  const lftS = last(X.lft).floating_share_dpf, venc = last(X.rol).vincendo_12m_pct, rep = lftS / 100 + venc / 100 * (1 - lftS / 100);
  const selicNow = Number(last(X.selic).value), selicDate = last(X.selic).reference_date;
  const ipcaNow = Number(last(X.ipca).value), ipcaMonth = last(X.ipca).reference_date.slice(0, 7);
  const fo = last(X.focus), focusIpca = fo ? Number(fo.median) : null;
  const scen = Object.fromEntries(X.sc.map((r) => [r.id, r])), w = X.pw.map((r) => ({ id: r.id, p: r.probability, s: scen[r.id] ? scen[r.id].selic_end2027 : null })).filter((r) => r.s != null);
  const wsum = w.reduce((a, r) => a + r.p, 0), selicExp = w.reduce((a, r) => a + r.p * r.s, 0) / wsum;
  const lo = Math.min(...P.impacto_2027.map((x) => x.min_bi)), hi = Math.max(...P.impacto_2027.map((x) => x.max_bi));
  const Q = P.premissas, rPlp = Math.max(0, -Q.di_reacao.bp / 100 * rep);
  const DEF = { imp: Math.round((lo + hi) / 2), gat: Q.gatilhos.valor_bi, rplp: Number(rPlp.toFixed(2)), selic: Math.round(selicExp * 4) / 4, ipca: focusIpca != null ? Math.round(focusIpca * 10) / 10 : ipcaNow };
  const pct = (v) => nf(0).format(v * 100) + "%";

  const ctl = el("div", "fs-ctl");
  const inputs = {};
  const group = (title, items) => { const fs = el("fieldset"); fs.append(el("legend", "", title)); items.forEach(([id, name, min, max, step, base]) => {
    const l = el("label"); const o = el("output"); const i = el("input"); Object.assign(i, { type: "range", min, max, step }); i.setAttribute("aria-label", name);
    const b = el("small", "", base); l.append(document.createTextNode(name + " "), o, i, b); fs.append(l); inputs[id] = { i, o }; }); ctl.append(fs); };
  group("Pacote PLP 299/2026", [
    ["imp", "Impacto em 2027", 0, 100, 1, `Provável: R$ ${DEF.imp} bi, o meio da faixa de R$ ${nf(1).format(lo)} a ${nf(1).format(hi)} bi do parecer e do governo (Dado). Zero = rejeitado.`],
    ["gat", "Gatilhos a partir de 2028", 0, 20, 0.1, `Provável: R$ ${nf(1).format(DEF.gat)} bi por ano, estimativa do governo no PLOA (${Q.gatilhos.fonte}).`],
    ["rplp", "Queda do juro pelo pacote", 0, 1.5, 0.01, `Provável: ${nf(2).format(rPlp)} p.p. O ${Q.di_reacao.ticker} caiu ${nf(0).format(-Q.di_reacao.bp)} bp em ${dmy(Q.di_reacao.data)} (B3 pelo SILO) × ${pct(rep)} da dívida que muda de taxa em 1 ano (Cálculo).`]]);
  group("Juros", [
    ["selic", "Selic até 2030", 8, 18, 0.25, `Provável: ${nf(2).format(DEF.selic)}%, a Selic de fim de 2027 dos 3 cenários pesada pelos pesos de agora (Cálculo). Hoje: ${nf(2).format(selicNow)}% (BCB pelo SILO, ${dmy(selicDate)}). A diferença muda o juro da dívida em ${pct(rep)} dela (LFT ${nf(1).format(lftS)}% + vencimentos de 12 meses ${nf(1).format(venc)}%, Tesouro).`]]);
  group("Inflação", [
    ["ipca", "IPCA até 2030", 2, 9, 0.1, focusIpca != null ? `Provável: ${nf(1).format(DEF.ipca)}%, a mediana do Focus para ${fo.horizon} (${dmy(fo.survey_date)}, BCB pelo SILO). Hoje: ${nf(2).format(ipcaNow)}% em 12 meses (${monthName(ipcaMonth)}). O PLOA usa ${nf(1).format(K.ploa_ipca)}%.` : `Focus indisponível agora; o controle abre no IPCA de 12 meses, ${nf(2).format(ipcaNow)}%.`]]);
  const reset = el("button", "", "Voltar aos valores prováveis"); reset.type = "button"; ctl.append(reset);

  const say = el("p", "fs-say"), chart = el("div", "fs-fig"), key = el("div", "fs-key");
  const tbl = el("table", "fs-tbl"); tbl.innerHTML = '<thead><tr><th>Dívida bruta, % do PIB</th><th class="n">2027</th><th class="n">2028</th><th class="n">2029</th><th class="n">2030</th></tr></thead><tbody></tbody>';
  const chH = el("h3", "", "O que cada canal faz com a dívida de 2030"), chN = el("p", "fs-note"), chFig = el("div", "fs-fig");
  const cH = el("h3", "", "O tamanho da conta de 2027 contra o gasto que se pode cortar"), cN = el("p", "fs-note"), cFig = el("div", "fs-fig");
  const tH = el("h3", "", "Dentro do teto: inflação, benefícios e espaço das discricionárias"), tN = el("p", "fs-note");
  const src = el("p", "fs-src");
  src.innerHTML = '<span class="tag tag-sim">Projeção</span> Dívida do ano seguinte = dívida × (1 + r) ÷ (1 + g) − primário, com r e g fixos a partir do último dado do BCB (pelo <b>SILO</b>). '
    + '<span class="tag tag-calc">Cálculo</span> Selic: a diferença para a de hoje muda r na parte da dívida que muda de taxa em 1 ano. IPCA: a diferença para o de hoje soma ao crescimento nominal g e encarece a NTN-B em R$ 3,2 bi por p.p. (PLDO 2027, Anexo de Riscos Fiscais). '
    + '<span class="tag tag-jul">Julgamento</span> O deflator do PIB segue o IPCA; o primário em % do PIB não muda com a inflação, porque receita e teto sobem com os preços; o pacote cresce com o PIB nominal depois de 2027. '
    + '<span class="tag tag-dado">Dado</span> Discricionárias e bloqueio da IFI: PLOA 2027 (Ipea) e IFI, RAF 116. Compromisso de 1,5% do PIB em 2030: declaração do presidente.';
  const grid = el("div", "fs-grid"), right = el("div"); right.append(chart, key); grid.append(ctl, right);
  root.replaceChildren(say, grid, tbl, chH, chN, chFig, cH, cN, cFig, tH, tN, src);

  const set = (v) => Object.entries(v).forEach(([k, x]) => { inputs[k].i.value = x; });
  set(DEF);
  const c27 = P.compromisso.primario_2027_pct_pib, c30 = P.compromisso.primario_2030_pct_pib;
  const pibY = (k, g) => pib * Math.pow(1 + g / 100, k);
  function run(v) {
    const dr = -v.rplp + (v.selic - selicNow) * rep + K.ipca_ntnb * (v.ipca - ipcaNow) / (f.d / 100 * pib) * 100;
    const r = f.r + dr, g = f.g + (v.ipca - ipcaNow);
    const prim = [0, 1, 2, 3].map((k) => f.primary + v.imp / pib * 100 + (k ? v.gat / pibY(k, g) * 100 : 0));
    return { r, g, prim, d: path(f.d, r, g, prim) };
  }
  const ZERO = { imp: 0, gat: 0, rplp: 0, selic: selicNow, ipca: ipcaNow };

  function draw() {
    const v = Object.fromEntries(Object.entries(inputs).map(([k, x]) => [k, Number(x.i.value)]));
    inputs.imp.o.textContent = `R$ ${nf(0).format(v.imp)} bi`; inputs.gat.o.textContent = `R$ ${nf(1).format(v.gat)} bi/ano`; inputs.rplp.o.textContent = `${nf(2).format(v.rplp)} p.p.`;
    inputs.selic.o.textContent = `${nf(2).format(v.selic)}%`; inputs.ipca.o.textContent = `${nf(1).format(v.ipca)}%`;
    reset.disabled = Object.keys(DEF).every((k) => Math.abs(v[k] - DEF[k]) < 1e-9);
    const base = run(ZERO), sim = run(v);
    const comp = path(f.d, sim.r, sim.g, [0, 1, 2, 3].map((k) => c27 + (c30 - c27) * k / 3));
    const L = [["Hoje mantido: sem pacote, Selic e IPCA de hoje", base.d, COL.base], ["Com os canais escolhidos", sim.d, COL.sim], [`Compromisso: ${nf(1).format(c27)}% em 2027 até ${nf(1).format(c30)}% em 2030`, comp, COL.comp]];
    // Debt paths
    const all = L.flatMap((l) => l[1]), lo2 = Math.floor(Math.min(...all) - 1), hi2 = Math.ceil(Math.max(...all) + 1);
    const W = Math.max(300, Math.min(720, chart.clientWidth || 560)), H = W < 500 ? 240 : 290, m = { l: 40, r: 40, t: 12, b: 26 };
    const x = (i) => m.l + i * (W - m.l - m.r) / 4, y = (q) => m.t + (hi2 - q) * (H - m.t - m.b) / (hi2 - lo2);
    const s = svg(W, H, "Dívida bruta em % do PIB, de 2026 a 2030");
    const step = (hi2 - lo2) > 16 ? 4 : 2;
    for (let q = Math.ceil(lo2 / step) * step; q <= hi2; q += step) { s.add("line", { x1: m.l, x2: W - m.r, y1: y(q), y2: y(q), stroke: "var(--color-border-line)" }); s.add("text", { x: m.l - 6, y: y(q) + 4, "text-anchor": "end" }, q + "%"); }
    [2026, 2027, 2028, 2029, 2030].forEach((yr, i) => s.add("text", { x: x(i), y: H - 6, "text-anchor": "middle" }, yr));
    L.forEach(([, d, c]) => s.add("path", { fill: "none", "stroke-width": 2.25, stroke: c, d: d.map((p, i) => (i ? "L" : "M") + x(i) + " " + y(p)).join(" ") }));
    const ends = L.map(([, d, c]) => ({ y: y(d[4]), v: d[4], c })).sort((a, b) => a.y - b.y);
    for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 14) ends[i].y = ends[i - 1].y + 14;
    ends.forEach((e) => s.add("text", { x: x(4) + 6, y: e.y + 4, style: "fill:" + e.c + ";font-weight:600" }, nf(1).format(e.v)));
    chart.replaceChildren(s);
    key.replaceChildren(...L.map(([n, , c]) => { const k = el("span"); const i = el("i"); i.style.background = c; k.append(i, document.createTextNode(n)); return k; }));
    tbl.tBodies[0].replaceChildren(...L.map(([n, d, c]) => { const tr = el("tr"); const a = el("td"); const sw = el("i", "sw"); sw.style.background = c; a.append(sw, document.createTextNode(n)); tr.append(a, ...d.slice(1).map((p) => el("td", "n", nf(1).format(p)))); return tr; }));
    // Each channel alone, against "today kept".
    const ch = [["Pacote PLP 299/2026", { ...ZERO, imp: v.imp, gat: v.gat, rplp: v.rplp }, COL.plp], ["Selic", { ...ZERO, selic: v.selic }, COL.selic], ["Inflação", { ...ZERO, ipca: v.ipca }, COL.ipca]]
      .map(([n, z, c]) => ({ n, c, dv: run(z).d[4] - base.d[4] }));
    const tot = sim.d[4] - base.d[4], inter = tot - ch.reduce((a, q) => a + q.dv, 0);
    const rows = ch.concat(Math.abs(inter) >= 0.05 ? [{ n: "Interação entre os canais", c: "var(--color-fg-muted)", dv: inter }] : []).concat([{ n: "Todos juntos", c: "var(--color-fg)", dv: tot, b: true }]);
    {
      const W2 = Math.max(300, Math.min(900, chFig.clientWidth || 700)), narrow = W2 < 520, lab = narrow ? 0 : 190, bar = 18, gap = narrow ? 24 : 10, top = 4, H2 = top + rows.length * (bar + gap) + 20;
      const mn = Math.min(-0.5, ...rows.map((q) => q.dv)) * 1.15, mx = Math.max(0.5, ...rows.map((q) => q.dv)) * 1.15, xs = (q) => lab + 60 + (q - mn) * (W2 - lab - 120) / (mx - mn);
      const s2 = svg(W2, H2, "Mudança da dívida de 2030 por canal, em pontos do PIB");
      s2.add("line", { x1: xs(0), x2: xs(0), y1: narrow ? 14 : 0, y2: H2 - 18, stroke: "var(--color-fg-muted)" });
      s2.add("text", { x: xs(0) - 6, y: H2 - 4, "text-anchor": "end" }, "← menor"); s2.add("text", { x: xs(0) + 6, y: H2 - 4, "text-anchor": "start" }, "maior →");
      rows.forEach((q, k) => {
        const yy = top + k * (bar + gap) + (narrow ? 14 : 0);
        s2.add("text", narrow ? { x: 0, y: yy - 4, class: "lbl" } : { x: lab, y: yy + bar / 2 + 4, "text-anchor": "end", class: "lbl" }, q.n).style.fontWeight = q.b ? 700 : 400;
        s2.add("rect", { x: Math.min(xs(0), xs(q.dv)), y: yy, width: Math.max(1, Math.abs(xs(q.dv) - xs(0))), height: bar, rx: 3, fill: q.c, opacity: q.b ? 1 : 0.85 });
        s2.add("text", { x: q.dv < 0 ? xs(q.dv) - 4 : xs(q.dv) + 4, y: yy + bar / 2 + 4, "text-anchor": q.dv < 0 ? "end" : "start" }, sg(q.dv) + " p.p.");
      });
      chFig.replaceChildren(s2);
    }
    chN.textContent = `Cada barra liga só um canal, com os outros no valor de hoje, e mede a dívida de 2030 contra a linha "hoje mantido" (${nf(1).format(base.d[4])}% do PIB). Selic e inflação valem a partir do valor de hoje, não do PLOA.`;
    // The 2027 bill against what can be cut.
    const stab = f.d * (sim.r - sim.g) / (100 + sim.g), p27 = sim.prim[0], gapPct = stab - p27, gapBi = gapPct / 100 * pib;
    const disc = B.discricionarias.valor_bi, ifi = B.contingenciamento_ifi.valor_bi;
    const bars = [["Superávit que estabiliza a dívida", stab / 100 * pib, "var(--color-fg-muted)"], ["Primário com o pacote", p27 / 100 * pib, COL.plp], ["Falta", gapBi, COL.base], ["Todas as discricionárias", disc, "var(--color-ok)"], ["Bloqueio estimado pela IFI", ifi, "var(--color-ok)"]];
    {
      const W3 = Math.max(300, Math.min(900, cFig.clientWidth || 700)), narrow = W3 < 520, lab = narrow ? 0 : 230, bar = 18, gap = narrow ? 24 : 10, top = 4, H3 = top + bars.length * (bar + gap) + 4;
      const mn = Math.min(0, ...bars.map((b) => b[1])), mx = Math.max(...bars.map((b) => b[1])) * 1.15, xs = (q) => lab + 8 + (q - mn) * (W3 - lab - 70) / (mx - mn);
      const s3 = svg(W3, H3, "A conta de 2027 contra o gasto discricionário, em R$ bilhões");
      s3.add("line", { x1: xs(0), x2: xs(0), y1: narrow ? 14 : 0, y2: H3, stroke: "var(--color-fg-muted)" });
      bars.forEach(([n, q, c], k) => {
        const yy = top + k * (bar + gap) + (narrow ? 14 : 0);
        s3.add("text", narrow ? { x: 0, y: yy - 4, class: "lbl" } : { x: lab, y: yy + bar / 2 + 4, "text-anchor": "end", class: "lbl" }, n);
        s3.add("rect", { x: Math.min(xs(0), xs(q)), y: yy, width: Math.max(1, Math.abs(xs(q) - xs(0))), height: bar, rx: 3, fill: c });
        s3.add("text", { x: Math.max(xs(0), xs(q)) + 4, y: yy + bar / 2 + 4 }, bi(q));
      });
      cFig.replaceChildren(s3);
    }
    cN.textContent = gapBi > 0
      ? `Com os canais escolhidos, a dívida para de subir com um superávit de ${nf(1).format(stab)}% do PIB em 2027. O primário com o pacote é de ${sg(p27, 2)}% (setor público, 12 meses até ${monthName(f.month)}, mais o pacote). Faltam ${bi(gapBi)}: ${gapBi > disc ? "mais que todo o gasto discricionário do PLOA" : nf(0).format(gapBi / disc * 100) + "% de todo o gasto discricionário do PLOA"} e ${nf(1).format(gapBi / ifi)} vezes o bloqueio que a IFI estima.`
      : `Com os canais escolhidos, o primário de 2027 já estabiliza a dívida: sobram ${bi(-gapBi)}.`;
    const dpi = v.ipca - K.ploa_ipca, teto = K.ipca_teto * dpi, ben = K.inpc_benef * dpi;
    tN.textContent = Math.abs(dpi) < 0.05 ? `Com o IPCA igual aos ${nf(1).format(K.ploa_ipca)}% do PLOA, o teto e os benefícios ficam como no Orçamento.`
      : `Com o IPCA ${dpi > 0 ? "acima" : "abaixo"} dos ${nf(1).format(K.ploa_ipca)}% do PLOA em ${nf(1).format(Math.abs(dpi))} p.p., o teto ${dpi > 0 ? "sobe" : "cai"} ${bi(Math.abs(teto))} no ano seguinte e os benefícios ligados ao salário mínimo ${dpi > 0 ? "sobem" : "caem"} ${bi(Math.abs(ben))}. O espaço das discricionárias ${teto - ben >= 0 === dpi > 0 ? "aumenta" : "diminui"} ${bi(Math.abs(teto - ben))}. Esse efeito fica dentro do teto e não muda a conta da dívida acima.`;
    say.textContent = `Com estes valores, a dívida bruta chega a ${nf(1).format(sim.d[4])}% do PIB em 2030, contra ${nf(1).format(base.d[4])}% se tudo ficar como hoje (${nf(1).format(f.d)}% em ${monthName(f.month)}). Juro implícito de ${nf(1).format(sim.r)}% e crescimento nominal de ${nf(1).format(sim.g)}% (hoje: ${nf(1).format(f.r)}% e ${nf(1).format(f.g)}%).`;
  }
  Object.values(inputs).forEach(({ i }) => i.addEventListener("input", draw));
  reset.addEventListener("click", () => { set(DEF); draw(); });
  let t; addEventListener("resize", () => { clearTimeout(t); t = setTimeout(draw, 120); });
  draw();
}

function init() { document.querySelectorAll("[data-sim]").forEach(mount); }
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
