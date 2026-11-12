"""Calibration of the Fiscal-tab alarm rules on past crises.

Crisis: the 2-year DI (PRE 720) rises more than 200 bp, or the dollar (SGS 1) rises more than
15%, over 60 sessions. The crisis starts on the first session where either 60-session change
crosses its line; a new crisis needs more than 60 sessions without a crossing.
Rules tested (each on its own):
  be2_50   2-year implied inflation up more than 50 bp in 20 sessions
  be5_50   5-year implied inflation up more than 50 bp in 20 sessions
  r5_gt5   5-year real rate (DPL 1800) above 5.00%
  r5_gt7   5-year real rate above 7.00%
  r5_50    5-year real rate up more than 50 bp in 20 sessions
Implied inflation = (1 + PRE) / (1 + DPL) - 1 at 720 and 1800 days (B3 curves via SILO).
"Avisou": the rule was on at least once in the 60 sessions before the crisis start.
"Antecedência": sessions from the first such day to the start (median over hits).
"Aceso em calma": share of calm sessions with the rule on. Calm = farther than 60 sessions
from any crisis window (start - 60 to start + 60).
Limit: crisis and market rules come from the same curves, so the test favours those rules.
Writes data/research/calibration.json.
"""
import json, os, statistics as st
import silo

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "research", "calibration.json")
# The Fiscal tab table. The script rewrites the numbers of the 5 market rules; the verdicts
# and the 2 background conditions (r - g, primary gap: share of months) stay by hand.
CALIB = os.path.join(os.path.dirname(__file__), "..", "data", "dominancia", "calib.json")
ORDER = ["be2_50", "be5_50", "r5_gt5", "r5_gt7", "r5_50"]


def run(start=2010):
    pre2, pre5 = silo.curve("PRE", 720, start), silo.curve("PRE", 1800, start)
    dpl2, dpl5 = silo.curve("DPL", 720, start), silo.curve("DPL", 1800, start)
    usd = silo.macro("USDBRL", start)
    days = sorted(set(pre2) & set(pre5) & set(dpl2) & set(dpl5) & set(usd))
    n = len(days)
    be = lambda p, r: ((1 + p / 100) / (1 + r / 100) - 1) * 100
    s = {
        "di2": [pre2[d] for d in days], "usd": [usd[d] for d in days], "r5": [dpl5[d] for d in days],
        "be2": [be(pre2[d], dpl2[d]) for d in days], "be5": [be(pre5[d], dpl5[d]) for d in days],
    }
    cross = [i >= 60 and ((s["di2"][i] - s["di2"][i - 60]) * 100 > 200 or s["usd"][i] / s["usd"][i - 60] - 1 > 0.15) for i in range(n)]
    starts, last = [], -10 ** 9
    for i in range(n):
        if cross[i]:
            if i - last > 60:
                starts.append(i)
            last = i
    ch = lambda k, i, w=20: (s[k][i] - s[k][i - w]) * 100 if i >= w else 0
    rules = {
        "be2_50": ("Inflação implícita 2 anos sobe mais de 50 bp em 4 semanas", lambda i: ch("be2", i) > 50),
        "be5_50": ("Inflação implícita 5 anos sobe mais de 50 bp em 4 semanas", lambda i: ch("be5", i) > 50),
        "r5_gt5": ("Juro real 5 anos acima de 5%", lambda i: s["r5"][i] > 5),
        "r5_gt7": ("Juro real 5 anos acima de 7%", lambda i: s["r5"][i] > 7),
        "r5_50": ("Juro real 5 anos sobe mais de 50 bp em 4 semanas", lambda i: ch("r5", i) > 50),
    }
    near = [False] * n
    for a in starts:
        for i in range(max(0, a - 60), min(n, a + 61)):
            near[i] = True
    calm = [i for i in range(n) if not near[i]]
    out = []
    for key, (label, on) in rules.items():
        leads = []
        for a in starts:
            lit = [i for i in range(max(0, a - 60), a + 1) if on(i)]
            if lit:
                leads.append(a - lit[0])
        out.append({"id": key, "regra": label, "avisou": len(leads), "crises": len(starts),
                    "antecedencia_mediana_sessoes": st.median(leads) if leads else None,
                    "aceso_em_calma_pct": round(100 * sum(on(i) for i in calm) / len(calm), 1)})
    return {
        "origin": "Cálculo sobre Dado (SILO: curvas PRE e DPL da B3, dólar SGS 1)",
        "from": days[0], "to": days[-1], "sessions": n, "calm_sessions": len(calm),
        "crises": [{"start": days[a], "di2_60s_bp": round((s["di2"][a] - s["di2"][a - 60]) * 100), "usd_60s_pct": round((s["usd"][a] / s["usd"][a - 60] - 1) * 100, 1)} for a in starts],
        "rules": out,
    }


if __name__ == "__main__":
    r = run()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    with open(CALIB) as f:
        table = json.load(f)
    by_id = {x["id"]: x for x in r["rules"]}
    for row, key in zip(table, ORDER):
        x = by_id[key]
        row["avisou"] = f'{x["avisou"]} de {x["crises"]}'
        row["antecedencia_mediana"] = x["antecedencia_mediana_sessoes"]
        row["aceso_em_calma_pct"] = x["aceso_em_calma_pct"]
    with open(CALIB, "w") as f:
        json.dump(table, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(len(r["crises"]), "crises:", [c["start"] for c in r["crises"]])
    for x in r["rules"]:
        print(x["id"], f'{x["avisou"]}/{x["crises"]}', x["antecedencia_mediana_sessoes"], x["aceso_em_calma_pct"])
