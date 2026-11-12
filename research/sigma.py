"""σ of the scenario likelihood: how far the 2-year DI wanders after a shock.

Method (as stated on the Método page, 29/10/2026):
  - Series: B3 PRE curve, 720-day vertex, daily, from SILO curve_history, 2015 onward.
  - Shock day: daily change larger than 2 standard deviations of all daily changes.
    Shock days closer than 20 sessions to the previous shock belong to the same episode.
  - For each episode and each horizon h of 20..40 sessions, the move from the close
    before the shock to the close h sessions later.
  - σ(h) = standard deviation of those moves across episodes. The page reports the range.
Writes data/research/sigma.json.
"""
import json, os, statistics as st
import silo

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "research", "sigma.json")


def run(start=2015, gap=20, k=2.0, h_from=20, h_to=40):
    pre = silo.curve("PRE", 720, start)
    days = sorted(pre)
    lv = [pre[d] for d in days]
    ch = [(lv[i] - lv[i - 1]) * 100 for i in range(1, len(lv))]          # bp
    sd = st.pstdev(ch)
    shocks, last = [], -10 ** 9
    for i, c in enumerate(ch, start=1):
        if abs(c) > k * sd and i - last >= gap:
            shocks.append(i)
        if abs(c) > k * sd:
            last = i
    sig = {}
    for h in range(h_from, h_to + 1):
        mv = [(lv[i - 1 + h] - lv[i - 1]) * 100 for i in shocks if i - 1 + h < len(lv)]
        sig[h] = round(st.stdev(mv), 1)
    return {
        "origin": "Cálculo sobre Dado (SILO, curva PRE da B3, vértice de 720 dias)",
        "series": {"curve": "PRE", "tenor_days": 720, "from": days[0], "to": days[-1], "sessions": len(days)},
        "rule": {"shock_sd_multiple": k, "daily_change_sd_bp": round(sd, 2), "episode_gap_sessions": gap, "horizon_sessions": [h_from, h_to]},
        "episodes": [{"date": days[i], "change_bp": round(ch[i - 1], 1)} for i in shocks],
        "sigma_bp_by_horizon": sig,
        "sigma_bp_range": [min(sig.values()), max(sig.values())],
        "sigma_bp_median": st.median(sig.values()),
        "sigma_used_bp": 100,
        "sigma_used_origin": "Julgamento: valor redondo dentro da faixa medida; não reestimado por cenário",
    }


if __name__ == "__main__":
    r = run()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    print(len(r["episodes"]), "episodes;", "σ range", r["sigma_bp_range"], "median", r["sigma_bp_median"])
