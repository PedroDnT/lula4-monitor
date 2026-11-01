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
