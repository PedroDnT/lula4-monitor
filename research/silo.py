"""Read-only client for the public SILO API (schema api). Standard library only.

Every call is one POST to /rest/v1/rpc/<function> with the publishable key that the site
already uses. Windows larger than the 1,000-row ceiling are split by year. Raw answers are
cached in research/cache/ so a rerun is reproducible offline; delete the cache to refresh.
"""
import json, os, hashlib, urllib.request, datetime as dt

URL = "https://zcjbtpxuhdekpwcxmepn.supabase.co/rest/v1/rpc/"
KEY = "sb_publishable__yfFQsykAglrvc9GS6_PYw_B24ex437"
CACHE = os.path.join(os.path.dirname(__file__), "cache")


def rpc(fn, **args):
    os.makedirs(CACHE, exist_ok=True)
    tag = hashlib.sha256((fn + json.dumps(args, sort_keys=True)).encode()).hexdigest()[:16]
    path = os.path.join(CACHE, f"{fn}-{tag}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    req = urllib.request.Request(URL + fn, data=json.dumps(args).encode(), method="POST", headers={
        "apikey": KEY, "Accept-Profile": "api", "Content-Profile": "api", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        rows = json.load(r)
    with open(path, "w") as f:
        json.dump(rows, f)
    return rows


def by_year(fn, start, end, **args):
    """Call fn once per calendar year (p_from/p_to) and concatenate, oldest first."""
    out = []
    for y in range(start, end + 1):
        out += rpc(fn, p_from=f"{y}-01-01", p_to=f"{y}-12-31", **args)
    return out


def curve(name, tenor, start=2010, end=None):
    """{date: rate %} for one SILO curve vertex (B3 reference curves, e.g. PRE or DPL)."""
    end = end or dt.date.today().year
    rows = by_year("curve_history", start, end, p_curve=name, p_tenor_days=tenor)
    return {r["trade_date"]: float(r["rate"]) for r in rows if r.get("rate") is not None}


def macro(series, start, end=None):
    """{date: value} for one SGS series in SILO macro_series."""
    end = end or dt.date.today().year
    rows = by_year("macro_series", start, end, p_series=series)
    return {r["reference_date"]: float(r["value"]) for r in rows if r.get("value") is not None}


def focus_annual(indicator, horizon, start, end=None):
    """[(survey_date, median)] for one Focus annual horizon, oldest first."""
    end = end or dt.date.today().year
    rows = by_year("focus_expectations", start, end, p_endpoint="ExpectativasMercadoAnuais", p_horizon=str(horizon), p_indicator=indicator)
    return sorted({r["survey_date"]: float(r["median"]) for r in rows if r.get("median") is not None}.items())


def dol_front(days, workers=8):
    """{date: % change of the most liquid DOL contract} from B3 settlements (future_curve).

    The most liquid contract is the one with the largest open interest on the day; its change is
    against its own settlement on the previous date in `days`, so rolls never create a jump.
    """
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(workers) as ex:
        curves = dict(zip(days, ex.map(lambda d: rpc("future_curve", p_root="DOL", p_trade_date=d), days)))
    px = {d: {r["ticker"]: (float(r["settlement_price"]), r.get("open_interest") or 0) for r in rows if r.get("settlement_price")}
          for d, rows in curves.items()}
    out = {}
    for a, b in zip(days, days[1:]):
        if not px.get(b) or not px.get(a):
            continue
        t = max(px[b], key=lambda k: px[b][k][1])
        if t in px[a]:
            out[b] = (px[b][t][0] / px[a][t][0] - 1) * 100
    return out
