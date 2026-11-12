"""Daily closes from the public Yahoo Finance chart endpoint. Standard library only.

Raw answers are cached in research/cache/ like silo.py; delete the cache to refresh.
"""
import json, os, hashlib, urllib.request, datetime as dt

CACHE = os.path.join(os.path.dirname(__file__), "cache")
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={a}&period2={b}&interval=1d&events=history"


def closes(sym, start="2008-01-01", end=None):
    """{YYYY-MM-DD: close} for one Yahoo symbol (adjusted close when Yahoo gives it)."""
    end = end or dt.date.today().isoformat()
    a = int(dt.datetime.fromisoformat(start).replace(tzinfo=dt.timezone.utc).timestamp())
    b = int(dt.datetime.fromisoformat(end).replace(tzinfo=dt.timezone.utc).timestamp()) + 86400
    os.makedirs(CACHE, exist_ok=True)
    tag = hashlib.sha256(f"{sym}{start}{end}".encode()).hexdigest()[:16]
    path = os.path.join(CACHE, f"yahoo-{tag}.json")
    if os.path.exists(path):
        raw = json.load(open(path))
    else:
        req = urllib.request.Request(URL.format(sym=sym, a=a, b=b), headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = json.load(r)
        json.dump(raw, open(path, "w"))
    res = raw["chart"]["result"][0]
    tz = res["meta"].get("gmtoffset", 0)
    ts = res.get("timestamp") or []
    q = res["indicators"]
    vals = (q.get("adjclose") or [{}])[0].get("adjclose") or q["quote"][0]["close"]
    out = {}
    for t, v in zip(ts, vals):
        if v is not None:
            out[dt.datetime.fromtimestamp(t + tz, dt.timezone.utc).date().isoformat()] = float(v)
    if not out:
        raise RuntimeError(f"Yahoo sem dados para {sym}")
    return out
