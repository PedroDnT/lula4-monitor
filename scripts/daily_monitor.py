#!/usr/bin/env python3
"""Prepare a validated daily batch. No git writes, publishing or scheduling."""
import argparse
import copy
from datetime import date, datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

IDS = ('ancora', 'deriva', 'estresse')
# Marks: research/termpremium.py (scenario Selic path + measured 2-year premium), approved 12/11/2026.
MARKS = (28, 123, 295)
BASE_DATE = '2026-10-23'
BASE_RATE = 12.640
SIGMA = 100
SILO = 'https://zcjbtpxuhdekpwcxmepn.supabase.co/rest/v1/rpc/future_series'
KEY = 'sb_publishable__yfFQsykAglrvc9GS6_PYw_B24ex437'
TZ = ZoneInfo('America/Sao_Paulo')
WEIGHTS = 'data/relatorio/pesos.json'
SCENARIOS = 'data/dominancia/scenarios.json'
FACTS = 'data/relatorio/fatos.json'
HISTORY = 'data/dominancia/scenario_history.json'
STATE = 'docs/rotina/state.json'
SIGMA_FILE = 'data/research/sigma.json'
ALLOWED = {0.77, 0.87, 0.95, 1.0, 1.05, 1.15, 1.30}
ORIGINS = {'Norma', 'Dado', 'Cálculo', 'Regressão', 'Literatura', 'Julgamento', 'Projeção'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def number(x):
    require(type(x) in (int, float) and math.isfinite(x), 'Número ausente, inválido ou não finito')
    return x


def iso(s):
    require(isinstance(s, str) and date.fromisoformat(s).isoformat() == s, 'Data inválida')
    return s


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def normalize(values):
    values = [number(x) for x in values]
    require(len(values) == 3 and all(x >= 0 for x in values) and sum(values) > 0, 'Pesos inválidos')
    return [x / sum(values) for x in values]


def posterior(start, move):
    """Always start × likelihood of the cumulative move; stable log normalization."""
    number(move)
    require(abs(move) <= 10000, 'DI fora do intervalo operacional; revisão necessária')
    require(abs(sum(start) - 1) < 1e-9, 'Partida não soma 1')
    normalize(start)
    logs = [math.log(p) - ((move - m) / SIGMA) ** 2 / 2 if p else -math.inf
            for p, m in zip(start, MARKS)]
    peak = max(logs)
    return normalize([math.exp(x - peak) for x in logs])


def fingerprint(fact):
    return digest({'url': fact['url'].rstrip('/'), 'fato': ' '.join(fact['fato'].casefold().split())})


def ordered(rows):
    require(isinstance(rows, list) and len(rows) == 3 and {r['id'] for r in rows} == set(IDS), 'Cenários inválidos')
    return [next(r for r in rows if r['id'] == key) for key in IDS]


def validate_repo(root):
    # Every JSON must parse, including files outside this routine's write scope.
    def finite(obj):
        if isinstance(obj, dict):
            for v in obj.values(): finite(v)
        elif isinstance(obj, list):
            for v in obj: finite(v)
        elif isinstance(obj, float): number(obj)
    for path in (root / 'data').rglob('*.json'):
        finite(read(path))
    weights, scenarios = ordered(read(root / WEIGHTS)), ordered(read(root / SCENARIOS))
    for rows in (weights, scenarios):
        for field in ('start', 'probability'):
            values = [number(r[field]) for r in rows]
            require(all(0 <= x <= 1 for x in values) and abs(sum(values) - 1) < 1e-9, field + ' inválido')
        require(tuple(r['di_jan29_move_bp'] for r in rows) == MARKS, 'Marcas alteradas')
    for a, b in zip(weights, scenarios):
        require(all(a[k] == b[k] for k in ('id', 'start', 'probability', 'di_jan29_move_bp')), 'Datasets de pesos divergentes')
    require(len({r['partida_em'] for r in weights}) == len({r['agora_em'] for r in weights}) == 1, 'Datas dos pesos divergentes')
    for r in weights:
        iso(r['partida_em']); iso(r['agora_em'])
        require(r['partida_em'] <= r['agora_em'], 'Partida posterior ao agora')
    # One sigma for the batch and the pages: they read data/research/sigma.json, this script uses SIGMA.
    require(read(root / SIGMA_FILE).get('sigma_used_bp') == SIGMA, 'Sigma divergente de ' + SIGMA_FILE)
    facts = read(root / FACTS)
    require(len({f['id'] for f in facts}) == len(facts), 'Fatos duplicados')
    for f in facts:
        iso(f['data'])
        require(f['url'].startswith('https://') and f['fonte'] and f['fato'], 'Fato sem fonte')
        for key in IDS: require(number(f['f_' + key]) in ALLOWED, 'Fator fora da escala publicada')
    history = read(root / HISTORY)
    require(len({(r['date'], r['label']) for r in history}) == len(history), 'Histórico duplicado')
    for r in history:
        iso(r['date'])
        v = [number(r[k]) for k in IDS]
        require(all(0 <= x <= 1 for x in v) and abs(sum(v) - 1) < 1e-9, 'Histórico inválido')
    last = next(r for r in reversed(history) if r['label'].startswith('Partida'))
    require(all(last[k] == r['start'] for k, r in zip(IDS, weights)), 'Histórico e partida divergentes')
    require(last['date'] == weights[0]['partida_em'], 'Data histórica da partida divergente')
    if (root / STATE).exists():
        state = read(root / STATE)
        require(state['start'] == [r['start'] for r in weights], 'Ledger e partida divergentes')
        for key, value in (('facts', facts), ('weights', weights), ('history', history)):
            require(state[key + '_sha256'] == digest(value), 'Ledger divergente: ' + key)
        runs = state.get('runs', {})
        if runs:
            audit = runs[state['as_of']]
            move = (number(audit['market']['rate_pct']) - BASE_RATE) * 100
            require(audit['start'] == state['start'], 'Partida do audit divergente')
            expected_now = posterior(state['start'], move)
            require(all(abs(r['probability'] - p) < 1e-12 for r, p in zip(weights, expected_now)), 'Cálculo do agora divergente')
    return weights, scenarios, facts, history


def previous_session(run_date, holidays):
    # Calendar supplied by the repo; do not extrapolate its coverage silently.
    require('2026-11-03' <= run_date <= '2027-12-31', 'Calendário requer revisão fora da cobertura operacional')
    d = date.fromisoformat(run_date) - timedelta(days=1)
    while d.weekday() >= 5 or d.isoformat() in holidays:
        d -= timedelta(days=1)
    return d.isoformat()


def fetch(url, body=None):
    headers = {'User-Agent': 'lula4-monitor/1.0'}
    if body is not None:
        headers.update({'apikey': KEY, 'Accept-Profile': 'api', 'Content-Profile': 'api', 'Content-Type': 'application/json'})
    request = Request(url, data=json.dumps(body).encode() if body is not None else None, headers=headers)
    with urlopen(request, timeout=30) as response:
        require(response.status == 200, 'Fonte sem resposta 200')
        raw = response.read(8_000_001)
        require(len(raw) <= 8_000_000 and raw, 'Fonte vazia ou resposta excessiva')
        return raw


def collect_market(run_date, expected):
    args = {'p_ticker': 'DI1F29', 'p_from': BASE_DATE}
    raw = fetch(SILO, args)
    rows = json.loads(raw)
    require(isinstance(rows, list) and rows, 'SILO sem série')
    by_date = {}
    for r in rows:
        d = iso(r['trade_date'])
        require(d not in by_date, 'SILO com data duplicada')
        value = number(r['settlement_rate'])
        require(0 < value < 100, 'Taxa SILO fora da unidade percentual')
        by_date[d] = value
    selected = [r for r in rows if r['trade_date'] in (BASE_DATE, expected)]
    require(all(r.get('ticker') == 'DI1F29' and r.get('settlement_status') == 'F' for r in selected), 'Contrato errado ou ajuste não final')
    # The base is B3's own figure: the session after 23/10 prints it as prev_settlement_rate
    # (12.640 on 26/10), while the 23/10 row prints 12.642. Decision of Pedro, 08/11/2026.
    require(BASE_DATE in by_date, 'SILO sem a sessão base')
    base_next = min((d for d in by_date if d > BASE_DATE), default=None)
    require(base_next is not None, 'SILO sem a sessão seguinte à base')
    base_row = next(r for r in rows if r['trade_date'] == base_next)
    require(abs(number(base_row.get('prev_settlement_rate')) - BASE_RATE) < 1e-9, 'Base de 23/10 divergente')
    eligible = [d for d in by_date if d < run_date]
    require(eligible and max(eligible) == expected, 'SILO atrasado ou calendário divergente')
    return {'origin': 'Dado', 'url': SILO, 'args': args, 'date': expected,
            'rate_pct': by_date[expected], 'baseline_date': BASE_DATE, 'baseline_pct': BASE_RATE,
            'baseline_source': 'prev_settlement_rate de ' + base_next + ' (B3 Price Report via SILO)',
            'response_sha256': hashlib.sha256(raw).hexdigest()}, raw


def verify_source(fact):
    require(fact['url'].startswith('https://'), 'Fonte deve usar HTTPS')
    raw = fetch(fact['url'])
    # An HTTP 200 alone does not establish evidence (paywall, bot page, etc.).
    quote = fact['evidence_quote']
    require(isinstance(quote, str) and len(quote.strip()) >= 40, 'Trecho verificável insuficiente')
    require(quote in raw.decode('utf-8'), 'Trecho não encontrado na resposta da fonte')
    return {'url': fact['url'], 'origin': 'Dado', 'quote': quote,
            'response_sha256': hashlib.sha256(raw).hexdigest()}


def prepare(root, run_date, incoming, market_reader=collect_market, source_reader=verify_source):
    weights, scenarios, facts, history = copy.deepcopy(validate_repo(root))
    state = copy.deepcopy(read(root / STATE))
    require(state['start'] == [r['start'] for r in weights], 'Ledger e partida divergentes')
    require(state['facts_sha256'] == digest(facts), 'Fatos alterados fora do ledger')
    require(state['weights_sha256'] == digest(weights), 'Pesos alterados fora do ledger')
    require(state['history_sha256'] == digest(history), 'Histórico alterado fora do ledger')
    require(state['as_of'] <= run_date, 'Execução anterior ao ledger')
    known = {f['id']: f for f in facts}
    require(set(state['applied_ids']) == {f['id'] for f in facts if f['status'] == 'Na partida'}, 'Ledger de aplicações divergente')
    holidays = {r['data'] for r in read(root / 'data/relatorio/feriados.json')}
    expected = previous_session(run_date, holidays)
    market, raw = market_reader(run_date, expected)
    require(market['date'] == expected and market['origin'] == 'Dado' and market['url'] == SILO, 'Fonte de DI inválida')
    require(market['baseline_date'] == BASE_DATE and market['baseline_pct'] == BASE_RATE, 'Base inválida')
    number(market['rate_pct'])
    require(isinstance(incoming, list), 'Entrada de fatos deve ser uma lista')
    start = state['start'][:]
    applied, evidence, changes = [], [], []
    seen = {fingerprint(f) for f in facts}
    channels = set(state['channels'])
    for fact in incoming:
        if fact['id'] in known:
            require(fact == known[fact['id']], 'ID já existente com conteúdo diferente')
            continue
        require(fingerprint(fact) not in seen, 'Fato repetido com outro ID')
        require(fact['status'] == 'Na partida' and fact['origin'] in ORIGINS, 'Fato sem origem ou situação válida')
        require(iso(fact['data']) <= run_date and fact['fonte'] and fact['degrau'], 'Fato inválido')
        approval = fact['approval']
        require(approval['by'] == 'Pedro' and approval['reference'].startswith('https://') and approval['origin'] == 'Julgamento', 'Fatores sem aprovação rastreável de Pedro')
        channel = fact['channel']
        require(isinstance(channel, str) and channel.strip(), 'Canal ausente')
        factors = [number(fact['f_' + k]) for k in IDS]
        require(all(f in ALLOWED for f in factors), 'Fator fora da escala publicada')
        if channel in channels:
            require(all(0.95 <= f <= 1.05 for f in factors), 'Canal repetido admite no máximo fraco')
        evidence.append(source_reader(fact))
        before = start[:]
        start = normalize([p * f for p, f in zip(start, factors)])
        changes.append({'id': fact['id'], 'before': before, 'factors': factors, 'after': start[:],
                        'factor_origin': 'Julgamento', 'weight_origin': 'Cálculo', 'approval': approval})
        applied.append(fact['id']); facts.append(fact); known[fact['id']] = fact
        seen.add(fingerprint(fact)); channels.add(channel)
    require(not applied or run_date > state['as_of'], 'Novo fato em lote já fechado; revisão necessária')
    move = (market['rate_pct'] - BASE_RATE) * 100
    now = posterior(start, move)
    for i, row in enumerate(weights):
        row.update(start=start[i], probability=now[i], agora_em=run_date)
        if applied: row['partida_em'] = run_date
    for i, row in enumerate(scenarios):
        row.update(start=start[i], probability=now[i])
    def add_history(label, values, note):
        entry = dict(date=run_date, label=label, note=note, **dict(zip(IDS, values)))
        existing = next((r for r in history if (r['date'], r['label']) == (run_date, label)), None)
        require(existing is None or existing == entry, 'Execução conflitante na mesma data')
        if existing is None: history.append(entry)
    if applied:
        add_history('Partida ' + run_date, start, 'Cálculo: fatores aprovados dos fatos ' + ', '.join(applied) + '; ver ledger.')
    add_history('Agora ' + run_date, now, 'Cálculo: partida × verossimilhança normal; DI1F29 SILO de ' + expected + '; ver ledger.')
    state.update(as_of=run_date, start=start, channels=sorted(channels),
                 applied_ids=state['applied_ids'] + applied, facts_sha256=digest(facts),
                 weights_sha256=digest(weights), history_sha256=digest(history))
    report = {'run_date_brt': run_date, 'prepared_at_brt': datetime.now(TZ).isoformat(), 'market': market, 'move_bp': {'origin': 'Cálculo', 'value': move},
              'start': {'origin': 'Julgamento' if not applied else 'Cálculo', 'value': start},
              'now': {'origin': 'Cálculo', 'value': now}, 'changes': changes, 'sources': evidence,
              'method': {'marks_bp': {'origin': 'Cálculo', 'value': list(MARKS), 'source': 'data/research/term_premium.json (research/termpremium.py): caminho da Selic por cenário (Julgamento) + prêmio medido (Cálculo)'},
                         'sigma_bp': {'origin': 'Julgamento', 'value': SIGMA, 'source': 'data/research/sigma.json (research/sigma.py): faixa medida de 78 a 123 bp, mediana 101'},
                         'formula': 'normalize(start * exp(-(move_bp - marks_bp)^2 / (2 * sigma_bp^2)))'},
              # Open items come from the ledger, so a warning disappears once its item is resolved there.
              'warnings': list(state.get('unresolved', []))}
    audit = {'market': market, 'changes': changes, 'start': start, 'now': now}
    runs = state.setdefault('runs', {})
    if run_date in runs:
        previous = runs[run_date]
        require(all(previous[k] == audit[k] for k in ('market', 'start', 'now')), 'Lote diário mudou; revisão necessária')
        report = previous['report']
    else:
        audit['report'] = copy.deepcopy(report)
        runs[run_date] = audit
    return {WEIGHTS: weights, SCENARIOS: scenarios, FACTS: facts, HISTORY: history, STATE: state}, report, raw


def stage(root, output, run_date, incoming):
    require(not output.exists(), 'Destino já existe; nenhum arquivo sobrescrito')
    require(not output.is_relative_to(root), 'Destino deve ficar fora do checkout')
    files, report, raw = prepare(root, run_date, incoming)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        batch = Path(tmp) / 'batch'
        shutil.copytree(root / 'data', batch / 'data')
        for path, obj in files.items(): write(batch / path, obj)
        validate_repo(batch)
        write(batch / 'report.json', report)
        (batch / 'silo-response.json').write_bytes(raw)
        write(batch / 'manifest.json', {'inputs': {p: digest(read(root / p)) for p in files},
                                      'outputs': {p: digest(v) for p, v in files.items()}})
        # The full data copy is only for validation; deliver only the write allowlist.
        for path in (batch / 'data').rglob('*.json'):
            if str(path.relative_to(batch)) not in files: path.unlink()
        batch.rename(output)


def apply_batch(root, batch):
    """Apply only a reviewed batch whose inputs still match this checkout."""
    allowed = {WEIGHTS, SCENARIOS, FACTS, HISTORY, STATE}
    manifest = read(batch / 'manifest.json')
    require(set(manifest['inputs']) == set(manifest['outputs']) == allowed, 'Manifest fora do escopo')
    originals = {p: (root / p).read_bytes() for p in allowed}
    for p in allowed:
        require(digest(read(root / p)) == manifest['inputs'][p], 'Checkout mudou desde a preparação: ' + p)
        require(digest(read(batch / p)) == manifest['outputs'][p], 'Lote alterado: ' + p)
    with tempfile.TemporaryDirectory() as tmp:
        candidate = Path(tmp)
        shutil.copytree(root / 'data', candidate / 'data')
        for p in allowed: write(candidate / p, read(batch / p))
        validate_repo(candidate)
    try:
        for p in sorted(allowed):
            target = root / p
            temp = target.with_suffix('.json.daily-tmp')
            try:
                with temp.open('xb') as stream: stream.write((batch / p).read_bytes())
                temp.replace(target)
            finally:
                if temp.exists(): temp.unlink()
        validate_repo(root)
    except BaseException:
        for p, raw in originals.items(): (root / p).write_bytes(raw)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'prepare', 'apply'])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--date', default=datetime.now(TZ).date().isoformat())
    parser.add_argument('--facts', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--batch', type=Path)
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        if args.command == 'validate':
            validate_repo(root)
            print('Datasets válidos; pendência histórica de 30/10 preservada.')
        elif args.command == 'apply':
            require(args.batch is not None, '--batch é obrigatório')
            apply_batch(root, args.batch.resolve())
            print('Lote aplicado localmente; nenhum commit ou push executado.')
        else:
            require(args.facts is not None and args.output is not None, '--facts e --output são obrigatórios')
            stage(root, args.output.resolve(), iso(args.date), read(args.facts))
            print('Lote validado: ' + str(args.output))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({'status': 'failed', 'date_brt': args.date, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
