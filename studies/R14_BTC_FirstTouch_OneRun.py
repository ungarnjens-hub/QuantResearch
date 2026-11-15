#!/usr/bin/env python3
"""R14 / one-pass exploratory FIRST-TOUCH audit of frozen R13 BTC signals.
Only reads canonical BTC parquet, frozen R13 files and R12 source. No orders.
Run from ~/QuantResearch-Git/studies/, where R12 reference resides.
"""
import hashlib, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

HOME=Path.home()
SOURCE=Path(__file__).resolve().parent
R12=SOURCE/'R12_3_Strategien_BTC_Explorativ.py'
INPUT=HOME/'QuantResearch/R13_BTC_EntryPaths/Sep2024_Dec2025_v1'
OUTPUT=HOME/'QuantResearch/R14_BTC_FirstTouch/Sep2024_Dec2025_v1'
STOP_BP=14.0
TARGET_BP=28.0
HORIZON=12 # 60 minutes, open of 13th bar if no first touch
COST_BP=14.0 # hypothetical roundtrip fees/slippage/funding reserve
STRESS_COST_BP=24.0
NOTIONAL=100.0
R12_HASH='7c434924f85cdd94fb09438dbf033cb797a946bc93ff8f3bdb82a9850839609d'

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def touch(o,h,l,entry,side,stop_bp=STOP_BP,target_bp=TARGET_BP,bars=HORIZON):
    """First touch in OHLC 5m; stop first on within-bar ambiguity.
    Adverse opening gap exits at the actual opening price, not a favorable stop.
    No fictitious same-bar re-entry. Peak time is first max favorable bar,
    explicitly NOT a tradeable maximum or tick time.
    """
    price=float(o[entry]); last=entry+bars
    if last>=len(o):raise ValueError('crosses data boundary')
    high=np.asarray(h[entry:last]);low=np.asarray(l[entry:last]);opens=np.asarray(o[entry:last])
    favourable=high/price-1 if side==1 else 1-low/price
    adverse=1-low/price if side==1 else high/price-1
    peak_idx=entry+int(np.argmax(favourable))
    max_f=float(np.max(favourable)*10000)
    max_a=float(np.max(adverse)*10000)
    sl=price*(1-side*stop_bp/10000)
    tp=price*(1+side*target_bp/10000)
    both=False;ex=None
    for i in range(entry,last):
        op,hi,lo=float(o[i]),float(h[i]),float(l[i])
        if side==1:
            stop_gap=op<=sl;target_gap=op>=tp
            stop_hit=lo<=sl;target_hit=hi>=tp
        else:
            stop_gap=op>=sl;target_gap=op<=tp
            stop_hit=hi>=sl;target_hit=lo<=tp
        if stop_gap:
            ex=(i,op,'stop_gap');break
        if target_gap:
            ex=(i,op,'target_gap');break
        if stop_hit and target_hit:
            both=True;ex=(i,sl,'ambiguous_stop_first');break
        if stop_hit:ex=(i,sl,'stop');break
        if target_hit:ex=(i,tp,'target');break
    if ex is None:ex=(last,float(o[last]),'time')
    exit_idx,exit_price,reason=ex
    gross=side*(exit_price/price-1)*10000
    # Conservatively known favorable movement before the exit candle.
    # If stop and target collide in one candle, do not credit its high/low.
    prior=favourable[:max(0,exit_idx-entry)]
    before_exit_bp=float(max(0.0, float(np.max(prior))*10000)) if len(prior) else 0.0
    if reason in ('target','target_gap'):
        before_exit_bp=max(before_exit_bp,TARGET_BP)
    return dict(max_favorable_before_exit_bp=before_exit_bp,
                exit_index=exit_idx,exit_reason=reason,exit_bars=int(exit_idx-entry),
                gross_bp=float(gross),base_net_bp=float(gross-COST_BP),
                stress_net_bp=float(gross-STRESS_COST_BP),peak_index=peak_idx,
                peak_minute_bar=int((peak_idx-entry)*5),max_mfe_bp=max_f,
                max_mae_bp=max_a,same_bar_ambiguous=bool(both))

def synthetic():
    o=np.full(40,100.);h=np.full(40,100.);l=np.full(40,100.)
    h[2]=100.3;l[2]=99.9
    a=touch(o,h,l,2,1)
    assert a['exit_reason']=='target' and abs(a['gross_bp']-28)<1e-8
    h[2]=100.4;l[2]=99.8
    b=touch(o,h,l,2,1)
    assert b['exit_reason']=='ambiguous_stop_first' and b['gross_bp']<0
    h[2]=100.0;l[2]=100.0
    o[3]=99.7;h[3]=99.8;l[3]=99.6
    c=touch(o,h,l,2,1)
    assert c['exit_reason']=='stop_gap' and c['gross_bp']<b['gross_bp']
    # short target / stop, and no-touch expiry
    o.fill(100);h.fill(100);l.fill(100);l[2]=99.7
    assert touch(o,h,l,2,-1)['exit_reason']=='target'
    h[2]=100.3;l[2]=99.7
    assert touch(o,h,l,2,-1)['exit_reason']=='ambiguous_stop_first'
    h.fill(100);l.fill(100)
    assert touch(o,h,l,2,1)['exit_reason']=='time'
    print('R14 SYNTHETIC: PASS, long/short target, ambiguous, adverse gap, expiry')

def summary(d):
    x=d.base_net_bp.to_numpy(dtype=float)
    wins=x[x>0].sum();losses=-x[x<0].sum()
    return {'signals':len(d),'target_pct':round(100*d.exit_reason.isin(['target','target_gap']).mean(),2),
            'stop_pct':round(100*d.exit_reason.isin(['stop','stop_gap','ambiguous_stop_first']).mean(),2),
            'time_pct':round(100*(d.exit_reason=='time').mean(),2),
            'ambiguous_pct':round(100*d.same_bar_ambiguous.mean(),2),
            'gross_mean_bp':round(d.gross_bp.mean(),3),'net_mean_bp':round(x.mean(),3),
            'stress_net_mean_bp':round(d.stress_net_bp.mean(),3),
            'profit_factor_base':round(wins/losses,3) if losses else None,
            'mean_exit_bars':round(d.exit_bars.mean(),2),
            'peak_bar_median_min':round(d.peak_minute_bar.median(),1),
            'peak_mfe_median_bp':round(d.max_mfe_bp.median(),2),
            'pre_exit_favorable_median_bp':round(d.max_favorable_before_exit_bp.median(),2),
            'stops_without_prior_14bp_favorable_pct':round(100*((d.exit_reason.isin(['stop','stop_gap','ambiguous_stop_first'])) & (d.max_favorable_before_exit_bp<14)).mean(),2)}

def main():
    synthetic()
    if '--preflight' in sys.argv:
        if not R12.exists():raise FileNotFoundError(R12)
        if digest(R12)!=R12_HASH:raise RuntimeError('R12 source changed')
        for file in ('R13_RESULTS.json','R13_ENTRY_PATHS.csv'):
            if not (INPUT/file).exists():raise FileNotFoundError(INPUT/file)
        print('R14 PREFLIGHT: PASS / no market measurement');return
    if sys.argv[1:]!=['--run']:
        raise SystemExit('Usage: python R14_BTC_FirstTouch_OneRun.py --preflight | --run')
    if OUTPUT.exists():raise RuntimeError('FAIL CLOSED: output folder exists; no overwrite')
    if digest(R12)!=R12_HASH:raise RuntimeError('R12 hash mismatch')
    # Import source without invoking any trade runner / modifying original files
    import importlib.util
    spec=importlib.util.spec_from_file_location('r12_ref_readonly',R12)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    a=mod.load_and_audit()
    recorded=json.loads((INPUT/'R13_RESULTS.json').read_text())
    if a['hashes']!=recorded['input_sha256']:raise RuntimeError('Canonical BTC input hashes differ from R13')
    sig,_=mod.features(a)
    d=pd.read_csv(INPUT/'R13_ENTRY_PATHS.csv',parse_dates=['signal_time_utc','entry_time_utc'])
    if len(d)!=45279 or d[['period','strategy','signal_idx']].duplicated().any():raise RuntimeError('Unexpected R13 event count or duplicates')
    t,o,h,l=a['t'],a['o'],a['h'],a['l']
    bounds={'2024_SepDec':int(t.searchsorted(pd.Timestamp('2025-01-01',tz='UTC'))),
            '2025_JanDec':int(t.searchsorted(pd.Timestamp('2026-01-01',tz='UTC')))}
    result=[]
    for row in d.itertuples(index=False):
        j=int(row.signal_idx);side=int(row.side);ent=j+1
        if sig[row.strategy][j]!=side:raise RuntimeError(f'Original entry rule mismatch: {row.strategy} {j}')
        if t[j]!=row.signal_time_utc or t[ent]!=row.entry_time_utc:raise RuntimeError('R13 timestamp mismatch')
        if ent+HORIZON>=bounds[row.period]:raise RuntimeError('Exit crosses period')
        z=touch(o,h,l,ent,side)
        if not (np.isclose(z['max_mfe_bp'],row.mfe_60_bp,atol=1e-7) and np.isclose(z['max_mae_bp'],row.mae_60_bp,atol=1e-7)):
            raise RuntimeError('R13 excursions do not reconcile')
        z.update(period=row.period,strategy=row.strategy,signal_idx=j,side=side,
                 entry_time_utc=str(t[ent]),exit_time_utc=str(t[z['exit_index']]),
                 peak_bar_open_utc=str(t[z['peak_index']]),
                 trend_60m_bp=float(row.trend_60m_bp),aligned_60m=bool(row.aligned_60m))
        result.append(z)
    out=pd.DataFrame(result)
    summaries=[]
    for (period,strategy),sub in out.groupby(['period','strategy'],sort=True):
        z=summary(sub);z.update(period=period,strategy=strategy);summaries.append(z)
        print(f'{period} {strategy:9s} n={z["signals"]:5d} target={z["target_pct"]:5.1f}% stop={z["stop_pct"]:5.1f}% time={z["time_pct"]:5.1f}% net={z["net_mean_bp"]:+.2f} bp')
    OUTPUT.mkdir(parents=True,exist_ok=False)
    out.to_csv(OUTPUT/'R14_FIRST_TOUCH_EVENTS.csv',index=False)
    response={'status':'EXPLORATORY_NO_CONFIRMED_STRATEGY',
              'parameters':{'stop_bp':STOP_BP,'target_bp':TARGET_BP,'max_hold_bars':HORIZON,
                 'cost_base_bp':COST_BP,'cost_stress_bp':STRESS_COST_BP,
                 'bar_collision_policy':'stop_first','gap_policy':'opening_price',
                 'peak':'bar with greatest favorable high/low across full 60m, not realized trade peak'},
              'input_r13_csv_sha256':digest(INPUT/'R13_ENTRY_PATHS.csv'),
              'input_r13_json_sha256':digest(INPUT/'R13_RESULTS.json'),
              'input_r12_source_sha256':digest(R12),
              'input_market_hashes':a['hashes'],'summary':summaries}
    (OUTPUT/'R14_RESULTS.json').write_text(json.dumps(response,indent=2,ensure_ascii=False))
    # No post-hoc optimizations or candidate ranking
    lines=['# R14 BTC First-Touch Explorative Diagnose','',
           '**Nicht bestätigt; keine live nutzbare Strategie und keine Optimierung.**','',
           'Signal = unveränderter R12-Entry (alle R13-Signale). Einstieg nächste 5m Open. ',
           'Feste, nur diagnostische Grenzen: Stop 14bp / Ziel 28bp / Zeitablauf nach 60 Minuten.',
           'Konservative Reihenfolge Stop vor Ziel bei Berührung in derselben 5m-Kerze; offene Kurslücke zum schlechteren Open.',
           'Netto = realisierter OHLC-Bruttoertrag minus 14bp modellierte Kosten; Stress 24bp. Das ist keine Live-PnL.',
           'Jedes Signal wird unabhängig beurteilt, auch bei zeitlich überlappenden Signalen; Ergebnisse sind keine Portfolio-PnL.',
           'Ein historisches MFE-Maximum ist nicht die erreichbare Take-Profit-Höhe und kann erst nach einem Stop eintreten.',
           'max_favorable_before_exit_bp zählt nur vollständig vor dem Exit-Bar bekannte Kursausschläge; bei Stop-/Ziel-Kollision wird der Exit-Bar konservativ nicht als Gewinnchance gewertet.',
           '', '| Zeitraum | Einstieg | n | Ziel zuerst % | Stop zuerst % | Zeit % | Konflikt % | Ø brutto bp | Ø netto bp | PF |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for z in summaries:
        lines.append(f'| {z["period"]} | {z["strategy"]} | {z["signals"]} | {z["target_pct"]} | {z["stop_pct"]} | {z["time_pct"]} | {z["ambiguous_pct"]} | {z["gross_mean_bp"]} | {z["net_mean_bp"]} | {z["profit_factor_base"]} |')
    lines.extend(['','## Bereits beim Entry bekannte Marktbedingungen: 60m-Trendrichtung','',
                  '| Zeitraum | Strategie | 60m relativ zum Signal | n | Ziel zuerst % | Stop zuerst % | Ø netto bp |',
                  '|---|---|---|---:|---:|---:|---:|'])
    for (period,strategy,aligned),sub in out.groupby(['period','strategy','aligned_60m'],sort=True):
        z=summary(sub)
        lines.append(f'| {period} | {strategy} | {"konform" if aligned else "gegenlaeufig"} | {z["signals"]} | {z["target_pct"]} | {z["stop_pct"]} | {z["net_mean_bp"]} |')
    lines.extend(['','## Was die Diagnose NICHT leisten kann','',
                  'Keine historischen Funding-Abrechnungen, keine Orderbuch-Ausführung, kein Tick-Level für intrabar Reihenfolge.',
                  'Keine separaten Holdout-Daten; diese historische Stichprobe wurde bereits vielfach untersucht.',
                  'Trend-/Stundengruppen nur mit vorab bekannten Merkmalen und als Explorationshinweis, nicht als bestätigter Filter.',
                  'Ziel 28/Stop 14 ist NICHT aus den R14-Ergebnissen optimiert, sondern vorab als einfache feste Diagnose festgelegt.'])
    (OUTPUT/'R14_REPORT.md').write_text('\n'.join(lines)+'\n')
    print('R14 FILES:',OUTPUT/'R14_REPORT.md',OUTPUT/'R14_RESULTS.json',OUTPUT/'R14_FIRST_TOUCH_EVENTS.csv',sep='\n')

if __name__=='__main__':
    try:main()
    except Exception as e:print('R14 FAIL CLOSED:',type(e).__name__,str(e));sys.exit(4)
