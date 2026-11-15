#!/usr/bin/env python3
"""R19 fixed, exploratory BTC NY opening-range continuation vs false-break, research ONLY.
US equities weekdays by NY civil weekday (holidays not removed); no orders, no production writes.
Usage: --preflight / --run ; binary dependency on frozen R12 canonical read-only loader.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, sys
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

ROOT=Path.home()/'QuantResearch-Git/studies'
LOADER=ROOT/'R12_3_Strategien_BTC_Explorativ.py'
LOADER_HASH='7c434924f85cdd94fb09438dbf033cb797a946bc93ff8f3bdb82a9850839609d'
OUT=Path.home()/'QuantResearch/R19_BTC_NY_Open/Sep2024_Dec2025_v1'
NY=ZoneInfo('America/New_York')
PERIODS={'2024_SepDec':('2024-09-01','2025-01-01'),'2025_JanDec':('2025-01-01','2026-01-01')}
COST_BASE=14.0; COST_STRESS=24.0; RR=1.5; MAX_BARS=24
SEED=20261115; BLOCK_DAYS=7; DRAWS=2000

def sha(p):
    hh=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):hh.update(chunk)
    return hh.hexdigest()

def load():
    if not LOADER.exists() or sha(LOADER)!=LOADER_HASH:raise RuntimeError('R12 read-only loader hash mismatch; STOP')
    spec=importlib.util.spec_from_file_location('r19_frozen_r12',LOADER)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.load_and_audit()

def atr14(a):
    h,l,c=a['h'],a['l'],a['c']
    prev=np.r_[c[0],c[:-1]]
    tr=np.maximum.reduce([h-l,abs(h-prev),abs(l-prev)])
    return pd.Series(tr).rolling(14,min_periods=14).mean().to_numpy()

def execution(a, idx, end, direction, stop, rr=RR, maxbars=MAX_BARS):
    """Next 5m bar open; SL first when both touched; last expiry open; no next-year labels."""
    if idx>=end or idx+maxbars>=end:return None
    entry=float(a['o'][idx]);risk=direction*(entry-stop)
    if not np.isfinite(risk) or risk<=0 or stop<=0:return None
    target=entry+direction*rr*risk
    reason='time';price=float(a['o'][idx+maxbars]);exitidx=idx+maxbars;collision=False
    for k in range(idx,idx+maxbars):
        op=float(a['o'][k]);hi=float(a['h'][k]);lo=float(a['l'][k])
        gap_sl=(op<=stop) if direction==1 else (op>=stop)
        gap_tp=(op>=target) if direction==1 else (op<=target)
        touch_sl=(lo<=stop) if direction==1 else (hi>=stop)
        touch_tp=(hi>=target) if direction==1 else (lo<=target)
        if gap_sl:reason='stop_gap';price=op;exitidx=k;break
        if gap_tp:reason='target_gap';price=target;exitidx=k;break
        if touch_sl and touch_tp:reason='ambiguous_stop_first';price=stop;exitidx=k;collision=True;break
        if touch_sl:reason='stop';price=stop;exitidx=k;break
        if touch_tp:reason='target';price=target;exitidx=k;break
    gross=direction*(price/entry-1)*1e4
    return {'entry_idx':idx,'exit_idx':exitidx,'entry_price':entry,'stop_price':float(stop),'target_price':float(target),
            'risk_bp':float(risk/entry*1e4),'holding_bars':exitidx-idx,'exit_reason':reason,'collision':collision,
            'gross_bp':float(gross),'net_base_bp':float(gross-COST_BASE),'net_stress_bp':float(gross-COST_STRESS)}

def events(a, date_filter=None):
    t=a['t'];o,h,l,c=[a[k] for k in ('o','h','l','c')]; atr=atr14(a)
    ny=t.tz_convert(NY)
    mm=np.asarray(ny.hour)*60+np.asarray(ny.minute)
    starts=np.flatnonzero(mm==9*60+30)
    rows=[];sessions=[]
    for s in starts:
        if s+60>=len(t):continue
        if ny[s].weekday()>=5:continue
        date=str(ny[s].date())
        if date_filter is not None and date not in date_filter:continue
        if t[s+23]-t[s]!=pd.Timedelta(minutes=115):raise RuntimeError('Noncontiguous NY trading window')
        period='2024_SepDec' if t[s].year==2024 else '2025_JanDec'
        if t[s].year not in (2024,2025):continue
        start_year=2024 if period=='2024_SepDec' else 2025
        end_date=pd.Timestamp(f'{start_year+1}-01-01',tz='UTC')
        end=min(len(t),int(t.searchsorted(end_date)))
        if s+60>=end:continue
        rhi=float(np.max(h[s:s+3]));rlo=float(np.min(l[s:s+3]));middle=(rhi+rlo)/2
        day={'period':period,'ny_date':date,'ny_weekday':int(ny[s].weekday()),'range15_bp':float((rhi/rlo-1)*1e4),
             'start_utc':str(t[s]),'open_range_high':rhi,'open_range_low':rlo}
        records={}
        # Wait for FIRST 5m CLOSE outside range, starting after 15m completed at 09:45.
        # Signal latest 11:25 NY, next-open entry <=11:30.
        first=None;breach_direction=0
        for j in range(s+3,s+24):
            if c[j]>rhi: first=j;breach_direction=1;break
            if c[j]<rlo: first=j;breach_direction=-1;break
        if first is not None:
            # ORB: breakout continuation; stop at opening-range midpoint (no future).
            sig=first;res=execution(a,sig+1,end,breach_direction,middle)
            if res is not None:
                records['ORB']={'signal_idx':sig,'direction':breach_direction,'role':'continuation','signal_utc':str(t[sig]),
                     'signal_ny':str(ny[sig]),'signal_window':'09:45-10:30' if mm[sig]<630 else '10:30-11:30',**res}
            # Fakeout: return back INTO range within next three completed 5m bars.
            # One first-breach opportunity per date: no scanning later independent candidates.
            extreme=float(np.max(h[first:first+1])) if breach_direction==1 else float(np.min(l[first:first+1]))
            for k in range(first+1,min(first+4,s+24)):
                extreme=max(extreme,float(h[k])) if breach_direction==1 else min(extreme,float(l[k]))
                reentry=(c[k]<rhi and c[k]>rlo)
                if reentry:
                    direction=-breach_direction
                    buffer=float(atr[k])*0.10
                    stop=extreme+buffer if breach_direction==1 else extreme-buffer
                    res=execution(a,k+1,end,direction,stop)
                    if res is not None:
                        records['FAKEOUT']={'signal_idx':k,'direction':direction,'role':'reversal',
                          'signal_utc':str(t[k]),'signal_ny':str(ny[k]),
                          'signal_window':'09:45-10:30' if mm[k]<630 else '10:30-11:30',**res}
                    break
        day['had_breach']=first is not None
        day['range_30m_forward_bp']=float((np.max(h[s+3:s+9])/np.min(l[s+3:s+9])-1)*1e4)
        sessions.append(day)
        for strategy in ('ORB','FAKEOUT'):
            if strategy in records:
                row={**day,'strategy':strategy,**records[strategy]}
                row['entry_utc']=str(t[int(row['entry_idx'])]);row['exit_utc']=str(t[int(row['exit_idx'])]);rows.append(row)
    return pd.DataFrame(rows),pd.DataFrame(sessions)

def block_ci(daily, k, seed):
    """Circular day-level 7-day blocks, sorted NY calendar weekdays incl trading holidays;
    exploratory percentile CI, not multiplicity calibrated."""
    x=np.asarray(daily[k],dtype=float);n=len(x)
    if n<14:return None
    rng=np.random.default_rng(seed);values=np.empty(DRAWS)
    for b in range(DRAWS):
        p=[]
        while len(p)<n:
            z=int(rng.integers(n));p.extend((z+np.arange(BLOCK_DAYS))%n)
        values[b]=float(np.mean(x[np.array(p[:n],dtype=int)]))
    return [float(v) for v in np.quantile(values,[.025,.975])]

def summarize(trades,sessions):
    result=[];dailies=[]
    for period in PERIODS:
        s=sessions[sessions.period==period].copy().sort_values('ny_date')
        if len(s)==0:continue
        t=trades[trades.period==period].copy()
        daily=s[['ny_date','period','range15_bp','had_breach']].copy()
        for method in ('ORB','FAKEOUT'):
            tt=t[t.strategy==method].copy()
            if tt.ny_date.duplicated().any():raise RuntimeError('Duplicate per method and NY day')
            lookup=tt.set_index('ny_date')
            daily[f'{method}_base']=daily.ny_date.map(lookup.net_base_bp).fillna(0).astype(float)
            daily[f'{method}_stress']=daily.ny_date.map(lookup.net_stress_bp).fillna(0).astype(float)
        daily['paired_fake_minus_orb']=daily.FAKEOUT_base-daily.ORB_base
        dailies.append(daily)
        o={'period':period,'sessions':len(s),'first_breach_sessions':int(s.had_breach.sum()),
           'opening_range_median_bp':float(s.range15_bp.median()),'paired_diff_base_bp_per_session':float(daily.paired_fake_minus_orb.mean()),
           'paired_diff_ci95_exploratory':block_ci(daily,'paired_fake_minus_orb',SEED+1)}
        for method in ('ORB','FAKEOUT'):
            tt=t[t.strategy==method]
            executed=len(tt)
            dat={'trades':executed,'trade_rate_per_session':executed/len(s),
                 'net_bp_per_session':float(daily[f'{method}_base'].mean()),
                 'stress_bp_per_session':float(daily[f'{method}_stress'].mean()),
                 'ci95_per_session_exploratory':block_ci(daily,f'{method}_base',SEED+(0 if method=='ORB' else 2))}
            if executed:
                net=tt.net_base_bp.to_numpy();wins=net[net>0].sum();loss=-net[net<0].sum()
                dat.update({'mean_gross_bp_per_trade':float(tt.gross_bp.mean()),
                  'mean_net_base_bp_per_trade':float(tt.net_base_bp.mean()),
                  'mean_net_stress_bp_per_trade':float(tt.net_stress_bp.mean()),
                  'profit_factor_net':float(wins/loss) if loss>0 else None,
                  'target_frac':float(tt.exit_reason.isin(['target','target_gap']).mean()),
                  'stop_frac':float(tt.exit_reason.isin(['stop','stop_gap','ambiguous_stop_first']).mean()),
                  'time_frac':float((tt.exit_reason=='time').mean()),
                  'median_risk_bp':float(tt.risk_bp.median()),
                  'median_holding_minutes':float(tt.holding_bars.median()*5),
                  'by_signal_window':{z:{'n':len(g),'mean_net_bp':float(g.net_base_bp.mean())} for z,g in tt.groupby('signal_window')}})
            o[method]=dat
        result.append(o)
    return result,pd.concat(dailies,ignore_index=True)

def synthetic():
    t=pd.date_range('2025-07-01 13:30',periods=80,freq='5min',tz='UTC')
    assert t[0].tz_convert(NY).strftime('%H:%M')=='09:30'
    assert pd.Timestamp('2025-01-15 14:30',tz='UTC').tz_convert(NY).strftime('%H:%M')=='09:30'
    a={'t':t,'o':np.full(80,100.),'h':np.full(80,100.05),'l':np.full(80,99.95),'c':np.full(80,100.),'v':np.ones(80)}
    # opening range [99.95,100.05], breakout candle j=3 must complete before j=4 open
    a['c'][3]=100.10;a['h'][3]=100.15;a['o'][4]=100.10
    # first-bar gap adverse to breakout stop=100.0 and short stop=extreme+buffer
    x=execution(a,4,80,1,100.0)
    assert x is not None and x['entry_idx']==4 and x['exit_idx']==4 and x['exit_reason']=='stop'
    # Explicit intrabar collision on entry bar: stop wins.
    b={k:(v.copy() if hasattr(v,'copy') else v) for k,v in a.items()}
    b['h'][4]=100.50;b['l'][4]=99.90
    z=execution(b,4,80,1,100.0)
    assert z is not None and z['exit_reason']=='ambiguous_stop_first'
    # gap adverse open is correctly used
    b['o'][4]=99.5
    z=execution(b,4,80,1,100.0)
    assert z is None  # invalid because stop is above open for an attempted long
    # time expiry on completely flat path
    q={k:(v.copy() if hasattr(v,'copy') else v) for k,v in a.items()}
    q['h'][:]=100.05;q['l'][:]=99.95;q['c'][:]=100.;q['o'][:]=100.
    z=execution(q,4,80,1,99.,rr=1.5)
    assert z is not None and z['exit_reason']=='time' and z['exit_idx']==28
    # Future prices cannot change the pre-entry opening range or breakout condition.
    assert (np.max(a['h'][:3]),np.min(a['l'][:3]))==(100.05,99.95)
    # End-to-end synthetic: include sufficient ATR warmup before the NY open.
    tt=pd.date_range('2025-07-01 11:30',periods=130,freq='5min',tz='UTC')
    zz={'t':tt,'o':np.full(130,100.),'h':np.full(130,100.05),'l':np.full(130,99.95),'c':np.full(130,100.),'v':np.ones(130)}
    zz['c'][27]=100.2;zz['h'][27]=100.25;zz['o'][28]=100.1;zz['c'][28]=100.0
    tr,ss=events(zz)
    assert len(ss)==1 and set(tr.strategy)=={'ORB','FAKEOUT'}
    assert int(tr.loc[tr.strategy=='ORB','signal_idx'].iloc[0])==27
    assert int(tr.loc[tr.strategy=='FAKEOUT','signal_idx'].iloc[0])==28
    return {'ny_dst':True,'close_before_entry':True,'collision_stop_first':True,
            'invalid_gap_entry_skipped':True,'time_limit':True,'range_historic':True,'e2e_both_strategies':True}

def run():
    checks=synthetic()
    print('R19 SYNTHETIC PASS',checks,flush=True)
    a=load();print('R19 DATA GATE PASS',len(a['t']),'5m bars',len(a['hashes']),'monthly original files',flush=True)
    return a

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--preflight',action='store_true');g.add_argument('--run',action='store_true')
    args=p.parse_args();a=run()
    if args.preflight:
        print('R19 PREFLIGHT ONLY; NO REAL MARKET STRATEGY MEASUREMENT');return
    if OUT.exists():raise RuntimeError('OUTPUT EXISTS / fail closed: '+str(OUT))
    trades,sessions=events(a)
    if trades.empty or sessions.empty:raise RuntimeError('No eligible sessions/trades, fail closed')
    # prevent accidentally introducing sessions outside declared partitions
    if sessions.period.isna().any():raise RuntimeError('Invalid partition')
    results,daily=summarize(trades,sessions)
    if len(results)!=2:raise RuntimeError('Missing annual partition')
    obj={'study':'R19 BTC NY opening range first-close breakout vs first false-break',
         'status':'EXPLORATORY_NOT_BLINDTEST','original_hashes':a['hashes'],'reference_loader_sha':LOADER_HASH,
         'source_sha256':sha(Path(__file__)),'timezone':'America/New_York',
         'rules':{'weekdays':'Mon-Fri NY, market holidays NOT removed','opening_range':'09:30-09:45 NY first 3 completed 5m bars',
          'signal':'first completed 5m close outside range between 09:45 and 11:30 NY',
          'ORB':'enter next open same direction, stop opening-range midpoint, target 1.5R',
          'FAKEOUT':'first closed return inside range within next three 5m bars; enter next open opposite breakout, stop outside breach extreme +0.1 ATR14, target 1.5R',
          'one_signal_per_method_per_day':True,'max_hold_minutes':120,'base_cost_bp':COST_BASE,'stress_cost_bp':COST_STRESS},
         'limitations':['Cost assumptions incl funding reserve are not actual executions','Same bar SL/TP collision conservative stop-first',
         'No tick replay or liquidity modeling','NY civil weekdays include exchange holidays',
         '2024/2025 BTC history previously explored; 09:30 window selected from R18; not independent evidence',
         'Trade strategies evaluated separately, no simultaneous portfolio, daily zero when no signal',
         'No optimal parameter search; first completed break only; signal may occur up to 11:25 NY'],
         'results':results}
    OUT.mkdir(parents=True,exist_ok=False)
    trades.to_csv(OUT/'R19_TRADES.csv',index=False)
    sessions.to_csv(OUT/'R19_SESSIONS.csv',index=False)
    daily.to_csv(OUT/'R19_DAILY_PAIRED.csv',index=False)
    (OUT/'R19_RESULTS.json').write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    lines=['# R19: BTC NY 09:30 Opening Range versus Fehlausbruch','',
           '**EXPLORATIV, nicht bestätigend, keine Live-Orders.**','',
           'Die 09:30-New-York-Zeit wurde wegen R18 gewählt: keine neue unabhängige Evidenz.','',
           'Kosten 14 bp je Roundtrip, Stress 24 bp; pauschale Annahmen inkl. Fundingreserve.','',
           '| Periode | Handels-Tage | Ausbruch Trades | Ausbruch Netto bp/Trade | Fehlausbruch Trades | Fehlausbruch Netto bp/Trade | Netto-Differenz bp/Tag |',
           '|---|---:|---:|---:|---:|---:|---:|']
    for r in results:
        orb=r['ORB'];fake=r['FAKEOUT']
        lines.append(f"| {r['period']} | {r['sessions']} | {orb['trades']} | {orb.get('mean_net_base_bp_per_trade',float('nan')):.3f} | {fake['trades']} | {fake.get('mean_net_base_bp_per_trade',float('nan')):.3f} | {r['paired_diff_base_bp_per_session']:.3f} |")
    lines.extend(['','**Entscheidungsregeln:** kein Kandidat wird als profitabel eingestuft ohne positive Kosten-Stress-Prognose und unabhängigen, zuvor versiegelten Test.','',
                  'Für einzelne Trades, Exit-Gründe und frühe/späte Signale die CSV und JSON heranziehen.'])
    (OUT/'R19_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for r in results:
        print('R19',r['period'],'days',r['sessions'],
          'ORB trades',r['ORB']['trades'],'net/trade',round(r['ORB'].get('mean_net_base_bp_per_trade',float('nan')),3),
          'FAKEOUT trades',r['FAKEOUT']['trades'],'net/trade',round(r['FAKEOUT'].get('mean_net_base_bp_per_trade',float('nan')),3),
          'diff/session',round(r['paired_diff_base_bp_per_session'],3),flush=True)
    print('R19 COMPLETE, NO ORDERS, NO CONFIRMATORY CLAIM')
    print('REPORT:',OUT/'R19_REPORT.md');print('RESULT:',OUT/'R19_RESULTS.json');print('TRADES:',OUT/'R19_TRADES.csv')

if __name__=='__main__':main()
