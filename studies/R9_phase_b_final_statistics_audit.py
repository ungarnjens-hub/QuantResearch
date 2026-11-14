#!/usr/bin/env python3
"""R9 phase B: read-only source audit and synthetic calibration. Never scores real returns.

Usage: python R9_phase_b_final_statistics_audit.py --run
Outputs in ~/QuantResearch/R9_PhaseB_FinalAudit; does not touch source files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ASSETS = ('BTC', 'ETH')
START = pd.Timestamp('2024-09-01T00:00:00Z')
END = pd.Timestamp('2026-01-01T00:00:00Z')
ROOT = Path.home() / 'Dokumente/TradingLab/data/canonical/binance/perpetual/klines'
OUTPUT = Path.home() / 'QuantResearch/R9_PhaseB_FinalAudit'
SEED = 20261114
BOOTSTRAPS = 500  # Synthetic calibration only; real-analysis preregistration remains 5000
SIMULATIONS = 200
BLOCK = 7


def sha256(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def read_only_audit():
    out = {}
    expected = pd.date_range(START, END, freq='5min', inclusive='left')
    for a in ASSETS:
        folder = ROOT / f'{a}_USDT/5m'
        names = [f'{a}_USDT_5m_{y}-{m:02d}_v1.0.parquet'
                 for y, lo, hi in [(2024, 9, 12), (2025, 1, 12)] for m in range(lo, hi + 1)]
        files = [folder / n for n in names]
        hashes = {}
        ts_parts = []
        checks = {'16_files':len(files) == 16, 'files_exist':all(p.is_file() for p in files)}
        if not checks['files_exist']:
            out[a] = {'checks':checks, 'missing':[p.name for p in files if not p.is_file()]}
            continue
        rowcount = 0
        for f in files:
            cols = ['open_time','close_time','open','high','low','close','volume_base',
                    'is_closed','exchange','market_type','contract_type','timeframe',
                    'price_source','source_endpoint']
            df = pd.read_parquet(f)
            if not set(cols).issubset(df):
                checks['required_columns'] = False
                break
            hashes[f.name] = sha256(f)
            t = pd.DatetimeIndex(df['open_time'])
            ts_parts.append(t)
            rowcount += len(df)
            pr = df[['open','high','low','close']].to_numpy(dtype=float)
            volume = df['volume_base'].to_numpy(dtype=float)
            close_t = pd.DatetimeIndex(df['close_time'])
            meta = (df['exchange'].eq('binance').all() and
                    df['market_type'].eq('perpetual').all() and
                    df['contract_type'].eq('linear').all() and
                    df['timeframe'].eq('5m').all() and
                    df['price_source'].eq('last_trade').all() and
                    df['source_endpoint'].eq('/fapi/v1/klines').all())
            conditions = {
                'source_metadata':bool(meta),
                'closed_candles':bool(df['is_closed'].all()),
                'ohlc_positive_finite':bool(np.isfinite(pr).all() and (pr>0).all()),
                'ohlc_consistent':bool((pr[:,1]>=np.maximum(pr[:,0],pr[:,3])).all() and
                                      (pr[:,2]<=np.minimum(pr[:,0],pr[:,3])).all() and
                                      (pr[:,1]>=pr[:,2]).all()),
                'volume_base_valid':bool(np.isfinite(volume).all() and (volume>=0).all()),
                'candle_close_time':bool(((close_t-t)==pd.Timedelta(minutes=5)-pd.Timedelta(milliseconds=1)).all()),
                'utc':str(t.tz)=='UTC' and str(close_t.tz)=='UTC',
            }
            for k, v in conditions.items():
                checks[k] = checks.get(k, True) and v
        else:
            checks['required_columns'] = True
            all_ts = ts_parts[0].append(ts_parts[1:])
            checks['complete_exact_grid'] = all_ts.equals(expected)
            checks['unique_monotonic'] = all_ts.is_unique and all_ts.is_monotonic_increasing
            checks['rowcount_140256'] = rowcount==140256
        out[a] = {'checks':checks,'passed':bool(all(checks.values())),
                  'rows':rowcount, 'source_sha256':hashes}
    return out


def block_draws(n, block, draws, rng):
    starts = rng.integers(0,n,size=(draws,math.ceil(n/block)))
    offsets = np.arange(block)[None,None,:]
    return ((starts[:,:,None]+offsets)%n).reshape(draws,-1)[:,:n]


def paired_inference(days, draws=BOOTSTRAPS, rng=None):
    """Daily sums and group counts, common circular 7-day moving blocks.
    days: [n_days, 4] containing sum_M, count_M, sum_B, count_B.
    Bootstrap centered p is an approximate one-sided bootstrap test, NOT exact.
    """
    d = np.asarray(days, dtype=float)
    if len(d)<2*BLOCK or np.any(d[:,[1,3]]<0):
        raise ValueError('invalid days')
    cm, cb = d[:,1].sum(), d[:,3].sum()
    if min(cm,cb)==0: return None
    obs = d[:,0].sum()/cm - d[:,2].sum()/cb
    idx = block_draws(len(d), BLOCK, draws, rng or np.random.default_rng(SEED))
    sample = d[idx].sum(axis=1)
    valid = (sample[:,1]>0)&(sample[:,3]>0)
    if valid.sum()<int(draws*.95): return None
    val = sample[valid,0]/sample[valid,1]-sample[valid,2]/sample[valid,3]
    ci = np.percentile(val,[2.5,97.5]).tolist()
    centered = val-obs
    p = (1+np.count_nonzero(centered>=obs))/(len(centered)+1)
    return {'delta':float(obs),'ci95':ci,'p_approx_one_sided':float(p),
            'valid_resamples':len(val),'invalid_resamples':int((~valid).sum())}


def holm(p):
    """Holm step-down adjusted p values."""
    p = np.asarray(p)
    order=np.argsort(p)
    adj=np.empty_like(p)
    peak=0.0
    for i, index in enumerate(order):
        peak=max(peak,min(1.0,(len(p)-i)*p[index]))
        adj[index]=peak
    return adj


def simulate(seed, effect=0.0, type_='independent'):
    """Synthetic daily-level common shocks and serial dependence; no real data.
    Null 1: independent groups conditional on common day shocks.
    Null 2: regimes influence group frequency and outcome variance, no mean difference.
    Alternative: +0.002 mean per qualified M event.
    """
    rng=np.random.default_rng(seed)
    n=240
    a=np.zeros(n)
    for j in range(1,n):a[j]=.68*a[j-1]+rng.normal(0,.0018)
    regime=np.zeros(n,dtype=int)
    current=0
    for j in range(n):
        if rng.random()<.06: current=1-current
        regime[j]=current
    rows=[]
    for i in range(n):
        if type_=='regimes':
            nm=rng.poisson(2.6 if regime[i] else 1.2)
            nb=rng.poisson(1.1 if regime[i] else 2.5)
            sigma=.003 if regime[i] else .0015
        else:
            nm=rng.poisson(1.8)
            nb=rng.poisson(1.8)
            sigma=.002
        # Common day shock: different group counts do not induce a systematic population mean effect.
        ym=(nm*(a[i]+effect)+rng.normal(0,sigma*math.sqrt(nm)) if nm else 0)
        yb=(nb*a[i]+rng.normal(0,sigma*math.sqrt(nb)) if nb else 0)
        rows.append([ym,nm,yb,nb])
    return np.asarray(rows)


def synthetic_calibration():
    cases={}
    for label,effect,typ in [('independent_null',0,'independent'),
                             ('regime_null',0,'regimes'),
                             ('positive_alternative',.002,'independent')]:
        pvals=[]
        positive=[]
        unfit=0
        for j in range(SIMULATIONS):
            days=simulate(SEED+100000*j+{'independent_null':1,'regime_null':2,'positive_alternative':3}[label],effect,typ)
            r=paired_inference(days,rng=np.random.default_rng(SEED+500000+j))
            if r is None:
                unfit+=1
            else:
                pvals.append(r['p_approx_one_sided'])
                positive.append(r['ci95'][0]>0)
        rate=sum(p<.05 for p in pvals)/len(pvals) if pvals else None
        cases[label]={'simulations':SIMULATIONS,'valid':len(pvals),'unfit':unfit,
                      'p_less_0_05':sum(p<.05 for p in pvals),
                      'rate':rate,'positive_95ci':sum(positive)}
    # Three-market Holm family check with independently simulated null assets (tests can be correlated in reality).
    holm_false=0
    for j in range(SIMULATIONS):
        ps=[]
        for k in range(3):
            days=simulate(SEED+700000+100*j+k,0,'independent')
            result=paired_inference(days,rng=np.random.default_rng(SEED+800000+100*j+k))
            ps.append(result['p_approx_one_sided'] if result else 1.)
        holm_false+=bool(np.any(holm(ps)<.05))
    cases['three_assets_holm_independent_null']={'simulations':SIMULATIONS,
                                                 'family_false_alarms':holm_false,
                                                 'rate':holm_false/SIMULATIONS}
    return cases


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run',action='store_true')
    args=ap.parse_args()
    if not args.run: ap.error('Only --run accepted. No actual market performance runs.')
    data=read_only_audit()
    calibration=synthetic_calibration()
    # This is a diagnostic, not proof of statistical validity in real markets.
    statistical_gate=(calibration['independent_null']['rate']<=.05 and
                      calibration['regime_null']['rate']<=.05 and
                      calibration['three_assets_holm_independent_null']['rate']<=.05)
    passed=all(data.get(a,{}).get('passed',False) for a in ASSETS) and statistical_gate
    report={'audit':'R9 phase B final', 'utc':datetime.now(timezone.utc).isoformat(),
            'script_sha256':sha256(Path(__file__)),
            'env':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__},
            'sources':data,'synthetic_calibration':calibration,
            'statistical_calibration_heuristic_pass':statistical_gate,
            'overall_pass':passed,
            'phase_C_approved':False,
            'notice':'NO real-momentum, returns, trades, fees, or PNL calculated. Synthetic error-rate tolerance 0.05 is diagnostic only; not a research significance threshold.'}
    OUTPUT.mkdir(parents=True,exist_ok=True)
    dest=OUTPUT/'R9_PHASE_B_FINAL_AUDIT.json'
    if dest.exists():
        raise SystemExit(f'STOP: result already exists, no overwrite: {dest}')
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('R9 FINAL DATA AUDIT:', 'PASS' if all(data.get(a,{}).get('passed',False) for a in ASSETS) else 'FAIL')
    for a in ASSETS:
        v=data[a]
        print(f'{a}:', 'PASS' if v.get('passed') else 'FAIL', f"rows={v.get('rows')}")
        for k, ok in v['checks'].items():
            if not ok:print(' FAIL:',k)
    print('R9 SYNTHETIC CALIBRATION:')
    for key,v in calibration.items():
        print(f" {key}: {v.get('p_less_0_05',v.get('family_false_alarms'))}/{v['simulations']} p<0.05, rate={v['rate']:.3f}")
    print('R9 STATISTICAL CALIBRATION HEURISTIC:', 'PASS' if statistical_gate else 'FAIL')
    print('R9 PHASE C: NOT APPROVED; NO REAL MARKET EVENT/RETURN/PNL MEASURED')
    print('RESULT:',dest)
    raise SystemExit(0 if passed else 2)

if __name__=='__main__':main()
