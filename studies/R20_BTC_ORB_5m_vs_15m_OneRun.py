#!/usr/bin/env python3
"""R20: One-shot exploratory BTC US-open ORB: 5-minute vs frozen R19 15-minute range.
Research only. Reads canonical BTC data via hash-pinned R19/R12; creates new isolated outputs.
Usage: python R20_BTC_ORB_5m_vs_15m_OneRun.py --preflight | --run
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math
from pathlib import Path
import numpy as np
import pandas as pd

STUDIES = Path.home()/'QuantResearch-Git/studies'
REF = STUDIES/'R19_BTC_NY_ORB_Fakeout_OneRun.py'
REF_SHA = 'a626bce4bad126e372247bb15c061c861ebc2b8b5cf9157c7c2e4340a8d88769'
OLD_RESULT = Path.home()/'QuantResearch/R19_BTC_NY_Open/Sep2024_Dec2025_v1/R19_RESULTS.json'
OUT = Path.home()/'QuantResearch/R20_BTC_ORB_5m_15m/Sep2024_Dec2025_v1'
COST_BASE = 14.; COST_STRESS = 24.; SEED=20261115; BOOT=2000; BLOCK=7


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def reference():
    if not REF.is_file() or sha(REF)!=REF_SHA:
        raise RuntimeError('STOP: eingefrorener R19-Code fehlt oder SHA256 stimmt nicht')
    spec=importlib.util.spec_from_file_location('frozen_r19_for_r20',REF)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m


def five_minute_orb(a, old):
    """Same date universe as R19; one 5m opening bar and first later close outside it."""
    m=reference()
    t=a['t']; ny=t.tz_convert(m.NY)
    mm=np.asarray(ny.hour)*60+np.asarray(ny.minute)
    starts=np.flatnonzero(mm==570)
    old_dates=set(old.ny_date)
    rec=[]
    used=set()
    for s in starts:
        date=str(ny[s].date())
        if date not in old_dates:continue
        if date in used:raise RuntimeError('duplicate NY day')
        used.add(date)
        yr=t[s].year; end=min(len(t),int(t.searchsorted(pd.Timestamp(f'{yr+1}-01-01',tz='UTC'))))
        if s+60>=end:raise RuntimeError('missing future in R19 session')
        hi=float(a['h'][s]); lo=float(a['l'][s]);mid=(hi+lo)/2
        first=None;d=0
        # First possible signal is 09:35-09:40 close (j=s+1); next open 09:40.
        # Same last signal as R19: candle s+23, next open 11:30.
        for j in range(s+1,s+24):
            if a['c'][j]>hi:first=j;d=1;break
            if a['c'][j]<lo:first=j;d=-1;break
        if first is None:continue
        res=m.execution(a,first+1,end,d,mid)
        if res is None:continue
        rec.append({'ny_date':date,'period':'2024_SepDec' if yr==2024 else '2025_JanDec',
                    'strategy':'ORB_5m','range_bp':(hi/lo-1)*1e4,'signal_idx':first,
                    'signal_utc':str(t[first]),'signal_ny':str(ny[first]),'entry_utc':str(t[first+1]),
                    'direction':d,**res})
    if used!=old_dates:raise RuntimeError(f'NY-day mismatch: R19={len(old_dates)} R20={len(used)}')
    return pd.DataFrame(rec)


def block_ci(x, seed):
    x=np.asarray(x,dtype=float);n=len(x)
    if n<14:return None
    rng=np.random.default_rng(seed);y=np.empty(BOOT)
    for k in range(BOOT):
        ix=[]
        while len(ix)<n:
            p=int(rng.integers(n));ix.extend((p+np.arange(BLOCK))%n)
        y[k]=float(x[np.asarray(ix[:n],dtype=int)].mean())
    return [float(v) for v in np.quantile(y,[.025,.975])]


def analyze(a, m, audit=True):
    old_trades, old_sessions=m.events(a)
    if old_sessions.empty or old_trades.empty:raise RuntimeError('R19 source returned no sessions')
    if old_sessions.ny_date.duplicated().any():raise RuntimeError('duplicate R19 session')
    old_orb=old_trades[old_trades.strategy=='ORB'].copy()
    five=five_minute_orb(a,old_sessions)
    if five.empty:raise RuntimeError('no 5min ORB')
    # Check exact R19 15m reproduction against frozen R19 result, not new optimized baseline.
    if audit:
        if not OLD_RESULT.is_file():raise RuntimeError('STOP: original R19_RESULTS.json unavailable for exact baseline audit')
        old=json.loads(OLD_RESULT.read_text())
        for r in old['results']:
            p=r['period'];me=old_orb[old_orb.period==p]
            if len(me)!=r['ORB']['trades']:raise RuntimeError('R19 count mismatch for '+p)
            if not np.isclose(me.net_base_bp.mean(),r['ORB']['mean_net_base_bp_per_trade'],atol=1e-9):
                raise RuntimeError('R19 net result mismatch for '+p)
            if len(old_sessions[old_sessions.period==p])!=r['sessions']:
                raise RuntimeError('R19 session count mismatch for '+p)
    old_orb['strategy']='ORB_15m'
    old_orb['range_bp']=old_orb['range15_bp']
    cols=['ny_date','period','strategy','range_bp','signal_idx','signal_utc','signal_ny',
          'entry_utc','direction','entry_price','stop_price','target_price','risk_bp',
          'holding_bars','exit_reason','gross_bp','net_base_bp','net_stress_bp']
    trades=pd.concat([five[cols],old_orb[cols]],ignore_index=True)
    days=old_sessions[['ny_date','period']].copy()
    results=[]
    for p in ('2024_SepDec','2025_JanDec'):
        day=days[days.period==p].copy().sort_values('ny_date')
        if day.empty:raise RuntimeError('period missing '+p)
        out={'period':p,'sessions':len(day)}
        for name,tag in [('5m','ORB_5m'),('15m','ORB_15m')]:
            x=trades[(trades.period==p)&(trades.strategy==tag)]
            if x.ny_date.duplicated().any():raise RuntimeError('duplicate trades')
            lk=x.set_index('ny_date')
            day[f'net_{name}']=day.ny_date.map(lk.net_base_bp).fillna(0).astype(float)
            day[f'stress_{name}']=day.ny_date.map(lk.net_stress_bp).fillna(0).astype(float)
            win=x.net_base_bp[x.net_base_bp>0].sum()
            loss=-x.net_base_bp[x.net_base_bp<0].sum()
            out[name]={'trades':len(x),'trade_rate':len(x)/len(day),
                       'mean_net_trade_bp':float(x.net_base_bp.mean()),
                       'mean_gross_trade_bp':float(x.gross_bp.mean()),
                       'mean_stress_trade_bp':float(x.net_stress_bp.mean()),
                       'net_base_bp_per_session':float(day[f'net_{name}'].mean()),
                       'net_stress_bp_per_session':float(day[f'stress_{name}'].mean()),
                       'ci95_net_session_descriptive':block_ci(day[f'net_{name}'],SEED+(0 if name=='5m' else 1)),
                       'profit_factor_net':float(win/loss) if loss>0 else None,
                       'target_fraction':float(x.exit_reason.isin(['target','target_gap']).mean()),
                       'stop_fraction':float(x.exit_reason.isin(['stop','stop_gap','ambiguous_stop_first']).mean()),
                       'time_fraction':float((x.exit_reason=='time').mean()),
                       'median_risk_bp':float(x.risk_bp.median()),
                       'median_opening_range_bp':float(x.range_bp.median()),
                       'median_holding_min':float(x.holding_bars.median()*5)}
        day['delta_5m_minus_15m']=day.net_5m-day.net_15m
        day['delta_stress']=day.stress_5m-day.stress_15m
        out['paired_5m_minus_15m_bp_per_session']=float(day.delta_5m_minus_15m.mean())
        out['paired_stress_diff_bp_per_session']=float(day.delta_stress.mean())
        out['ci95_paired_diff_descriptive']=block_ci(day.delta_5m_minus_15m,SEED+3)
        results.append(out)
    return results,trades,days


def synthetic(m):
    # Two different opening ranges: first 5m narrow, next two 5m wide.
    t=pd.date_range('2025-07-01 11:30',periods=132,freq='5min',tz='UTC')
    n=len(t);a={'t':t,'o':np.full(n,100.),'h':np.full(n,100.05),
         'l':np.full(n,99.95),'c':np.full(n,100.),'v':np.ones(n)}
    s=24 # 13:30 UTC = 09:30 NY
    assert t[s].tz_convert(m.NY).strftime('%H:%M')=='09:30'
    assert pd.Timestamp('2025-01-15 14:30',tz='UTC').tz_convert(m.NY).strftime('%H:%M')=='09:30'
    # 5m: bar s+1 breaks narrow 100.05 range; 15m: second bar s+1 inside wider 100.50
    a['h'][s+1]=100.50;a['l'][s+1]=99.95;a['c'][s+1]=100.40
    a['o'][s+2]=100.40
    a['h'][s+2]=100.45;a['l'][s+2]=99.95;a['c'][s+2]=100.30
    a['h'][s+3]=100.70;a['c'][s+3]=100.65
    a['o'][s+4]=100.65
    # constant prices outside synthetic scenario, triggers may stop immediately: valid under model.
    old_t,old_s=m.events(a)
    five=five_minute_orb(a,old_s)
    assert len(old_s)==1 and len(five)==1
    old=old_t[old_t.strategy=='ORB']
    assert len(old)==1
    assert int(five.signal_idx.iloc[0])==s+1
    assert int(old.signal_idx.iloc[0])==s+3
    assert int(five.entry_idx.iloc[0])==s+2
    assert int(old.entry_idx.iloc[0])==s+4
    assert five.range_bp.iloc[0]<old.range15_bp.iloc[0]
    # Future changes do not alter the fixed five-minute range or signal close.
    alt={k:(v.copy() if hasattr(v,'copy') else v) for k,v in a.items()}
    alt['h'][s+30:]=500.;alt['l'][s+30:]=1.;alt['c'][s+30:]=400.
    f2=five_minute_orb(alt,old_s)
    assert int(f2.signal_idx.iloc[0])==s+1
    # Execution behavior is inherited unchanged from frozen, pre-audited R19.
    assert m.synthetic()['e2e_both_strategies']
    return {'NY_DST':True,'5m_earlier_than_15m':True,'next_candle_entry':True,
            'same_session':True,'5m_not_using_future_bars':True,'frozen_execution':True}


def main():
    pa=argparse.ArgumentParser()
    g=pa.add_mutually_exclusive_group(required=True)
    g.add_argument('--preflight',action='store_true');g.add_argument('--run',action='store_true')
    args=pa.parse_args()
    m=reference();print('R20 SYNTHETIK:',synthetic(m),flush=True)
    a=m.load();print('R20 DATENGATE:',len(a['t']),'BTC-Kerzen,',len(a['hashes']),'Originaldateien',flush=True)
    if args.preflight:
        print('R20 PREFLIGHT ONLY: keine BTC-Ergebnismessung');return
    if OUT.exists():raise RuntimeError('STOP: Ergebnisordner existiert bereits')
    res,trades,days=analyze(a,m,audit=True)
    obj={'study':'R20 BTC NY 5-minute vs 15-minute ORB','status':'EXPLORATORY_NOT_BLINDTEST',
         'source_sha256':sha(Path(__file__)),'R19_frozen_sha256':REF_SHA,
         'original_hashes':a['hashes'],'R19_baseline_reproduced':True,
         'rules':{'timezone':'America/New_York','NY_weekdays':True,'market_holidays_excluded':False,
                  'opening_range_5m':'09:30-09:35 NY first complete 5m bar',
                  'opening_range_15m':'09:30-09:45 NY first three complete 5m bars',
                  'first_break':'first 5m close outside relevant opening range; latest 11:25 NY',
                  'entry':'next 5m open, stop at own range midpoint, target 1.5R',
                  'max_hold_minutes':120,'base_roundtrip_cost_bp':COST_BASE,'stress_roundtrip_cost_bp':COST_STRESS,
                  'benchmark':'previously frozen R19 15m ORB; no exit or cost tuning',
                  'nonsignal_session':'zero PnL, both variants same NY days'},
         'limitations':['2024/2025 already explored; not a blindtest',
                        'R18 NY window already selected on same data',
                        'Equal exit formula does not imply equal risk distribution: 5m opening range can narrow stop',
                        'No true funding or orderbook slippage; 14/24bp assumptions',
                        'Conservative 5m bar collision stop-first; no tick order',
                        'Two separate hypothetical strategies, not a simultaneously deployable portfolio',
                        'Uncalibrated block-bootstrap intervals; one posthoc 5m-vs-15m comparison',
                        'US equity holidays included by NY weekday rule'],
         'results':res}
    OUT.mkdir(parents=True,exist_ok=False)
    trades.to_csv(OUT/'R20_TRADES.csv',index=False)
    days.to_csv(OUT/'R20_DAILY_PAIRED.csv',index=False)
    (OUT/'R20_RESULTS.json').write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    lines=['# R20 BTC: 5 Minuten gegen 15 Minuten Opening Range', '',
           '**Explorativ. Kein unabhängiger Test, keine Live-Orders.**','',
           'Vergleich: gleiche NY-Handelstage, gleiche Kosten und Exit-Formel, identische 5m-Ausführungsengine.',
           'Der ursprüngliche R19-15m-ORB wurde auf den Originaldaten exakt reproduziert.', '',
           '| Zeitraum | Handelstage | 5m-Trades | Netto/Trade 5m (bp) | 15m-Trades | Netto/Trade 15m (bp) | Vorteil 5m pro Tag (bp) | 95%-Intervall Vorteil |',
           '|---|---:|---:|---:|---:|---:|---:|---|']
    for x in res:
        ci=x['ci95_paired_diff_descriptive']
        lines.append(f"| {x['period']} | {x['sessions']} | {x['5m']['trades']} | {x['5m']['mean_net_trade_bp']:.3f} | {x['15m']['trades']} | {x['15m']['mean_net_trade_bp']:.3f} | {x['paired_5m_minus_15m_bp_per_session']:+.3f} | [{ci[0]:+.3f}, {ci[1]:+.3f}] |")
    lines+=['','## Risikoprofil und Ausführung','',
            '| Zeitraum | OR | Median Stop-Risiko bp | Treffer Ziel % | Stop % | Stress-Netto pro Tag bp |',
            '|---|---|---:|---:|---:|---:|']
    for x in res:
        for v in ('5m','15m'):
            r=x[v]
            lines.append(f"| {x['period']} | {v} | {r['median_risk_bp']:.2f} | {100*r['target_fraction']:.1f} | {100*r['stop_fraction']:.1f} | {r['net_stress_bp_per_session']:+.3f} |")
    lines+=['','**Entscheidung:** Kein Kandidat ist allein wegen einer positiven Punktzahl als profitabel bestätigt.',
             'Falls 5m besser wirkt, bleibt das eine neue explorative Hypothese. Kein Parameter-Tuning oder erneute Nutzung als Blindtest.']
    (OUT/'R20_REPORT.md').write_text('\n'.join(lines)+'\n')
    for x in res:
        print(f"R20 {x['period']} Tage={x['sessions']} 5m n={x['5m']['trades']} netto={x['5m']['mean_net_trade_bp']:.3f}bp 15m n={x['15m']['trades']} netto={x['15m']['mean_net_trade_bp']:.3f}bp diff/Tag={x['paired_5m_minus_15m_bp_per_session']:+.3f}bp",flush=True)
    print('R20 EXPLORATIVE COMPLETE; R19 BASELINE MATCHED; KEINE ORDERS')
    print('BERICHT:',OUT/'R20_REPORT.md');print('JSON:',OUT/'R20_RESULTS.json')

if __name__=='__main__':main()
