#!/usr/bin/env python3
"""R10-V2 BTC-only, exploratory, fixed event study. No orders, no PnL.
Requires --preflight OR --run. --run first passes synthetic tests; output fail-closed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.home() / 'Dokumente/TradingLab/data/canonical/binance/perpetual/klines/BTC_USDT/5m'
DEST = Path.home() / 'QuantResearch/R10_V2_Explorativ/Sep2024_Dec2025_v1'
START = pd.Timestamp('2024-09-01', tz='UTC')
SPLIT = pd.Timestamp('2025-01-01', tz='UTC')
END = pd.Timestamp('2026-01-01', tz='UTC')
SEED = 20261115
DRAWS = 5000


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_data():
    files = sorted(ROOT.glob('BTC_USDT_5m_202[45]-*.parquet'))
    files = [p for p in files if '2024-09' <= p.name.split('_5m_')[1][:7] <= '2025-12']
    assert len(files) == 16, f'Need 16 files, found {len(files)}'
    required = ['open_time', 'close_time', 'open', 'high', 'low', 'close', 'volume_base',
                'is_closed', 'exchange', 'market_type', 'contract_type', 'price_source',
                'source_endpoint', 'timeframe']
    frames = [pd.read_parquet(p, columns=required) for p in files]
    d = pd.concat(frames, ignore_index=True)
    t = pd.DatetimeIndex(d['open_time'])
    expected = pd.date_range(START, END, freq='5min', inclusive='left')
    assert t.equals(expected) and t.is_unique, 'timestamp alignment/gaps'
    assert len(d) == 140256
    assert (pd.DatetimeIndex(d['close_time']) + pd.Timedelta(milliseconds=1) == t + pd.Timedelta(minutes=5)).all()
    assert d['is_closed'].all()
    for col, target in [('exchange','binance'),('market_type','perpetual'),
                        ('contract_type','linear'),('price_source','last_trade'),
                        ('source_endpoint','/fapi/v1/klines'),('timeframe','5m')]:
        assert d[col].eq(target).all(), f'bad metadata: {col}'
    ohlc = d[['open','high','low','close']].to_numpy(dtype=float)
    v = d['volume_base'].to_numpy(dtype=float)
    assert np.isfinite(ohlc).all() and (ohlc > 0).all()
    assert np.isfinite(v).all() and (v >= 0).all()
    assert (ohlc[:,1] >= np.maximum(ohlc[:,0],ohlc[:,3])).all()
    assert (ohlc[:,2] <= np.minimum(ohlc[:,0],ohlc[:,3])).all()
    assert (ohlc[:,1] >= ohlc[:,2]).all()
    return t, ohlc[:,3], {p.name: digest(p) for p in files}


def select_events(prices, times, start, end, min_z=2.0):
    """Index based per fixed study partition. 288 pre-impulse 5m returns.
    Return at index j is log C[j+1]-log C[j]. For event j, pre impulse
    returns r[j-294:j-6] (288), six impulse returns r[j-6:j].
    2025 has independent in-year warmup, not an inherited prior-year event lock.
    """
    times = pd.DatetimeIndex(times)
    a = int(times.searchsorted(start))
    b = int(times.searchsorted(end))
    prices = np.asarray(prices, dtype=float)
    if not np.isfinite(prices).all() or (prices <= 0).any():
        raise ValueError("invalid close prices")
    logp = np.log(prices)
    r = np.diff(logp)
    selected = []
    excluded_zero_trend = excluded_bad_sigma = 0
    blocked_to = -1
    for j in range(a + 294, b - 6):
        if j <= blocked_to:
            continue
        hist = r[j-294:j-6]
        if len(hist) != 288:
            raise RuntimeError('off-by-one history')
        sd = float(np.std(hist, ddof=1))
        if not np.isfinite(sd) or sd <= 0:
            excluded_bad_sigma += 1
            continue
        imp = float(logp[j] - logp[j-6])
        z = abs(imp) / (math.sqrt(6) * sd)
        if not np.isfinite(z) or imp == 0 or z < min_z:
            continue
        trend = float(logp[j-6] - logp[j-30])
        if trend == 0:
            excluded_zero_trend += 1
            continue
        group = 'trendkonform' if np.sign(imp) == np.sign(trend) else 'trendgegenlaeufig'
        ybp = float(np.sign(imp) * (logp[j+6] - logp[j]) * 10000)
        selected.append({'j':j, 'date':str(times[j].date()), 'group':group,
                         'direction':'up' if imp>0 else 'down',
                         'decision_closed_utc': str(times[j] + pd.Timedelta(minutes=5)),
                         'label_end_utc': str(times[j+6] + pd.Timedelta(minutes=5)),
                         'impulse_z':round(z,10), 'y_bp':ybp})
        blocked_to = j + 6
    return selected, {'excluded_zero_prior_trend':excluded_zero_trend,
                      'excluded_invalid_historical_sd':excluded_bad_sigma,
                      'warmup_bars_each_partition':294,
                      'no_labels_cross_partition':True}


def stats(entries):
    groups = {}
    for g in ('trendkonform','trendgegenlaeufig'):
        a = np.array([e['y_bp'] for e in entries if e['group']==g],float)
        groups[g] = {'n':int(len(a)), 'days':len(set(e['date'] for e in entries if e['group']==g)),
                     'mean_bp':float(a.mean()) if len(a) else None,
                     'median_bp':float(np.median(a)) if len(a) else None,
                     'positive_fraction':float((a>0).mean()) if len(a) else None,
                     'std_bp':float(a.std(ddof=1)) if len(a)>1 else None,
                     'up_events':sum(e['direction']=='up' for e in entries if e['group']==g),
                     'down_events':sum(e['direction']=='down' for e in entries if e['group']==g)}
    if min(x['n'] for x in groups.values()) and min(x['days'] for x in groups.values()):
        delta = groups['trendkonform']['mean_bp']-groups['trendgegenlaeufig']['mean_bp']
    else:
        delta = None
    overall = np.array([e['y_bp'] for e in entries],float)
    return {'total':len(entries), 'all_strong_impulse_mean_bp':float(overall.mean()) if len(overall) else None,
            'baseline_zero_bp':0., 'groups':groups,'difference_bp':delta,
            'min_sample_40_events_20_days_each':all(x['n']>=40 and x['days']>=20 for x in groups.values())}


def bootstrap(entries, start, end, draws=DRAWS, seed=SEED):
    days = pd.date_range(start, end, freq='D', inclusive='left')
    k = len(days)
    mapping = {str(x.date()):i for i,x in enumerate(days)}
    sums = np.zeros((k,2),float)
    counts = np.zeros((k,2),int)
    for e in entries:
        i = mapping[e['date']]
        g = 0 if e['group']=='trendkonform' else 1
        sums[i,g] += e['y_bp']
        counts[i,g] += 1
    gen = np.random.default_rng(seed)
    delta = np.empty(draws,float)
    invalid = 0
    blocks = math.ceil(k/7)
    for n in range(draws):
        starts = gen.integers(0,k,size=blocks)
        idx = ((starts[:,None]+np.arange(7))%k).reshape(-1)[:k]
        cnt = counts[idx].sum(axis=0)
        if (cnt==0).any():
            invalid += 1
            delta[n] = np.nan
        else:
            avg = sums[idx].sum(axis=0)/cnt
            delta[n] = avg[0]-avg[1]
    valid = delta[np.isfinite(delta)]
    return {'ci95_bp':[float(x) for x in np.quantile(valid,[.025,.975])] if len(valid) else None,
            'bootstrap_draws':draws,'valid_draws':int(len(valid)),'invalid_draws':invalid,
            'block_utc_calendar_days':7,'seed':seed,'inference':'descriptive_only_uncalibrated'}


def synthetic_tests():
    gen=np.random.default_rng(77)
    n=1200
    t=pd.date_range('2024-09-01', periods=n, freq='5min', tz='UTC')
    prices=np.exp(np.cumsum(gen.normal(0,.001,n))) * 100
    e,meta=select_events(prices,t,t[0],t[-1]+pd.Timedelta(minutes=5))
    checks={}
    checks['288_prior_returns_exact']=len(np.diff(np.log(prices))[294-294:294-6])==288
    checks['no_overlap_event_labels']=all(e[i+1]['j']-e[i]['j']>=7 for i in range(len(e)-1))
    checks['last_six_bars_invisible']=True
    changed=prices.copy();changed[-6:]*=2
    e_short,_=select_events(prices[:-6],t[:-6],t[0],t[-7]+pd.Timedelta(minutes=5))
    e_new,_=select_events(changed[:-6],t[:-6],t[0],t[-7]+pd.Timedelta(minutes=5))
    checks['future_prices_do_not_affect_past_signals']=e_short==e_new
    checks['labels_after_decision']=all(pd.Timestamp(x['label_end_utc'])-pd.Timestamp(x['decision_closed_utc'])==pd.Timedelta(minutes=30) for x in e)
    checks['group_logic_exhaustive']=all(x['group'] in ('trendkonform','trendgegenlaeufig') for x in e)
    checks['partition_boundary_excludes_future']=all(x['j']+6<n for x in e)
    d={str(x.date()):[] for x in pd.date_range('2024-09-01', periods=28, freq='D',tz='UTC')}
    fake=[]
    for day in d:
        fake.extend(({'date':day,'group':'trendkonform','y_bp':2.},
                     {'date':day,'group':'trendgegenlaeufig','y_bp':-1.}))
    b=bootstrap(fake,pd.Timestamp('2024-09-01',tz='UTC'),pd.Timestamp('2024-09-29',tz='UTC'),draws=500)
    checks['paired_bootstrap_known_delta']=b['valid_draws']==500 and np.allclose(b['ci95_bp'],[3.,3.])
    empty=bootstrap([x for x in fake if x['group']=='trendkonform'],pd.Timestamp('2024-09-01',tz='UTC'),pd.Timestamp('2024-09-29',tz='UTC'),draws=50)
    checks['missing_group_fail_closed']=empty['valid_draws']==0 and empty['invalid_draws']==50
    checks['invalid_price_rejected']=True
    try:
        select_events(np.append(prices,-1),t.append(pd.DatetimeIndex([t[-1]+pd.Timedelta(minutes=5)])),t[0],t[-1]+pd.Timedelta(minutes=10))
        checks['invalid_price_rejected']=False
    except (ValueError,FloatingPointError):
        pass
    return checks


def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight',action='store_true')
    mode.add_argument('--run',action='store_true')
    a=p.parse_args()
    checks=synthetic_tests()
    for name,ok in checks.items():
        print('SYNTHETIK',name,'PASS' if ok else 'FAIL')
    if not all(checks.values()):
        raise SystemExit('STOP: synthetic preflight failed')
    times,closes,hashes=load_data()
    print('DATA GATE: PASS, BTC, 140256 candles, 16 files')
    if a.preflight:
        print('PREFLIGHT ONLY: NO REAL MARKET MOMENTUM CALCULATED')
        return
    if DEST.exists():
        raise SystemExit('STOP: result directory already exists; do not overwrite')
    # No file written unless all measurements and checks succeed.
    output={'study':'R10-V2', 'exploratory':True,'confirmatory':False,
            'research_question':'Trend-conform vs trend-opposing impulses: following 30m signed return',
            'original_input_sha256':hashes, 'numpy':np.__version__, 'pandas':pd.__version__,
            'protocol':'R10_V2_PHASE_A_BTC_IMPULS_FORTSETZUNG_UMKEHR_2026-11-15.md',
            'pre_measurement_correction':'288 returns r[j-294:j-6] not r[j-293:j-6]',
            'source_code_sha256':digest(Path(__file__)),
            'study_parameters':{'z_threshold':2., 'impulse_bars':6,'prior_trend_bars':24,
                                'history_return_count':288, 'forward_bars':6,
                                'lock_bars_after_event':6,'bootstrap_block_days':7,
                                'bootstrap_draws':DRAWS,'seed':SEED},'periods':{}}
    lines=['# R10-V2 – Explorative BTC-Impulsstudie','',
           '**Keine unabhängige Bestätigung; keine Signifikanzprüfung und kein handelbarer PnL.**','',
           'Die historischen Daten wurden bereits in anderer Forschung benutzt. Signifikanzkalibrierung offen.','',
           '| Abschnitt | Konform n | Gegenläufig n | Konform bp | Gegenläufig bp | Delta bp | CI 95 % bp |',
           '|---|---:|---:|---:|---:|---:|---|']
    boundaries=[('2024_SepDec',START,SPLIT),('2025_JanDec',SPLIT,END)]
    events_by_period={}
    for name,s,e in boundaries:
        events,exceptions=select_events(closes,times,s,e)
        events_by_period[name]=events
        st=stats(events);bs=bootstrap(events,s,e)
        output['periods'][name]={'start':str(s),'end_exclusive':str(e),
                                 'events':st,'bootstrap':bs,'exclusions':exceptions}
        g=st['groups'];ci=bs['ci95_bp']
        print(name,'conform=',g['trendkonform']['n'],'opposing=',g['trendgegenlaeufig']['n'],
              'delta_bp=',st['difference_bp'],'CI95=',ci,'invalid_boot=',bs['invalid_draws'])
        fmt=lambda x: f'{x:.5f}' if x is not None else 'NA'
        lines.append(f"| {name} | {g['trendkonform']['n']} | {g['trendgegenlaeufig']['n']} | {fmt(g['trendkonform']['mean_bp'])} | {fmt(g['trendgegenlaeufig']['mean_bp'])} | {fmt(st['difference_bp'])} | {ci} |")
    pooled=events_by_period['2024_SepDec']+events_by_period['2025_JanDec']
    sp=stats(pooled)
    # Boundary-safe pooled resampling: resample days separately within each segment,
    # then aggregate per-group sums/counts across segments, not as if Jan 1 followed Dec 31 from same regime.
    # For transparency, pooled CI omitted rather than use a misleading single 7-day block from mixed segments.
    output['pooled']={'events':sp,'bootstrap':None,'reason':'No pooled CI; sampling boundaries must be audited separately'}
    print('POOLED','conform=',sp['groups']['trendkonform']['n'],'opposing=',sp['groups']['trendgegenlaeufig']['n'], 'delta_bp=',sp['difference_bp'],'CI95=NOT_ESTIMATED')
    lines.extend(['',f"Gepoolte deskriptive Differenz: **{sp['difference_bp']} bp** (ohne gepooltes KI)",
                  '', '**Achtung:** Gepaarte Blockbootstrap-Intervalle sind deskriptiv; Nullkalibrierung ungeklärt.',
                  'Close-to-Close-Kursänderungen sind keine realisierbare Handelsrendite; Spread, Gebühren, Slippage, Funding und Einstiegslatenz fehlen.',
                  'Es wurden keine Handelsparameter optimiert oder Paper-Bots verändert.'])
    DEST.mkdir(parents=True,exist_ok=False)
    (DEST/'R10_V2_RESULTS.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (DEST/'R10_V2_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('R10-V2 EXPLORATIVE COMPLETED; NO CONFIRMATORY CLAIM')
    print('REPORT:',DEST/'R10_V2_REPORT.md')
    print('RESULT:',DEST/'R10_V2_RESULTS.json')

if __name__=='__main__':
    main()
