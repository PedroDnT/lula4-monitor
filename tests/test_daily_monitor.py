import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import daily_monitor as m

ROOT = Path(__file__).resolve().parents[1]


def market(run_date, expected):
    return {'origin': 'Dado', 'url': m.SILO, 'date': expected, 'rate_pct': 14.96,
            'baseline_date': m.BASE_DATE, 'baseline_pct': m.BASE_RATE,
            'response_sha256': 'test'}, b'[]'


def fact(key='f14', channel='canal-novo'):
    return {'id': key, 'data': '2026-11-04', 'fato': 'Fato de teste com fonte e aprovação explícita.',
            'fonte': 'Fonte de teste', 'url': 'https://example.org/fato',
            'origin': 'Dado', 'f_ancora': 1.05, 'f_deriva': 1, 'f_estresse': 1,
            'status': 'Na partida', 'degrau': 'Teste fraco', 'channel': channel,
            'evidence_quote': 'Trecho de teste explicitamente presente na fonte consultada.',
            'approval': {'by': 'Pedro', 'reference': 'https://example.org/approval', 'origin': 'Julgamento'}}


class CalculationTests(unittest.TestCase):
    def test_reference(self):
        actual = m.posterior([.49, .31, .20], 232)
        for a, b in zip(actual, [15.43, 43.18, 41.38]):
            self.assertAlmostEqual(a * 100, b, delta=.005)
        self.assertAlmostEqual(sum(actual), 1)

    def test_level_is_not_chained(self):
        start = [.49, .31, .20]
        yesterday = m.posterior(start, 216)
        self.assertNotEqual(m.posterior(start, 232), m.posterior(yesterday, 232))
        self.assertEqual(m.posterior(start, 232), m.posterior(start, 232))

    def test_bad_values(self):
        for value in (None, True, '232', float('nan'), float('inf'), 10001):
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                m.posterior([.49, .31, .20], value)
        for start in ([.49, .31, .21], [-.1, .5, .6], [0, 0, 0]):
            with self.assertRaises(ValueError): m.posterior(start, 232)

    def test_zero_and_extreme(self):
        self.assertEqual(m.posterior([0, 1, 0], 10000), [0, 1, 0])
        self.assertAlmostEqual(sum(m.posterior([.49, .31, .2], -10000)), 1)


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'repo'
        shutil.copytree(ROOT / 'data', self.root / 'data')
        shutil.copytree(ROOT / 'docs/rotina', self.root / 'docs/rotina')
        # Frozen ledger snapshot of 02/11, so real daily batches do not change the fixture.
        shutil.copytree(ROOT / 'tests/fixtures/baseline-2026-11-02', self.root, dirs_exist_ok=True)

    def tearDown(self): self.tmp.cleanup()

    def prepare(self, facts=None, day='2026-11-04'):
        return m.prepare(self.root, day, facts or [], market, lambda f: {'url': f['url']})

    def apply(self, files):
        for p, value in files.items(): m.write(self.root / p, value)

    def mutate(self, path, fn):
        data = m.read(self.root / path)
        fn(data)
        m.write(self.root / path, data)

    def test_baseline_unchanged_and_copies_exact(self):
        files, report, _ = self.prepare()
        self.assertEqual(report['start']['value'], [.49, .31, .2])
        self.assertEqual(report['market']['date'], '2026-11-03')
        self.apply(files)
        m.validate_repo(self.root)
        self.assertEqual(files[m.WEIGHTS][0]['partida_em'], '2026-11-02')
        self.assertEqual(files[m.WEIGHTS][0]['probability'], files[m.SCENARIOS][0]['probability'])

    def test_apply_once_replay_and_next_day(self):
        new = fact()
        files, report, _ = self.prepare([new])
        self.assertAlmostEqual(files[m.WEIGHTS][0]['start'], .49 * 1.05 / (.49 * 1.05 + .31 + .2))
        self.assertEqual(report['changes'][0]['id'], 'f14')
        self.apply(files)
        again, replay, _ = self.prepare([new])
        self.assertEqual(files, again)
        self.assertEqual(report, replay)
        tomorrow, _, _ = self.prepare([new], '2026-11-05')
        self.assertEqual(files[m.WEIGHTS][0]['start'], tomorrow[m.WEIGHTS][0]['start'])

    def test_seeded_facts_not_reapplied(self):
        old = m.read(self.root / m.FACTS)
        self.assertEqual(self.prepare(old)[0][m.STATE]['start'], [.49, .31, .2])

    def test_duplicate_id_and_fingerprint(self):
        for rows in ([fact(), fact()], [fact(), dict(fact(), id='f15')]):
            # An exact ID replay in the same input is harmless; another ID is rejected.
            if rows[0] == rows[1]:
                self.assertEqual(len(self.prepare(rows)[1]['changes']), 1)
            else:
                with self.assertRaises(ValueError): self.prepare(rows)
        changed = dict(m.read(self.root / m.FACTS)[0], fato='alterado')
        with self.assertRaises(ValueError): self.prepare([changed])

    def test_repeated_channel_limit_and_approval(self):
        for change in ({'channel': 'leiloes', 'f_ancora': 1.15}, {'f_ancora': 1.2},
                       {'approval': {'by': 'Agent', 'reference': 'https://example.org', 'origin': 'Julgamento'}},
                       {'origin': 'Inventado'}, {'data': '2026-11-05'}):
            with self.subTest(change=change), self.assertRaises(ValueError): self.prepare([dict(fact(), **change)])

    def test_source_failure_no_mutation(self):
        original = (self.root / m.WEIGHTS).read_bytes()
        with self.assertRaises(OSError):
            m.prepare(self.root, '2026-11-04', [fact()], market, lambda f: (_ for _ in ()).throw(OSError('fonte caiu')))
        self.assertEqual(original, (self.root / m.WEIGHTS).read_bytes())

    def test_market_failure_no_batch(self):
        output = Path(self.tmp.name) / 'output'
        with patch.object(m, 'fetch', side_effect=OSError('SILO caiu')), self.assertRaises(OSError):
            m.stage(self.root, output, '2026-11-04', [])
        self.assertFalse(output.exists())

    def test_conflicting_same_day(self):
        files, _, _ = self.prepare()
        self.apply(files)
        with self.assertRaises(ValueError): self.prepare([fact()])

    def test_tampered_ledger_and_datasets(self):
        for path, fn in ((m.WEIGHTS, lambda d: d[0].update(start=.50)),
                         (m.SCENARIOS, lambda d: d[0].update(probability=.20)),
                         (m.HISTORY, lambda d: d[-1].update(ancora=.2)),
                         (m.FACTS, lambda d: d[0].update(fato='alterado'))):
            old = (self.root / path).read_bytes()
            self.mutate(path, fn)
            with self.subTest(path=path), self.assertRaises(ValueError): self.prepare()
            (self.root / path).write_bytes(old)

    def test_staging_allowlist_and_validation(self):
        output = Path(self.tmp.name) / 'output'
        rows = [{'trade_date': m.BASE_DATE, 'settlement_rate': 12.642, 'ticker': 'DI1F29', 'settlement_status': 'F'},
                {'trade_date': '2026-11-03', 'settlement_rate': 14.96, 'prev_settlement_rate': m.BASE_RATE,
                 'ticker': 'DI1F29', 'settlement_status': 'F'}]
        with patch.object(m, 'fetch', return_value=json.dumps(rows).encode()):
            m.stage(self.root, output, '2026-11-04', [])
        self.assertEqual({str(p.relative_to(output)) for p in (output / 'data').rglob('*.json')},
                         {m.WEIGHTS, m.SCENARIOS, m.FACTS, m.HISTORY})
        self.assertTrue((output / 'manifest.json').exists())
        m.apply_batch(self.root, output)
        m.validate_repo(self.root)
        with self.assertRaises(ValueError): m.apply_batch(self.root, output)
        with self.assertRaises(ValueError): m.stage(self.root, output, '2026-11-04', [])
        with self.assertRaises(ValueError): m.stage(self.root, self.root / 'output', '2026-11-04', [])


    def test_tampered_batch_refused(self):
        output = Path(self.tmp.name) / 'tampered'
        files, _, _ = self.prepare()
        for p, obj in files.items(): m.write(output / p, obj)
        m.write(output / 'manifest.json', {'inputs': {p: m.digest(m.read(self.root / p)) for p in files},
                                         'outputs': {p: m.digest(v) for p, v in files.items()}})
        m.write(output / m.WEIGHTS, [])
        before = (self.root / m.WEIGHTS).read_bytes()
        with self.assertRaises(ValueError): m.apply_batch(self.root, output)
        self.assertEqual(before, (self.root / m.WEIGHTS).read_bytes())

    def test_apply_rolls_back_on_post_write_failure(self):
        output = Path(self.tmp.name) / 'rollback'
        files, _, _ = self.prepare()
        for p, obj in files.items(): m.write(output / p, obj)
        m.write(output / 'manifest.json', {'inputs': {p: m.digest(m.read(self.root / p)) for p in files},
                                         'outputs': {p: m.digest(v) for p, v in files.items()}})
        before = {p: (self.root / p).read_bytes() for p in files}
        real_validate = m.validate_repo
        def validate(path):
            if path == self.root: raise OSError('simulated disk failure')
            return real_validate(path)
        with patch.object(m, 'validate_repo', validate), self.assertRaises(OSError):
            m.apply_batch(self.root, output)
        self.assertEqual(before, {p: (self.root / p).read_bytes() for p in files})


class SourceTests(unittest.TestCase):
    def test_calendar(self):
        self.assertEqual(m.previous_session('2026-11-03', {'2026-11-02'}), '2026-10-30')
        self.assertEqual(m.previous_session('2026-11-09', set()), '2026-11-06')
        with self.assertRaises(ValueError): m.previous_session('2028-01-03', set())

    def test_market_validation(self):
        good = [{'trade_date': m.BASE_DATE, 'settlement_rate': 12.642, 'ticker': 'DI1F29', 'settlement_status': 'F'},
                {'trade_date': '2026-11-03', 'settlement_rate': 14.96, 'prev_settlement_rate': m.BASE_RATE,
                 'ticker': 'DI1F29', 'settlement_status': 'F'}]
        bad = [[], {}, good[:1], good + [good[-1]],
               [good[0], dict(good[1], prev_settlement_rate=12.642)],
               [good[0], {k: v for k, v in good[1].items() if k != 'prev_settlement_rate'}],
               [good[0], dict(good[1], settlement_rate=None)],
               [good[0], dict(good[1], settlement_rate='14.96')],
               [good[0], dict(good[1], settlement_rate=1496)],
               [good[0], dict(good[1], settlement_status='P')],
               [good[0], dict(good[1], ticker='DI1F30')]]
        for rows in bad:
            with self.subTest(rows=rows), patch.object(m, 'fetch', return_value=json.dumps(rows).encode()), self.assertRaises(ValueError):
                m.collect_market('2026-11-04', '2026-11-03')
        with patch.object(m, 'fetch', return_value=json.dumps(good).encode()):
            result, _ = m.collect_market('2026-11-04', '2026-11-03')
            self.assertEqual(result['rate_pct'], 14.96)

    def test_evidence_and_http_error(self):
        f = fact()
        with patch.object(m, 'fetch', return_value=b'paywall'), self.assertRaises(ValueError): m.verify_source(f)
        with patch.object(m, 'fetch', return_value=f['evidence_quote'].encode()):
            self.assertEqual(m.verify_source(f)['origin'], 'Dado')
        with patch.object(m, 'urlopen', side_effect=OSError('HTTP 503')), self.assertRaises(OSError): m.fetch(m.SILO, {})


if __name__ == '__main__': unittest.main()
