"""Builds data/lara/*.json for lara.html (cenário Lara Resende).

Run from the repo root: python3 docs/lara/build.py
Downloads monthly series from the BIS SDMX API (policy rate WS_CBPOL,
USD exchange rate WS_XRU, CPI year-on-year WS_LONG_CPI) and writes:
  data/lara/casos.json     event study, months -6..+48 around each case
  data/lara/impactos.json  what each case would mean for Brazil, plus the
                           debt arithmetic of the plan
Brazil inputs (Selic, PTAX, IPCA 12m, DBGG) are read once from SILO and
pinned in BR below with their dates.
"""
import csv, io, json, urllib.request

BIS = "https://stats.bis.org/api/v2/data/dataflow/BIS"
# Brazil today (Dado, SILO api: macro_series SELIC_META, ptax USD, inflation IPCA_12M, macro_series DBGG_PIB)
BR = {"selic": 13.75, "selic_date": "2026-11-01", "ptax": 5.4212, "ptax_date": "2026-10-30",
      "ipca12": 4.58, "ipca_date": "2026-09", "dbgg": 82.93, "dbgg_date": "2026-09",
      "lft_share": 52.74, "lft_date": "2026-08",  # RMD, Tesouro (LFT share of DPF)
      "debt_cost": 12.68, "debt_cost_date": "2026-06"}  # custo médio da dívida, citado por Lara Resende
PASS = {"12": 0.10, "24": 0.16}  # BCB, RPM mar/2026, box de repasse cambial (projeções locais, jul/06-dez/25)
CASES = [
    # id, country, t0 (first month of the cut cycle), peers for the peer-relative FX index
    ("tr2021", "TR", "2021-09", ["MX", "ZA", "CL"]),
    ("br2011", "BR", "2011-08", ["MX", "ZA", "CL"]),
    ("br2019", "BR", "2019-07", ["MX", "ZA", "CL"]),
    ("jp2022", "JP", "2022-03", ["KR", "XM"]),
]

def bis(flow, key):
    url = f"{BIS}/{flow}/1.0/{key}?startPeriod=2010-01&format=csv"
    with urllib.request.urlopen(url, timeout=60) as r:
        rows = csv.DictReader(io.StringIO(r.read().decode()))
        return {x["TIME_PERIOD"]: float(x["OBS_VALUE"]) for x in rows if x["OBS_VALUE"]}

def addm(ym, k):
    y, m = map(int, ym.split("-")); m += k; y += (m - 1) // 12; m = (m - 1) % 12 + 1
    return f"{y:04d}-{m:02d}"

fx = {c: bis("WS_XRU", f"M.{c}..A") for c in ["TR", "BR", "JP", "MX", "ZA", "CL", "KR", "XM"]}
casos, resumo = [], {}
for cid, cc, t0, peers in CASES:
    pol, cpi = bis("WS_CBPOL", f"M.{cc}"), bis("WS_LONG_CPI", f"M.{cc}.771")
    b = addm(t0, -1)
    rows = []
    for k in range(-6, 49):
        ym = addm(t0, k)
        if ym not in fx[cc]:
            continue
        fxi = fx[cc][ym] / fx[cc][b] * 100
        pv = [fx[p][ym] / fx[p][b] for p in peers if ym in fx[p]]
        peer = sum(pv) / len(pv) * 100
        rows.append({"caso": cid, "t": k, "mes": ym, "juro": pol.get(ym), "cambio_idx": round(fxi, 1),
                     "cambio_rel": round(fxi / peer * 100, 1), "inflacao": round(cpi[ym], 2) if ym in cpi else None})
    casos += rows
    at = {r["t"]: r for r in rows}
    hike = next(r["t"] for r in rows[1:] if r["t"] > 0 and r["juro"] > at[r["t"] - 1]["juro"])
    resumo[cid] = {"juro_ini": at[-1]["juro"], "juro_min": min(r["juro"] for r in rows if r["t"] >= 0),
                   "mes_alta": hike, "juro_36": at[36]["juro"], "juro_48": at[48]["juro"] if 48 in at else None,
                   "infl_ini": at[-1]["inflacao"], "infl_12": at[12]["inflacao"], "infl_24": at[24]["inflacao"],
                   "infl_pico": max(r["inflacao"] for r in rows if 0 <= r["t"] <= 36),
                   "cambio_12": at[12]["cambio_idx"], "cambio_24": at[24]["cambio_idx"],
                   "rel_12": at[12]["cambio_rel"], "rel_24": at[24]["cambio_rel"],
                   "juro_real_12": round(at[12]["juro"] - at[12]["inflacao"], 1)}

# Brazil: what each case would mean (Projeção). Dollar = PTAX x peer-relative index; extra inflation = pass-through x depreciation.
imp = []
for cid, s in resumo.items():
    d12, d24 = s["rel_12"] - 100, s["rel_24"] - 100
    if cid == "tr2021":  # de-anchored case: Turkey's own ratio of extra inflation to depreciation in 12 months
        pt12 = round((s["infl_12"] - s["infl_ini"]) / (s["cambio_12"] - 100), 2); pt24 = None
    else:
        pt12, pt24 = PASS["12"], PASS["24"]
    imp.append({"caso": cid, "dolar_12": round(BR["ptax"] * s["rel_12"] / 100, 2), "dolar_24": round(BR["ptax"] * s["rel_24"] / 100, 2),
                "repasse_12": pt12, "infl_extra_12": round(pt12 * d12, 1), "infl_extra_24": round(pt24 * d24, 1) if pt24 else None,
                "mes_alta": s["mes_alta"]})

# Selic paths for Brazil, monthly, 36 months (Projeção)
def plan(k):  # Lara: 13.75 -> 7.5 in 12 months, then -> 5.5 by month 36 (spread falls gradually)
    return BR["selic"] + (7.5 - BR["selic"]) * k / 12 if k <= 12 else 7.5 + (5.5 - 7.5) * (k - 12) / 24
def reverse(at, top, by):  # plan until month `at`, then straight line to `top` by month `by`, then flat
    def f(k):
        if k <= at: return plan(k)
        a = plan(at); return a + (top - a) * min(1, (k - at) / (by - at))
    return f
s = resumo
paths = {
    "plano": plan,
    "br2011": reverse(s["br2011"]["mes_alta"], BR["selic"] * s["br2011"]["juro_48"] / s["br2011"]["juro_ini"], 48),
    "br2019": reverse(s["br2019"]["mes_alta"], BR["selic"] + (s["br2019"]["juro_36"] - s["br2019"]["juro_ini"]), 36),
    "tr2021": reverse(s["tr2021"]["mes_alta"], BR["selic"] * s["tr2021"]["juro_36"] / s["tr2021"]["juro_ini"], 30),
}
selic_rows, divida = [], []
lft = BR["dbgg"] * BR["lft_share"] / 100  # Selic-linked debt, % GDP (DPF share applied to DBGG: Julgamento)
for pid, f in paths.items():
    for k in range(0, 37):
        selic_rows.append({"caminho": pid, "mes": k, "selic": round(f(k), 2)})
    sav = [sum(lft * (BR["selic"] - f(k)) / 100 / 12 for k in range(y * 12 + 1, y * 12 + 13)) for y in range(3)]
    divida.append({"caminho": pid, "ano1": round(sav[0], 2), "ano2": round(sav[1], 2), "ano3": round(sav[2], 2), "total": round(sum(sav), 2)})
lara_full = round(BR["dbgg"] * (BR["debt_cost"] - 7.5) / 100, 2)

json.dump(casos, open("data/lara/casos.json", "w"), ensure_ascii=False)
json.dump({"br": BR, "repasse": PASS, "resumo": resumo, "impactos": imp, "selic": selic_rows,
           "divida": divida, "lft_pib": round(lft, 1), "lara_economia_plena": lara_full},
          open("data/lara/impactos.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({"resumo": resumo, "impactos": imp, "divida": divida, "lft": lft, "lara_full": lara_full}, indent=1))

# ---------------------------------------------------------------------------
# Projection 2027-2030: the monitor's numbers under 3 paths (sem plano, a favor, contra).
# Every parameter below carries its source in PREMISSAS (shown on the page).
P = {
    "g_real": 2.5,          # Lara Resende (2026): crescimento real potencial; igual nos 3 caminhos
    "pb": 0.52,             # déficit primário 12m, % PIB, set/26 (BCB SGS 5793, SILO); constante: sem mudança de política
    "nfsp_nom": 9.51,       # déficit nominal 12m, % PIB, set/26 (BCB SGS 5727, SILO)
    "matur": 3.8,           # prazo médio da DPF, anos (Tesouro, PAF 2026): parte não Selic que rola por ano = 1/3.8
    "rho_hoje": 7.97,       # juro real de 5 anos (DPL 1800 dias, B3, SILO, 30/10/2026)
    "rho_favor": 2.5,       # Lara Resende (2026): juro real converge ao crescimento real
    "selic_ipca": 0.27,     # BCB (2024), RI jun/24: +1 p.p. de Selic por 4 trimestres tira 0,27 p.p. do IPCA em 4 trimestres
    "pressao": 1.25,        # Drechsel (2024): choque de pressão política eleva o nível de preços em 5% em 4 anos -> 1,25 p.p./ano
    "meta": 3.0,            # CMN: meta de inflação
    "comp": {"selic": 52.74, "ipca": 23.22, "pre": 20.31, "cambio": 3.74},  # Tesouro (2026), RMD ago/26: composição da DPF, %
    "cupom_usd": 6.0,       # custo em dólar da dívida externa, % a.a. (julgamento); soma-se a desvalorização do ano
    "neutro_real": 5.0,     # BCB (2026), RPM jun/26: juro real neutro de 5,0%
    "meses_neutro": 36,     # sem plano: a Selic chega ao neutro nominal (5,0 + 3,0) em 36 meses, em linha reta (julgamento)
}
YEARS = [2027, 2028, 2029, 2030]

def monthly(path_fn, n=48):
    return [path_fn(k) for k in range(1, n + 1)]

def contra_selic(k):  # plano até o mês da 1ª alta de Brasil 2011 (20), depois sobe na proporção de 2011 (12,5 -> 14,25) até o mês 48
    at, top = resumo["br2011"]["mes_alta"], BR["selic"] * resumo["br2011"]["juro_48"] / resumo["br2011"]["juro_ini"]
    if k <= at: return plan(k)
    a = plan(at); return a + (top - a) * min(1, (k - at) / (48 - at))
def plan48(k): return plan(k) if k <= 36 else 5.5
def base_selic(k):
    alvo = P["neutro_real"] + P["meta"]
    return BR["selic"] + (alvo - BR["selic"]) * min(1, k / P["meses_neutro"])
SEL = {"sem": monthly(base_selic), "favor": monthly(plan48), "contra": monthly(contra_selic)}

# dólar no fim de cada ano
br11 = {r["t"]: r for r in casos if r["caso"] == "br2011"}
FX = {"sem": [BR["ptax"]] * 4, "favor": [BR["ptax"]] * 4,
      "contra": [round(BR["ptax"] * br11[m]["cambio_rel"] / 100, 2) for m in (12, 24, 36, 48)]}

def base_infl(i):  # sem plano: IPCA converge da taxa de hoje à meta em 3 anos (linha reta), depois fica na meta
    return max(P["meta"], BR["ipca12"] + (P["meta"] - BR["ipca12"]) * (i + 1) / 3)

proj = {}
C = {k: v / 100 for k, v in P["comp"].items()}
# custo inicial: juro real do estoque de NTN-B e de prefixados (mesmo juro real, julgamento) calibrado para dar o custo médio de hoje
c_real0 = (BR["debt_cost"] - C["selic"] * BR["selic"] - C["cambio"] * P["cupom_usd"]) / (C["ipca"] + C["pre"]) - BR["ipca12"]
P["c_real0"] = round(c_real0, 2)
for pid in ("sem", "favor", "contra"):
    d, c_real, c_pre = BR["dbgg"], c_real0, c_real0 + BR["ipca12"]
    rows, prev_fx, dep_prev = [], BR["ptax"], 0.0
    for i, y in enumerate(YEARS):
        sel = SEL[pid][i * 12:(i + 1) * 12]
        sel_avg, sel_end = sum(sel) / 12, sel[-1]
        fx_end = FX[pid][i]; dep = (fx_end / prev_fx - 1) * 100
        pi = base_infl(i)
        if pid == "contra":
            pi += P["selic_ipca"] * (BR["selic"] - sel_avg)                 # canal da demanda (BCB, 2024)
            pi += PASS["12"] * dep + (PASS["24"] - PASS["12"]) * dep_prev    # repasse cambial (BCB, 2026)
            pi += P["pressao"]                                                # pressão política sobre o BC (Drechsel, 2024)
        rho = P["rho_favor"] if pid == "favor" else P["rho_hoje"]
        c_real += (rho - c_real) / P["matur"]                 # NTN-B: o estoque rola para o juro real novo
        c_pre += (rho + pi - c_pre) / P["matur"]              # prefixados: rolam para juro real novo + inflação
        r = C["selic"] * sel_avg + C["ipca"] * (c_real + pi) + C["pre"] * c_pre + C["cambio"] * (P["cupom_usd"] + dep)
        g = ((1 + P["g_real"] / 100) * (1 + pi / 100) - 1) * 100
        juros = d * r / 100 / (1 + g / 100)
        estab = d * (r - g) / 100 / (1 + g / 100)
        d_new = d * (1 + r / 100) / (1 + g / 100) + P["pb"]
        rows.append({"ano": y, "selic_media": round(sel_avg, 2), "selic_fim": round(sel_end, 2), "dolar": round(fx_end, 2),
                     "ipca": round(pi, 2), "juro_real": round(sel_avg - pi, 2), "r": round(r, 2), "g": round(g, 2),
                     "r_menos_g": round(r - g, 2), "juros_pib": round(juros, 2), "deficit_nominal": round(juros + P["pb"], 2),
                     "primario_estab": round(estab, 2), "divida": round(d_new, 2)})
        d, prev_fx, dep_prev = d_new, fx_end, dep
    proj[pid] = rows

# hoje, pelo mesmo método
g0 = ((1 + P["g_real"] / 100) * (1 + BR["ipca12"] / 100) - 1) * 100
hoje = {"selic_media": BR["selic"], "selic_fim": BR["selic"], "dolar": BR["ptax"], "ipca": BR["ipca12"],
        "juro_real": round(BR["selic"] - BR["ipca12"], 2), "r": BR["debt_cost"], "g": round(g0, 2),
        "r_menos_g": round(BR["debt_cost"] - g0, 2), "juros_pib": round(BR["dbgg"] * BR["debt_cost"] / 100 / (1 + g0 / 100), 2),
        "deficit_nominal": P["nfsp_nom"], "primario_estab": round(BR["dbgg"] * (BR["debt_cost"] - g0) / 100 / (1 + g0 / 100), 2),
        "divida": BR["dbgg"]}

# DI jan/29 que cada caminho implica (CDI médio composto nov/26 a dez/28 = 26 meses; CDI = Selic - 0,10)
def di29(pid):
    f = 1.0
    for k in range(26):
        x = BR["selic"] if k == 0 else SEL[pid][k - 1]
        f *= (1 + (x - 0.10) / 100) ** (1 / 12)
    return round((f ** (12 / 26) - 1) * 100, 2)
di = {pid: di29(pid) for pid in SEL}

json.dump({"br": BR, "param": P, "repasse": PASS, "hoje": hoje, "proj": proj, "di29": di,
           "selic_mensal": {k: [round(x, 2) for x in v] for k, v in SEL.items()}},
          open("data/lara/projecao.json", "w"), ensure_ascii=False, indent=1)
for pid, rows in proj.items():
    print(pid, di[pid])
    for r in rows: print("  ", r)
print("hoje", hoje)
