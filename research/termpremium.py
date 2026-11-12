"""Term premium in the 2-year DI and the DI1F29 marks of the three scenarios.

Expected path (Cálculo): on each day t the expected Selic is a line through the knots
(t, Selic meta on t) and (31 Dec of each year, latest Focus annual median for that year at or
before t). Expected CDI = Selic - 0.10. The expected 2-year rate is the compounded average
of the daily expected CDI over 720 calendar days.
Premium (Cálculo) = PRE 720 (B3 curve via SILO) - expected 2-year rate.
Calm and stress (Cálculo): stress = the 60 sessions from each crisis start of
data/research/calibration.json; calm = farther than 60 sessions from any crisis window.
Scenario paths (Julgamento): Selic after each Copom meeting to Jan/29, written below.
Mark (Cálculo) = path average to 2029-01-02 + premium (calm median for Âncora and Deriva,
stress median for Estresse) - DI1F29 base on 23/10.
Limits: Focus data in SILO starts in 2019, so the sample is 2019 onward. Focus annual
medians are year-end levels, so the line between knots ignores the meeting calendar.
Writes data/research/term_premium.json.
"""
import json, os, bisect, datetime as dt, statistics as st
import silo

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "data", "research", "term_premium.json")
CAL = os.path.join(HERE, "..", "data", "research", "calibration.json")
D = dt.date.fromisoformat
BASE_DATE, BASE_RATE = "2026-10-23", 12.640   # DI1F29 settlement on 23/10 (the scenario base)
END = D("2029-01-02")                          # DI1F29 maturity

# Selic meta after each Copom meeting (date the new rate is in force). Julgamento.
# Âncora: cuts resume in 2027 with fiscal support. Deriva: stop, then slow cuts.
# Estresse: hikes in early 2027, held high. End-2027 levels match scenarios.json (12/13/14).
MEETINGS = ["2026-12-10", "2027-01-28", "2027-03-18", "2027-04-29", "2027-06-17", "2027-08-05",
            "2027-09-23", "2027-10-28", "2027-12-09", "2028-06-15", "2028-12-07"]
PATHS = {
    "ancora":   [13.75, 13.50, 13.25, 13.00, 12.75, 12.50, 12.25, 12.00, 12.00, 11.50, 11.00],
    "deriva":   [13.75, 13.75, 13.75, 13.75, 13.75, 13.50, 13.25, 13.00, 13.00, 13.00, 12.75],
    "estresse": [14.25, 14.75, 15.25, 15.25, 15.00, 14.75, 14.50, 14.25, 14.00, 14.00, 14.00],
}


def avg_rate(points, start, days):
    """Compounded annual average of a step or line path given as daily rates (% a.a.)."""
    acc = 1.0
    for k in range(days):
        acc *= (1 + points(start + dt.timedelta(k)) / 100) ** (1 / 365)
    return (acc ** (365 / days) - 1) * 100


def line(knots):
    xs = [k[0].toordinal() for k in knots]
    ys = [k[1] for k in knots]
    def f(d):
        x = d.toordinal()
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        j = bisect.bisect_right(xs, x)
        return ys[j - 1] + (ys[j] - ys[j - 1]) * (x - xs[j - 1]) / (xs[j] - xs[j - 1])
    return f


def step(dates, rates, before):
    ds = [D(x) for x in dates]
    def f(d):
        j = bisect.bisect_right(ds, d)
        return before if j == 0 else rates[j - 1]
    return f


def focus_table(first, last):
    """{horizon year: [(survey_date, median)]}, surveys from horizon-2 to horizon."""
    out = {}
    for h in range(first, last + 1):
        rows = []
        for y in range(max(2019, h - 2), min(h, dt.date.today().year) + 1):
            rows += silo.rpc("focus_expectations", p_endpoint="ExpectativasMercadoAnuais", p_horizon=str(h),
                             p_indicator="Selic", p_from=f"{y}-01-01", p_to=f"{y}-12-31")
        out[h] = sorted({r["survey_date"]: float(r["median"]) for r in rows if r.get("median") is not None}.items())
    return out


def latest(series, day):
    j = bisect.bisect_right([s[0] for s in series], day)
    return series[j - 1][1] if j else None


def run():
    year = dt.date.today().year
    pre2 = silo.curve("PRE", 720, 2019)
    selic = silo.macro("SELIC_META", 2019)
    sel_days = sorted(selic)
    foc = focus_table(2019, year + 2)
    days = [d for d in sorted(pre2) if d >= "2019-01-01"]
    prem = {}
    for d in days:
        t = D(d)
        s_now = selic[sel_days[bisect.bisect_right(sel_days, d) - 1]]
        knots = [(t, s_now)]
        for h in (t.year, t.year + 1, t.year + 2):
            v = latest(foc.get(h, []), d)
            if v is None:
                break
            knots.append((dt.date(h, 12, 31), v))
        if len(knots) < 3:
            continue
        exp2 = avg_rate(lambda x: line(knots)(x) - 0.10, t, 720)
        prem[d] = round((pre2[d] - exp2) * 100, 1)
    pdays = sorted(prem)
    cal = json.load(open(CAL))
    starts = [c["start"] for c in cal["crises"]]
    idx = {d: i for i, d in enumerate(pdays)}
    stress, near = set(), set()
    for a in starts:
        if a not in idx and not any(x >= a for x in pdays):
            continue
        i = idx.get(a, bisect.bisect_left(pdays, a))
        stress |= set(range(i, min(len(pdays), i + 61)))
        near |= set(range(max(0, i - 60), min(len(pdays), i + 61)))
    calm_v = [prem[pdays[i]] for i in range(len(pdays)) if i not in near]
    str_v = [prem[pdays[i]] for i in stress]
    calm_med, str_med = st.median(calm_v), st.median(str_v)

    # Today's DI1F29 premium against the Focus path to maturity.
    di = silo.rpc("future_series", p_ticker="DI1F29")
    di = sorted((r["trade_date"], float(r["settlement_rate"] if "settlement_rate" in r else r["rate"])) for r in di)
    last_d, last_r = di[-1]
    t = D(last_d)
    s_now = selic[sel_days[-1]]
    knots = [(t, s_now)] + [(dt.date(h, 12, 31), latest(foc[h], last_d)) for h in (t.year, t.year + 1, t.year + 2) if foc.get(h)]
    n = (END - t).days
    focus_avg = avg_rate(lambda x: line(knots)(x) - 0.10, t, n)
    marks = {}
    for k, path in PATHS.items():
        avg = avg_rate(lambda x: step(MEETINGS, path, s_now)(x) - 0.10, t, n)
        p = str_med if k == "estresse" else calm_med
        marks[k] = {"path_avg_pct": round(avg, 3), "premium_bp": p,
                    "mark_rate_pct": round(avg + p / 100, 3),
                    "mark_move_bp": round((avg + p / 100 - BASE_RATE) * 100)}
    out = {
        "method": __doc__.strip(),
        "sample": {"from": pdays[0], "to": pdays[-1], "n": len(pdays)},
        "premium_2y_bp": {"calm_median": calm_med, "calm_n": len(calm_v), "stress_median": str_med,
                          "stress_n": len(str_v), "last": {"date": pdays[-1], "value": prem[pdays[-1]]},
                          "p10_p90_calm": [round(st.quantiles(calm_v, n=10)[0], 1), round(st.quantiles(calm_v, n=10)[-1], 1)]},
        "series_2y_bp": [[d, prem[d]] for d in pdays[::5]],
        "di1f29_now": {"date": last_d, "rate_pct": last_r, "selic_meta": s_now,
                       "focus": {str(h): latest(foc[h], last_d) for h in (t.year, t.year + 1, t.year + 2) if foc.get(h)},
                       "focus_path_avg_pct": round(focus_avg, 3),
                       "premium_bp": round((last_r - focus_avg) * 100, 1)},
        "base": {"date": BASE_DATE, "rate_pct": BASE_RATE},
        "meetings": MEETINGS, "paths": PATHS, "marks": marks,
        "origin": {"premium": "Cálculo", "paths": "Julgamento", "marks": "Cálculo"},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    o = run()
    print(json.dumps({k: o[k] for k in ("sample", "premium_2y_bp", "di1f29_now", "marks")}, indent=1, ensure_ascii=False))
