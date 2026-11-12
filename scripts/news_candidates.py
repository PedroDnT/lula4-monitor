"""Candidate news for the daily review. Standard library only.

Searches the last 36 hours with Exa (EXA_API_KEY); if Exa has no key or fails, it uses
Firecrawl (FIRECRAWL_API_KEY). It prints a Markdown list for the PR body. Nothing here
changes a fact or a weight: each item is a candidate that Pedro accepts or ignores, and an
accepted fact goes in by hand with its quote (docs/rotina/README.md).
A failed search prints a notice and exits 0, so the price batch still opens its PR.
"""
import json, os, sys, urllib.request
from datetime import datetime, timedelta, timezone

# One query per channel the facts already use. PLP 299/2026 is the fiscal plan of 11/11.
QUERIES = [
    ("Plano fiscal", "PLP 299/2026 votação Câmara Senado corte de gastos"),
    ("Equipe econômica", "ministro da Fazenda Haddad equipe econômica anúncio"),
    ("Orçamento 2027", "Orçamento 2027 PLOA meta primária relator"),
    ("Copom", "Copom Banco Central Selic decisão comunicado diretor"),
    ("Rating", "agência de rating Brasil nota soberana perspectiva"),
    ("Arcabouço", "arcabouço fiscal mudança meta 2027 Congresso"),
]
HOURS = 36
PER_QUERY = 4


def post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def exa(query, since):
    key = os.environ.get("EXA_API_KEY")
    if not key:
        raise RuntimeError("sem EXA_API_KEY")
    out = post("https://api.exa.ai/search", {
        "query": query, "numResults": PER_QUERY, "type": "auto", "category": "news",
        "startPublishedDate": since.isoformat().replace("+00:00", "Z"),
        "contents": {"highlights": True},
    }, {"x-api-key": key})
    return [{"title": r.get("title") or r["url"], "url": r["url"], "date": (r.get("publishedDate") or "")[:10],
             "text": " ".join(r.get("highlights") or [])} for r in out.get("results", [])]


def firecrawl(query, since):
    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        raise RuntimeError("sem FIRECRAWL_API_KEY")
    out = post("https://api.firecrawl.dev/v2/search", {"query": query, "limit": PER_QUERY, "tbs": "sbd:1,qdr:d",
                                                        "sources": ["web"]},
               {"Authorization": "Bearer " + key})
    data = out.get("data") or {}
    # tbs filters only the web source (Firecrawl docs), so the fallback searches the web.
    rows = data.get("web") or [] if isinstance(data, dict) else data
    return [{"title": r.get("title") or r.get("url"), "url": r.get("url"), "date": (r.get("date") or "")[:10],
             "text": r.get("snippet") or r.get("description") or ""} for r in rows if r.get("url")]


def main():
    since = datetime.now(timezone.utc) - timedelta(hours=HOURS)
    lines, engine_used, errors, seen = [], set(), [], set()
    for channel, query in QUERIES:
        items = None
        for name, fn in (("Exa", exa), ("Firecrawl", firecrawl)):
            try:
                items = fn(query, since)
                engine_used.add(name)
                break
            except Exception as e:  # report and try the next engine; never invent results
                errors.append(f"{name} ({channel}): {e}")
        if items is None:
            continue
        items = [i for i in items if i["url"] not in seen]
        seen.update(i["url"] for i in items)
        if not items:
            continue
        lines.append(f"\n**{channel}**")
        for i in items:
            text = " ".join(i["text"].split())[:220]
            lines.append(f"- [{i['title']}]({i['url']}) {i['date']}" + (f": {text}" if text else ""))
    print("### Notícias candidatas (não aplicadas)\n")
    print("Busca automática das últimas 36 horas. Nenhum item muda fato ou peso: um fato só entra "
          "com a aprovação de Pedro, com o trecho da fonte.")
    if lines:
        print("Busca: " + " e ".join(sorted(engine_used)) + ".")
        print("\n".join(lines))
    else:
        print("\nNenhuma notícia coletada.")
    if errors:
        print("\nFalhas de busca: " + "; ".join(sorted(set(errors)))[:800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
