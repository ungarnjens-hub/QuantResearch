#!/usr/bin/env python3
"""R13: isolated exploratory entry-path audit, no orders or exit tuning.
Requires frozen R12_3_Strategien_BTC_Explorativ.py in same directory.
Usage: python R13_BTC_Entry_Excursions_OneRun.py --preflight | --run
"""
import argparse, hashlib, importlib.util, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

HOME=Path.home()
BASE=Path(__file__).resolve().parent
R12=BASE/'R12_3_Strategien_BTC_Explorativ.py'
DEST=HOME/'QuantResearch/R13_BTC_EntryPaths/Sep2024_Dec2025_v1'
HORIZONS=(3,6,12,24) # 15, 30, 60, 120 minutes
COST_BP=14.0 # illustrative R12 roundtrip assumption, NOT measured settlement
SEED=20261115
WARMUP=300

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def load_r12():
    if not R12.is_file():raise RuntimeError('Missing frozen R12 source: '+str(R12))
    expected='7c434924f85cdd94fb09438dbf033cb797a946bc93ff8f3bdb82a9850839609d'
    if sha(R12)!=expected:raise RuntimeError('R12 source SHA256 mismatch: original R12 must remain unchanged')
    # Import reference entry rules; never call R12.main or edit its inputs.
    spec=importlib.util.spec_from_file_location('r12_readonly',R12)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    if tuple(mod.STRATEGIES)!=('pullback','breakout','reversion') or mod.WARMUP!=300:
        raise RuntimeError('Unexpected R12 strategy contract')
    return mod

def inspect_path(o,h,l,entry_idx,side,bars):
    """Absolute OHLC excursions after next-open entry; NOT executable TP/SL fills.
    Includes entry bar; close at open of (entry_idx+bars) for fixed-horizon return.
    """
    e=float(o[entry_idx]); end=entry_idx+bars
    hp=float(np.max(h[entry_idx:end])); lp=float(np.min(l[entry_idx:end]))
    mfe=(hp/e-1)*10000 if side==1 else (1-lp/e)*10000
    mae=(1-lp/e)*10000 if side==1 else (hp/e-1)*10000
    ret=side*(float(o[end])/e-1)*10000
    return float(mfe),float(mae),float(ret)

def regime(c, j):
    # All inputs <= confirmed close j; 1h historical direction aligned to signal side later.
    # 1h movement and reference quiet threshold estimated from trailing 7d absolute 1h moves.
    return float(c[j]/c[j-12]-1)

def _daily_block_ci(dates,diffs,all_dates,draws=800):
    # Stratified by UTC calendar-day; zero-trade days absent in paired event mean; description only.
    # Bootstrap paired event-control daily sums/counts with circular 7-day blocks.
    ix=np.asarray((pd.DatetimeIndex(dates).normalize()-all_dates[0])//pd.Timedelta(days=1),dtype=int)
    sums=np.bincount(ix,weights=diffs,minlength=len(all_dates))
    cnt=np.bincount(ix,minlength=len(all_dates))
    if cnt.sum()<40 or len(all_dates)<28:return None
    rng=np.random.default_rng(SEED)
    n=len(all_dates);blocks=int(math.ceil(n/7)); out=[]
    for _ in range(draws):
        starts=rng.integers(0,n,size=blocks)
        ids=(starts[:,None]+np.arange(7)[None,:])%n
        ids=ids.ravel()[:n];den=cnt[ids].sum()
        if den:out.append(sums[ids].sum()/den)
    if len(out)<draws:return None
    return [float(x) for x in np.percentile(out,[2.5,97.5])]

def analyze(a,signals):
    t,o,h,l,c=a['t'],a['o'],a['h'],a['l'],a['c']
    all_rows=[];results={}
    for label,start,end in [('2024_SepDec','2024-09-01','2025-01-01'),('2025_JanDec','2025-01-01','2026-01-01')]:
        lo=int(t.searchsorted(pd.Timestamp(start,tz='UTC')))
        hi=int(t.searchsorted(pd.Timestamp(end,tz='UTC')))
        # Everyone gets a 120m follow-up; exclude any path that crosses the year boundary.
        js=np.arange(lo+WARMUP,hi-1-max(HORIZONS),dtype=int)
        if len(js)==0:raise RuntimeError('Insufficient period')
        # Never gate on existing R12 positions. Every qualified signal counts.
        # Controls are random qualifying bars on same UTC day, same clock hour if possible,
        # excluding same-strategy signals. No post-entry price used to choose a control.
        day=((js-lo)//288).astype(int)
        hour=(js%288)//12
        rperiod={}
        for strategy in ('pullback','breakout','reversion'):
            signal=signals[strategy]
            active=js[signal[js]!=0]
            non=js[signal[js]==0]
            if len(active)<40:raise RuntimeError('Too few signals '+strategy)
            groups={}
            for j in non:
                k=((j-lo)//288,int((j%288)//12))
                groups.setdefault(k,[]).append(int(j))
            byday={}
            for j in non:byday.setdefault(int((j-lo)//288),[]).append(int(j))
            rng=np.random.default_rng(SEED+{'pullback':1,'breakout':2,'reversion':3}[strategy])
            counters={'same_day_hour':0,'same_day_fallback':0,'unmatched':0}
            for j in active:
                j=int(j);side=int(signal[j]); day_id=int((j-lo)//288)
                pool=groups.get((day_id,int((j%288)//12)),[])
                if pool:counters['same_day_hour']+=1
                else:
                    pool=byday.get(day_id,[])
                    if pool:counters['same_day_fallback']+=1
                if not pool:
                    counters['unmatched']+=1;continue
                k=int(pool[int(rng.integers(len(pool)))])
                # Daily matched control uses same side. It is a descriptive benchmark,
                # not independent of other events / not necessarily tradeable simultaneously.
                assert k>=lo+WARMUP and k+1+max(HORIZONS)<hi
                row={'period':label,'strategy':strategy,'signal_idx':j,'control_idx':k,
                     'signal_time_utc':str(t[j]),'entry_time_utc':str(t[j+1]),
                     'control_time_utc':str(t[k]),'side':side,'trend_60m_bp':regime(c,j)*10000,
                     'aligned_60m':bool(side*regime(c,j)>0)}
                for horizon in HORIZONS:
                    mfe,mae,ret=inspect_path(o,h,l,j+1,side,horizon)
                    cmfe,cmae,cret=inspect_path(o,h,l,k+1,side,horizon)
                    suffix=str(horizon*5)
                    row.update({f'mfe_{suffix}_bp':mfe,f'mae_{suffix}_bp':mae,
                                f'gross_{suffix}_bp':ret,f'control_gross_{suffix}_bp':cret,
                                f'diff_{suffix}_bp':ret-cret,
                                f'net_if_fixed_exit_{suffix}_bp':ret-COST_BP})
                all_rows.append(row)
            sub=[x for x in all_rows if x['period']==label and x['strategy']==strategy]
            z={'total_signals':int(len(active)),'matched':len(sub),'matched_control':counters,
               'signals_per_utc_day':len(active)/((hi-lo)/288),'long_signals':int((signal[active]>0).sum()),
               'short_signals':int((signal[active]<0).sum()),'horizons':{}}
            for horizon in HORIZONS:
                suf=str(horizon*5)
                v=np.array([x[f'gross_{suf}_bp'] for x in sub])
                ctr=np.array([x[f'control_gross_{suf}_bp'] for x in sub])
                mfe=np.array([x[f'mfe_{suf}_bp'] for x in sub])
                mae=np.array([x[f'mae_{suf}_bp'] for x in sub])
                ds=pd.to_datetime([x['signal_time_utc'] for x in sub],utc=True)
                days=pd.date_range(t[lo].floor('D'),t[hi-1].floor('D'),freq='D',tz='UTC')
                z['horizons'][suf]={'n':len(v),'mean_gross_bp':float(v.mean()),
                    'mean_net_fixed_exit_cost14bp':float(v.mean()-COST_BP),
                    'positive_fixed_exit_fraction':float(np.mean(v>COST_BP)),
                    'mean_control_bp':float(ctr.mean()),'mean_signal_minus_control_bp':float((v-ctr).mean()),
                    'descriptive_7day_block_ci_diff_bp':_daily_block_ci(ds,v-ctr,days),
                    'median_mfe_bp':float(np.median(mfe)),'median_mae_bp':float(np.median(mae)),
                    'p75_mfe_bp':float(np.quantile(mfe,.75)),'p75_mae_bp':float(np.quantile(mae,.75)),
                    'mfe_exceeds_cost14bp_fraction':float(np.mean(mfe>=COST_BP)),
                    'mae_exceeds_14bp_fraction':float(np.mean(mae>=COST_BP)),
                    'aligned_60m':{},'opposed_60m':{}}
                for grp,label2 in [(True,'aligned_60m'),(False,'opposed_60m')]:
                    mask=np.array([x['aligned_60m']==grp for x in sub]); vv=v[mask]
                    z['horizons'][suf][label2]={'n':int(mask.sum()),'mean_gross_bp':float(vv.mean()) if len(vv) else None}
            rperiod[strategy]=z
        results[label]=rperiod
    return all_rows,results

def synthetic():
    o=np.full(100,100.0);h=np.full(100,100.2);l=np.full(100,99.8)
    o[20]=100;h[20:23]=101;l[20:23]=99;o[23]=100.5
    a=inspect_path(o,h,l,20,1,3)
    b=inspect_path(o,h,l,20,-1,3)
    # No future OHLC inside first 3 bars changes path result.
    h2=h.copy();l2=l.copy();o2=o.copy();h2[24:]=999;l2[24:]=1;o2[24:]=1
    c=inspect_path(o2,h2,l2,20,1,3)
    return {'directional_excursion':np.allclose(a[:2],[100,100]) and np.allclose(b[:2],[100,100]),
            'future_prices_do_not_change_past_path':a==c,
            'fixed_exit_uses_open_after_full_horizon':np.isclose(a[2],50),
            'funding_cost_not_claimed_actual':COST_BP==14}

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--preflight',action='store_true');g.add_argument('--run',action='store_true');args=p.parse_args()
    checks=synthetic();print('R13 SYNTHETIK:',checks)
    if not all(checks.values()):raise RuntimeError('Synthetic failed')
    r12=load_r12();a=r12.load_and_audit()
    if len(a['t'])!=140256 or len(a['hashes'])!=16:raise RuntimeError('Unexpected source size')
    print('R13 DATENGATE: PASS, BTC',len(a['t']),'closed bars',len(a['hashes']),'files')
    if args.preflight:
        print('R13 PREFLIGHT ONLY, no market signals or excursions measured');return
    if DEST.exists():raise RuntimeError('Output exists, never overwrite: '+str(DEST))
    sig,_=r12.features(a)
    rows,results=analyze(a,sig)
    obj={'study':'R13 BTC entry paths, fixed horizons, matched controls',
         'status':'EXPLORATORY_NOT_CONFIRMATORY','input_sha256':a['hashes'],
         'r12_code_sha256':sha(R12),'r13_code_sha256':sha(Path(__file__).resolve()),
         'parameters':{'horizons_minutes':[15,30,60,120],'warmup_bars_each_period':WARMUP,
             'signal': 'all signals independent of R12 open positions','entry':'next 5m open',
             'control':'nonsignal same UTC day/hour when available; same UTC day fallback; sampled with replacement',
             'cost_reference_bp':'R12 assumed 14bp, not real funding or validated executable net',
             'regime':'60m close-to-close sign at signal close; descriptive, no selected regime trading',
             'bootstrap':'descriptive circular paired daily 7-day block, 800, no calibrated multiplicity'},
         'results':results,'limitations':['MFE and MAE high/low intrabar path order unknown',
             'Time-joined control can be reused; descriptive not independent evidence',
             'Fixed-horizon open exits are diagnostic, not full trade execution/backtest',
             '2024/2025 BTC history extensively explored, not blindtest',
             'No optimized thresholds, risk-reward, or new trade strategy',
             'R12 entry rules reused as-is, no evaluation of all possible BTC opportunities']}
    DEST.mkdir(parents=True,exist_ok=False)
    (DEST/'R13_RESULTS.json').write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    pd.DataFrame(rows).to_csv(DEST/'R13_ENTRY_PATHS.csv',index=False)
    lines=['# R13 BTC Einstiegspfad-Analyse','',
        '**Explorativ. Keine Bestätigung, keine automatische Handelsregel, keine Live-Orders.**','',
        'Signalrekonstruktion aus unverändertem R12-Code; alle gültigen Signale, auch während R12-Positionen.','',
        'Renditen: Signal an Close j, Einstieg Open j+1, hypothetischer Exit Open j+1+h. MFE/MAE aus 5m High/Low, Reihenfolge innerhalb einer Kerze nicht bekannt.','',
        '14 bp sind nur ein angenommener Kostenansatz aus R12. Die feste Exit-Rendite nach 14 bp ist **kein** vollständiger Netto-Backtest.','',
        '| Periode | Strategie | Signale | Signale/Tag | Horizont | Ø Brutto bp | Ø minus 14bp | Ø Kontrolle bp | Δ vs Kontrolle bp | 95% deskriptives Blockintervall Δ | Median MFE / MAE bp |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|']
    for period,rr in results.items():
        for strategy,z in rr.items():
            for horizon,x in z['horizons'].items():
                ci=x['descriptive_7day_block_ci_diff_bp'];cis='–' if ci is None else f'[{ci[0]:+.2f}; {ci[1]:+.2f}]'
                lines.append(f'| {period} | {strategy} | {z["total_signals"]} | {z["signals_per_utc_day"]:.1f} | {horizon}m | {x["mean_gross_bp"]:+.2f} | {x["mean_net_fixed_exit_cost14bp"]:+.2f} | {x["mean_control_bp"]:+.2f} | {x["mean_signal_minus_control_bp"]:+.2f} | {cis} | {x["median_mfe_bp"]:.1f} / {x["median_mae_bp"]:.1f} |')
    lines+=['','## Interpretation','MFE ist nur ein historisch innerhalb des Beobachtungsfensters erreichtes Hoch/Tief; nicht automatisch ein realisierbarer Gewinn. MAE analog. Ohne Tick-Sequenz keine Aussagen zur Reihenfolge oder zu optimalen Stops.','Kontrollen werden zufällig im selben UTC-Tag und möglichst derselben Stunde ohne Signal gewählt; bei Bedarf Tages-Fallback. Kein mehrfachtestsicherer Nachweis.','Konformität zur vorherigen 60min-Bewegung wird nur beschreibend ausgewiesen; eine nachträglich profitable Untergruppe darf nicht als bestätigte Strategie gelten.']
    (DEST/'R13_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('R13 EXPLORATORY COMPLETE, NO ORDERS, NO NEW R12 BACKTEST')
    for period,rr in results.items():
        for s,z in rr.items():
            x=z['horizons']['60']
            print(f'{period} {s:9s} signals={z["total_signals"]:5d} per_day={z["signals_per_utc_day"]:.1f} 60m_gross={x["mean_gross_bp"]:+.2f}bp 60m_vs_control={x["mean_signal_minus_control_bp"]:+.2f}bp 60m_MFE/MAE_median={x["median_mfe_bp"]:.1f}/{x["median_mae_bp"]:.1f}bp')
    print('REPORT:',DEST/'R13_REPORT.md');print('RESULT:',DEST/'R13_RESULTS.json');print('ENTRY PATHS:',DEST/'R13_ENTRY_PATHS.csv')

if __name__=='__main__':
    try:main()
    except Exception as e:print('R13 FAIL CLOSED:',type(e).__name__,e);sys.exit(4)
