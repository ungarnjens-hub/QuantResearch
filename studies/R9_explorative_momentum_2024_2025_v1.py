#!/usr/bin/env python3
"""R9 registered exploratory descriptive market-mechanism run, BTC/ETH, 2024/2025.

Never reads or writes live bots. Read-only Parquet originals, isolated one-time output.
The 7-day block bootstrap is DESCRIPTIVE, NOT A VALIDATED SIGNIFICANCE TEST.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

START = pd.Timestamp('2024-09-01', tz='UTC')
SPLIT = pd.Timestamp('2025-01-01', tz='UTC')
END = pd.Timestamp('2026-01-01', tz='UTC')
SYMBOLS = ('BTC', 'ETH')
SEED = 20261114
DRAW = 5000
BLOCK = 7
PERIODS = {'2024_SepDec': (START, SPLIT), '2025_JanDec': (SPLIT, END), 'pooled_2024_2025': (START, END)}
SOURCE = Path.home() / 'Dokumente/TradingLab/data/canonical/binance/perpetual/klines'
OUT = Path.home() / 'QuantResearch/R9_Explorativ/Sep2024_Dec2025_v1'


def sha(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_market(coin: str):
    paths = [SOURCE / f'{coin}_USDT/5m/{coin}_USDT_5m_{x}_v1.0.parquet'
             for x in pd.period_range('2024-09', '2025-12', freq='M').astype(str)]
    if any(not p.is_file() for p in paths):
        raise RuntimeError('Missing monthly files: ' + ', '.join(p.name for p in paths if not p.is_file()))
    columns = ['open_time', 'close_time', 'open', 'high', 'low', 'close', 'is_closed',
               'exchange', 'market_type', 'contract_type', 'timeframe', 'price_source',
               'source_endpoint', 'volume_base', 'canonical_symbol', 'data_family']
    expected = pd.date_range(START, END, freq='5min', inclusive='left')
    hashes, frames = {}, []
    for p in paths:
        hashes[p.name] = sha(p)
        frames.append(pd.read_parquet(p, columns=columns))
    d = pd.concat(frames, ignore_index=True)
    times = pd.DatetimeIndex(d['open_time'])
    if len(d) != len(expected) or not times.equals(expected) or not times.is_unique:
        raise RuntimeError(f'{coin}: 5m UTC time grid incomplete or duplicated')
    if not (pd.DatetimeIndex(d['close_time']) == (times + pd.Timedelta(minutes=5) - pd.Timedelta(milliseconds=1))).all():
        raise RuntimeError(f'{coin}: close_time semantics are inconsistent')
    if not bool(d['is_closed'].all()):
        raise RuntimeError(f'{coin}: unclosed bars')
    metadata = {'exchange':'binance', 'market_type':'perpetual', 'contract_type':'linear',
                'timeframe':'5m', 'price_source':'last_trade',
                'source_endpoint':'/fapi/v1/klines', 'canonical_symbol':f'{coin}_USDT',
                'data_family':'klines'}
    for key, value in metadata.items():
        if not bool(d[key].eq(value).all()):
            raise RuntimeError(f'{coin}: invalid {key} metadata')
    p = d[['open', 'high', 'low', 'close']].to_numpy(dtype=float)
    vol = d['volume_base'].to_numpy(dtype=float)
    if not (np.isfinite(p).all() and (p > 0).all() and np.isfinite(vol).all() and (vol >= 0).all()):
        raise RuntimeError(f'{coin}: price or volume invalid')
    if not (np.all(p[:, 1] >= np.maximum(p[:, 0], p[:, 3]))
            and np.all(p[:, 2] <= np.minimum(p[:, 0], p[:, 3]))
            and np.all(p[:, 1] >= p[:, 2])):
        raise RuntimeError(f'{coin}: OHLC inconsistent')
    return times, p[:,3], vol, hashes


def scan_events(logp, volume, times):
    """Everything used at event j has been closed by t=times[j]+5min.

    Impulse returns: r[j-6:j] if r[k] = logp[k+1]-logp[k]
    Historical returns: r[j-294:j-6], exactly 288 before impulse start.
    Historical 5m volumes: vol[j-293:j-5], exactly 288, end j-6.
    Impulse volumes: vol[j-5:j+1], exactly six, end j.
    Future signed return: logp[j+6]-logp[j].
    """
    r = np.diff(logp)
    out = []
    lock_until = -1
    for j in range(294, len(logp) - 6):
        if j <= lock_until:
            continue
        h = r[j-294:j-6]
        basev = volume[j-293:j-5]
        impv = volume[j-5:j+1]
        sd = float(np.std(h, ddof=1))
        med = float(np.median(basev))
        if not (sd > 0 and med > 0):
            continue
        impulse = float(logp[j] - logp[j-6])
        if impulse == 0:
            continue
        z = abs(impulse) / (math.sqrt(6) * sd)
        if z < 2.0:
            continue
        ratio = float(impv.sum() / (6 * med))
        event_t = times[j] + pd.Timedelta(minutes=5)
        label_t = times[j+6] + pd.Timedelta(minutes=5)
        # Do not evaluate any 2024 event whose label crosses into 2025.
        if event_t < SPLIT and label_t > SPLIT:
            continue
        out.append({'time':event_t, 'label_end':label_t,
                    'period':'2024_SepDec' if event_t < SPLIT else '2025_JanDec',
                    'group':'M1' if ratio >= 1.5 else 'B1',
                    'y':float(np.sign(impulse)*(logp[j+6]-logp[j])),
                    'z':z, 'volume_ratio':ratio, 'direction':'long' if impulse > 0 else 'short'})
        lock_until = j + 6
    return out


def bootstrap(df, start, end, seed):
    days = pd.date_range(start, end, freq='D', inclusive='left')
    n = len(days)
    daily = np.zeros((n, 4), dtype=float)  # M1 sum,count B1 sum,count
    ids = (df['time'].dt.floor('D') - start) / pd.Timedelta(days=1)
    for ix, (y, group) in zip(ids.to_numpy(dtype=int), zip(df['y'], df['group'])):
        k = 0 if group == 'M1' else 2
        daily[ix,k] += y
        daily[ix,k+1] += 1
    rng = np.random.default_rng(seed)
    vals = []
    invalid = 0
    for _ in range(DRAW):
        starts = rng.integers(0, n, size=math.ceil(n/BLOCK))
        picked = (starts[:, None] + np.arange(BLOCK)[None, :]) % n
        x = daily[picked.ravel()[:n]].sum(axis=0)
        if x[1] == 0 or x[3] == 0:
            invalid += 1
            continue
        vals.append(x[0]/x[1]-x[2]/x[3])
    if not vals:
        return {'valid':0,'invalid':invalid,'ci95_bp':None,'ci_bonf_screen_bp':None}
    a = np.asarray(vals)
    return {'valid':len(vals),'invalid':invalid,'ci95_bp':(np.quantile(a, [.025,.975])*10000).tolist(),
            'ci_bonf_screen_bp':(np.quantile(a, [1/120, 119/120])*10000).tolist()}


def summarize(df, first, last, seed):
    outcome = {'events':len(df)}
    for gr in ('M1','B1'):
        d = df.loc[df['group']==gr]
        y = d['y'].to_numpy(dtype=float)
        outcome[gr] = {'n':len(d), 'event_days':int(d['time'].dt.floor('D').nunique()),
                       'mean_bp': float(y.mean()*1e4) if len(y) else None,
                       'median_bp':float(np.median(y)*1e4) if len(y) else None,
                       'positive_rate':float((y>0).mean()) if len(y) else None,
                       'mean_z':float(d['z'].mean()) if len(y) else None,
                       'median_z':float(d['z'].median()) if len(y) else None,
                       'mean_volume_ratio':float(d['volume_ratio'].mean()) if len(y) else None,
                       'long_n':int((d['direction']=='long').sum()),
                       'short_n':int((d['direction']=='short').sum())}
    valid_groups = all(outcome[g]['n'] > 0 for g in ('M1','B1'))
    outcome['delta_bp'] = outcome['M1']['mean_bp']-outcome['B1']['mean_bp'] if valid_groups else None
    outcome['bootstrap'] = bootstrap(df, first, last, seed)
    gates = {'M1_min_40':outcome['M1']['n']>=40,'B1_min_40':outcome['B1']['n']>=40,
             'M1_min_20_days':outcome['M1']['event_days']>=20,
             'B1_min_20_days':outcome['B1']['event_days']>=20,
             'bootstrap_99pct_valid':outcome['bootstrap']['valid']>=.99*DRAW}
    outcome['descriptive_sample_gates'] = gates
    # Report screening thresholds without statistical significance decisions;
    # prior synthetic 9% false alarms prevent inferential claim.
    outcome['screen_not_significance'] = None
    outcome['by_month'] = {}
    if len(df):
        for month, sub in df.groupby(df['time'].dt.strftime('%Y-%m')):
            mm = sub.loc[sub['group']=='M1','y']
            bb = sub.loc[sub['group']=='B1','y']
            outcome['by_month'][month] = {
                'M1_n':len(mm),'B1_n':len(bb),
                'M1_days':int(sub.loc[sub['group']=='M1','time'].dt.floor('D').nunique()),
                'B1_days':int(sub.loc[sub['group']=='B1','time'].dt.floor('D').nunique()),
                'delta_bp':float((mm.mean()-bb.mean())*1e4) if len(mm) and len(bb) else None}
    return outcome


def selftest():
    # Fixed impulse appears only when its closing index j is known.
    n=700; p=np.exp(np.cumsum(np.random.default_rng(43).normal(0,.002,n)))
    v=np.ones(n)*20
    dates=pd.date_range('2024-09-01', periods=n, freq='5min', tz='UTC')
    a=scan_events(np.log(p),v,dates)
    assert all(a[k+1]['time']-a[k]['time']>=pd.Timedelta(minutes=35) for k in range(len(a)-1))
    assert all(z['label_end']-z['time']==pd.Timedelta(minutes=30) for z in a)
    assert all(z['period']=='2024_SepDec' for z in a)
    # Horizon-and-history off-by-one, exactly 288 observations in each.
    j=294
    assert len(np.diff(np.log(p))[j-294:j-6])==288
    assert len(v[j-293:j-5])==288
    assert len(v[j-5:j+1])==6
    # Paired-block known deterministic delta.
    x=[]
    for day in pd.date_range('2024-09-01','2024-10-01',freq='D',tz='UTC',inclusive='left'):
        for group,y in [('M1',.002),('B1',-.001)]:
            x.append({'time':day,'y':y,'group':group})
    bd=bootstrap(pd.DataFrame(x),pd.Timestamp('2024-09-01',tz='UTC'),pd.Timestamp('2024-10-01',tz='UTC'),SEED)
    assert bd['invalid']==0 and np.allclose(bd['ci95_bp'],[30,30],atol=1e-9)
    # Empty group fails closed, with 5000 invalids.
    e=bootstrap(pd.DataFrame(x).query("group=='M1'"),pd.Timestamp('2024-09-01',tz='UTC'),pd.Timestamp('2024-10-01',tz='UTC'),SEED)
    assert e['valid']==0 and e['invalid']==DRAW
    return True


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--preflight', action='store_true', help='read-only metadata + synthetic tests, NO real market event computation')
    group.add_argument('--run', action='store_true', help='EXPLORATORY one-shot real market measurement')
    args=ap.parse_args()
    selftest()
    print('R9 SYNTHETIC PREFLIGHT: PASS')
    inputs={}
    datasets={}
    for c in SYMBOLS:
        t, close, v, hashes = load_market(c)
        inputs[c]={'files_sha256':hashes,'rows':len(t),'first_open_time':str(t[0]),'last_open_time':str(t[-1]),
                   'origin_endpoint':'/fapi/v1/klines (recorded in source metadata; not independently queried)'}
        datasets[c]=(t,close,v)
        print(f'{c} DATA GATE: PASS {len(t)} rows, {len(hashes)} monthly files')
    if args.preflight:
        print('R9 PREFLIGHT ONLY. NO REAL MARKET RETURNS OR MOMENTUM EVENTS COMPUTED.')
        return
    if OUT.exists():
        raise RuntimeError(f'FAIL CLOSED: Output exists, refusing second run: {OUT}')
    OUT.mkdir(parents=True,exist_ok=False)
    result={'study':'R9', 'version':'v1', 'classification':'EXPLORATORY ONLY',
            'phase':'C exploratory (not confirmatory)',
            'run_utc':datetime.now(timezone.utc).isoformat(),
            'method':'z>=2.0, v>=1.5, 6-bar lock, next 30m signed log return',
            'bootstrap':'7 UTC calendar day circular moving block, 5000, seed 20261114',
            'statistical_inference':'NOT AUTHORIZED (synthetic null calibration failed; CI descriptive only)',
            'economic_inference':'NOT AUTHORIZED (close-to-close proxy; no fees/spread/slippage/funding)',
            'python':platform.python_version(), 'numpy':np.__version__, 'pandas':pd.__version__,
            'script_sha256':sha(Path(__file__).resolve()), 'input':inputs, 'markets':{}}
    for coin in SYMBOLS:
        t, close, v=datasets[coin]
        ev=scan_events(np.log(close),v,t)
        frame=pd.DataFrame(ev)
        if len(frame)==0:
            raise RuntimeError(f'{coin}: no events; cannot evaluate')
        result['markets'][coin]={}
        for key,(a,b) in PERIODS.items():
            sub=frame.loc[(frame['time']>=a)&(frame['time']<b)].copy()
            result['markets'][coin][key]=summarize(sub,a,b,SEED)
        print(f'=== {coin} ===')
        for key in PERIODS:
            q=result['markets'][coin][key]
            print(f"{key}: M1={q['M1']['n']} B1={q['B1']['n']} delta_bp={q['delta_bp']} "
                  f"CI95_BP={q['bootstrap']['ci95_bp']} invalid_boot={q['bootstrap']['invalid']}")
        # Only summarized research data, not large raw events, into the output folder.
    js=OUT/'R9_EXPLORATIVE_RESULTS.json'
    js.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf8')
    report=['# R9: Explorative Momentum-Auswertung September 2024 bis Dezember 2025','',
            '**Kein bestätigter Handelssignal-Vorteil, kein Blindtest, kein PnL.**','',
            'Daten: Binance USD-M Linear Perpetual BTC/ETH Last-Trade-5m, Volume `volume_base`. 2024/2025 wurden in früheren Forschungsvorhaben teils bereits verwendet.','',
            'Primärer Effekt: Durchschnitt signierte 30m-Logrendite bei starkem 30m-Impuls mit `v>=1.5` minus `v<1.5`, je Markt; Einheit Basispunkte.','',
            'Bootstrap-CIs sind ausschließlich deskriptiv: Die zuvor geprüfte Nullkalibrierung der Signifikanzregel fiel durch (bis 9% Fehlalarme). **Keine Signifikanzbehauptung.**','',
            '| Markt | Zeitraum | M1 n/Tage | B1 n/Tage | Mittel M1 (bp) | Mittel B1 (bp) | Delta (bp) | 95% deskriptives CI (bp) |','|---|---|---:|---:|---:|---:|---:|---|']
    for coin, outcomes in result['markets'].items():
        for key, q in outcomes.items():
            ci=q['bootstrap']['ci95_bp']
            cistr=f'[{ci[0]:+.3f}, {ci[1]:+.3f}]' if ci is not None else 'nicht auswertbar'
            def fmt(a): return f'{a:+.3f}' if a is not None else 'NA'
            report.append(f"| {coin} | {key} | {q['M1']['n']}/{q['M1']['event_days']} | {q['B1']['n']}/{q['B1']['event_days']} | {fmt(q['M1']['mean_bp'])} | {fmt(q['B1']['mean_bp'])} | {fmt(q['delta_bp'])} | {cistr} |")
    report.extend(['','## Einschränkungen','',
                   '- Jahresabschnitte und Pool wurden vor Ausführung festgelegt; 2025 ist kein unabhängiger Holdout.',
                   '- Gruppendifferenzen können auf Impulsstärke, Volatilitätsregime und Uhrzeit beruhen; kein kausaler Volumeneffekt.',
                   '- Close-to-Close-Renditen setzen keinen ausführbaren Einstieg zum Signal-Schluss voraus. Keine Nettoertragsrechnung.',
                   '- Mindestereigniszahl 40 pro Gruppe auf 20 Tagen und Bootstrap-Gültigkeit sind nur deskriptive Stabilitätsgates.',
                   '- Keine Parametersuche, nachträgliche Market-Auswahl oder Entscheidungsoptimierung.',
                   '- Input-Hashes, Skript-Hash und vollständige Monatsaufschlüsselungen: `R9_EXPLORATIVE_RESULTS.json`.','',
                   '**R9 unabhängige Bestätigung: NICHT DURCHGEFÜHRT. R9 Handelsstrategie: NICHT NACHGEWIESEN.**',''])
    (OUT/'R9_EXPLORATIVE_REPORT.md').write_text('\n'.join(report),encoding='utf8')
    print('R9 EXPLORATORY COMPLETED; NOT CONFIRMATORY')
    print('REPORT:', OUT/'R9_EXPLORATIVE_REPORT.md')
    print('RESULT:', js)


if __name__=='__main__':
    main()
