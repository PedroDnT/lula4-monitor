"""Re-estimate the regressions the Agora page uses, and compare them with the published constants.

Data, daily changes (% for prices, bp for rates), OLS with intercept, Newey-West (HAC) errors:
  global     2019-01 to 2026-09, all days, New York closes (Yahoo): dollar (BRL=X) on EM (mean of
             MXN and ZAR); 2-year DI (B3 PRE 720 via SILO) on EM and US 10y; EWZ on EEM; dollar on
             DXY.                                                           (index.html GLB)
  stress     2018-01 to 2026-09, B3 closes: dollar = most liquid DOL future, settlement via SILO;
             Ibovespa = IBOV via SILO; stocks = B3 line (Yahoo .SA, adjusted). Days with the dollar
             or the DI beyond 2 sd: Ibovespa on dollar (and on dollar + DI), DI on dollar. Days with
             the dollar beyond 2 sd: each stock on dollar.                  (FV, FV2, DIFX, STK)
  fraction   2008-01 to 2026-10, PTAX (SGS 1 via SILO): local shock = dollar - b x EM (b from the
             same sample); days with |local shock| > 2 sd; cumulative dollar change from the day
             before to h sessions after, on the shock (local projection, Jordà 2005), h = 21, 63,
             126, 252.                                                      (scenario 0.75)
Limits: Yahoo (New York) and B3 closes are not simultaneous with the PTAX (about 13:00 Brasília).
Writes data/research/regressions.json. index.html copies the estimates by hand, with this file named.
"""
import json, os, statistics as st
import silo, yahoo

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "research", "regressions.json")
PUBLISHED = {
    "usd_on_em": 0.65, "di_on_em": 4.2, "di_on_ust": 0.34, "ewz_on_eem": 1.07, "usd_on_dxy": 0.43,
    "ibov_on_usd": {"c": -0.11, "b": -0.90, "se": 0.105, "n": 172}, "di_on_usd": {"c": 1.96, "b": 7.11},
    "stocks": {"ITUB": -0.924, "PBR": -0.965, "VALE": -0.58, "BBD": -1.10, "ABEV": -0.59, "SBS": -0.88, "SUZ": 0.19, "BBAS3.SA": -1.35},
    "fraction": {"21": 0.75, "63": 0.76, "126": 0.92, "252": 0.73, "n": 213},
}


# Page key -> B3 ticker on Yahoo. The page reads the ADRs before the B3 opens, converted to reais;
# the betas are estimated on the B3 line, as the published ones were.
STOCKS = {"ITUB": "ITUB4.SA", "PBR": "PETR4.SA", "VALE": "VALE3.SA", "BBD": "BBDC4.SA", "ABEV": "ABEV3.SA",
          "SBS": "SBSP3.SA", "SUZ": "SUZB3.SA", "BBAS3.SA": "BBAS3.SA"}


def solve(A, b):
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def inv(A):
    n = len(A)
    return [list(col) for col in zip(*[solve(A, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)])]


def ols(y, X, lags=5):
    """y on [1, X...]; returns coefficients, HAC standard errors, residual sd and n."""
    Z = [[1.0] + list(x) for x in X]
    k, n = len(Z[0]), len(y)
    ZZ = [[sum(z[i] * z[j] for z in Z) for j in range(k)] for i in range(k)]
    Zy = [sum(z[i] * yy for z, yy in zip(Z, y)) for i in range(k)]
    b = solve(ZZ, Zy)
    e = [yy - sum(bi * zi for bi, zi in zip(b, z)) for z, yy in zip(Z, y)]
    S = [[sum(Z[t][i] * Z[t][j] * e[t] ** 2 for t in range(n)) for j in range(k)] for i in range(k)]
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        for i in range(k):
            for j in range(k):
                s = sum(Z[t][i] * Z[t - L][j] * e[t] * e[t - L] + Z[t - L][i] * Z[t][j] * e[t - L] * e[t] for t in range(L, n))
                S[i][j] += w * s
    Q = inv(ZZ)
    V = [[sum(Q[i][a] * S[a][c] * Q[c][j] for a in range(k) for c in range(k)) for j in range(k)] for i in range(k)]
    return {"coef": [round(x, 4) for x in b], "se": [round(V[i][i] ** 0.5, 4) for i in range(k)],
            "resid_sd": round(st.pstdev(e), 3), "n": n}


def changes(series, kind):
    d = sorted(series)
    out = {}
    for a, b in zip(d, d[1:]):
        out[b] = (series[b] / series[a] - 1) * 100 if kind == "pct" else (series[b] - series[a]) * 100
    return out


def run():
    ptax = silo.macro("USDBRL", 2008)
    # Same-day regressions use the Yahoo dollar (New York close), synchronous with the other
    # Yahoo closes; the PTAX is fixed near 13:00 and halves the measured co-movement.
    usd_l = yahoo.closes("BRL=X", "2008-01-01", "2026-10-31")
    di_l = silo.curve("PRE", 720, 2008)
    ysyms = ["MXN=X", "ZAR=X", "EEM", "EWZ", "DX-Y.NYB", "^TNX"]
    Y = {s: yahoo.closes(s, "2008-01-01", "2026-10-31") for s in ysyms}
    # Changes on the dates both sides have (a missing day on either side drops that day).
    def chg(levels, kind, days):
        lv = {d: levels[d] for d in days if d in levels}
        return changes(lv, kind)
    out = {"method": __doc__.strip(), "published": PUBLISHED}

    # global
    days = sorted(set(usd_l) & set(di_l) & set(Y["MXN=X"]) & set(Y["ZAR=X"]) & set(Y["EEM"]) & set(Y["EWZ"]) & set(Y["DX-Y.NYB"]) & set(Y["^TNX"]))
    days = [d for d in days if "2018-12-28" <= d <= "2026-09-30"]
    c = {"usd": chg(usd_l, "pct", days), "di": chg(di_l, "bp", days), "mxn": chg(Y["MXN=X"], "pct", days), "zar": chg(Y["ZAR=X"], "pct", days),
         "eem": chg(Y["EEM"], "pct", days), "ewz": chg(Y["EWZ"], "pct", days), "dxy": chg(Y["DX-Y.NYB"], "pct", days), "ust": chg(Y["^TNX"], "bp", days)}
    g = [d for d in days[1:] if all(d in c[k] for k in c)]
    em = {d: (c["mxn"][d] + c["zar"][d]) / 2 for d in g}
    out["global"] = {
        "sample": [g[0], g[-1]],
        "usd_on_em": ols([c["usd"][d] for d in g], [[em[d]] for d in g]),
        "di_on_em_ust": ols([c["di"][d] for d in g], [[em[d], c["ust"][d]] for d in g]),
        "ewz_on_eem": ols([c["ewz"][d] for d in g], [[c["eem"][d]] for d in g]),
        "usd_on_dxy": ols([c["usd"][d] for d in g], [[c["dxy"][d]] for d in g]),
    }

    # stress days: dollar = most liquid DOL future (B3 settlement via SILO), as the page's ruler
    days = sorted(di_l)
    days = [d for d in days if "2017-12-28" <= d <= "2026-09-30"]
    u = silo.dol_front(days)
    dd = chg(di_l, "bp", days)
    ibl = {}
    for y in range(2017, 2027):
        for r in silo.rpc("index_history", p_index="IBOV", p_from=f"{y}-01-01", p_to=f"{y}-12-31"):
            ibl[r["trade_date"]] = float(r["level"])
    ib = chg(ibl, "pct", days)
    common = [d for d in days[1:] if d in u and d in dd and d in ib]
    su, sd_ = st.pstdev([u[d] for d in common]), st.pstdev([dd[d] for d in common])
    stress = [d for d in common if abs(u[d]) > 2 * su or abs(dd[d]) > 2 * sd_]
    fx_stress = [d for d in common if abs(u[d]) > 2 * su]
    out["stress"] = {
        "rule": {"usd_sd_pct": round(su, 3), "di_sd_bp": round(sd_, 2), "days": len(stress), "fx_days": len(fx_stress),
                 "usd": "DOL mais líquido (maior contratos em aberto), ajuste B3 via SILO", "ibov": "IBOV, B3 via SILO"},
        "ibov_on_usd": ols([ib[d] for d in stress], [[u[d]] for d in stress], 2),
        "di_on_usd": ols([dd[d] for d in stress], [[u[d]] for d in stress], 2),
        "ibov_on_usd_di": ols([ib[d] for d in stress], [[u[d], dd[d]] for d in stress], 2),
        "stocks": {},
    }
    # Each stock: B3 line (Yahoo .SA, adjusted) on the dollar, dollar-stress days only.
    for adr, b3 in STOCKS.items():
        lv = yahoo.closes(b3, "2008-01-01", "2026-10-31")
        sc = changes({d: lv[d] for d in days if d in lv}, "pct")
        ds = [d for d in fx_stress if d in sc]
        out["stress"]["stocks"][adr] = dict(ols([sc[d] for d in ds], [[u[d]] for d in ds], 2), b3=b3)

    # fraction that remains of a local dollar shock
    days = sorted(set(ptax) & set(Y["MXN=X"]) & set(Y["ZAR=X"]))
    days = [d for d in days if d <= "2026-10-31"]
    lv = [ptax[d] for d in days]
    uc = [None] + [(lv[i] / lv[i - 1] - 1) * 100 for i in range(1, len(days))]
    emc = [None] + [((Y["MXN=X"][days[i]] / Y["MXN=X"][days[i - 1]] - 1) + (Y["ZAR=X"][days[i]] / Y["ZAR=X"][days[i - 1]] - 1)) * 50 for i in range(1, len(days))]
    beta = ols(uc[1:], [[x] for x in emc[1:]])["coef"][1]
    loc = [None] + [uc[i] - beta * emc[i] for i in range(1, len(days))]
    sl = st.pstdev(loc[1:])
    shock = [i for i in range(1, len(days)) if abs(loc[i]) > 2 * sl]
    frac = {"em_beta": round(beta, 3), "local_sd_pct": round(sl, 3), "shock_days": len(shock), "h": {}}
    for h in (21, 63, 126, 252):
        idx = [i for i in shock if i + h < len(days)]
        y = [(lv[i + h] / lv[i - 1] - 1) * 100 for i in idx]
        frac["h"][str(h)] = ols(y, [[loc[i]] for i in idx], h)
    out["fraction"] = frac
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    o = run()
    gl, s, f = o["global"], o["stress"], o["fraction"]
    print("global", gl["sample"], "n", gl["usd_on_em"]["n"])
    print(" usd~em", gl["usd_on_em"]["coef"], "pub 0.65 | di~em,ust", gl["di_on_em_ust"]["coef"], "pub 4.2, 0.34")
    print(" ewz~eem", gl["ewz_on_eem"]["coef"], "pub 1.07 | usd~dxy", gl["usd_on_dxy"]["coef"], "pub 0.43")
    print("stress", s["rule"])
    print(" ibov~usd", s["ibov_on_usd"]["coef"], s["ibov_on_usd"]["se"], "pub -0.11 -0.90 se .105 | di~usd", s["di_on_usd"]["coef"], "pub 1.96 7.11")
    for k, v in s["stocks"].items():
        print(" ", k, v["coef"][1], "se", v["se"][1], "n", v["n"], "pub", PUBLISHED["stocks"][k])
    print("fraction", {k: v for k, v in f.items() if k != "h"})
    for h, v in f["h"].items():
        print(" h", h, v["coef"][1], "se", v["se"][1], "n", v["n"], "pub", PUBLISHED["fraction"][h])
