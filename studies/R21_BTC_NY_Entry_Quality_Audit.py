#!/usr/bin/env python3
"""R21: Read-only descriptive audit of frozen R20 opening-range entries.
No re-backtesting, no model fitting, no parameter selection, no productive writes.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd

HOME=Path.home()
ROOT=HOME/'QuantResearch/R20_BTC_ORB_5m_15m/Sep2024_Dec2025_v1'
TRADES=ROOT/'R20_TRADES.csv'
RESULT=ROOT/'R20_RESULTS.json'
OUT=HOME/'QuantResearch/R21_BTC_NY_EntryQuality/Sep2024_Dec2025_v1'
STUDIES=HOME/'QuantResearch-Git/studies'
SCRIPT_R19=STUDIES/'R19_BTC_NY_ORB_Fakeout_OneRun.py'
SCRIPT_R20=STUDIES/'R20_BTC_ORB_5m_vs_15m_OneRun.py'
EXPECTED_R19='a626bce4bad126e372247bb15c061c861ebc2b8b5cf9157c7c2e4340a8d88769'


def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def safe_num(arr):
    arr=np.asarray(arr,dtype=float);arr=arr[np.isfinite(arr)]
    return float(np.median(arr)) if arr.size else None


def test_synthetic():
    # Every feature must use signal-close data or earlier, not future prices.
    t=pd.date_range('2025-07-01 13:00',periods=36,freq='5min',tz='UTC')
    o=np.ones(36)*100;h=o+.1;l=o-.1;c=o.copy()
    o[10]=100.1;c[10]=100.2;h[10]=100.25
    def v(idx):
        tr=np.maximum.reduce((h-l,np.abs(h-np.r_[c[0],c[:-1]]),np.abs(l-np.r_[c[0],c[:-1]])))
        atr=pd.Series(tr).rolling(10).mean().iloc[idx]
        return (float((c[idx]/c[idx-6]-1)*1e4),float(abs(c[idx]-o[idx])/atr))
    before=v(10)
    h[11:]*=2;l[11:]*=.5;c[11:]*=1.5
    assert np.allclose(before,v(10))
    assert t[10].tz_convert('America/New_York').strftime('%H:%M')=='09:50'
    return True


def load_and_audit():
    for p in (TRADES,RESULT,SCRIPT_R19,SCRIPT_R20):
        if not p.is_file():raise RuntimeError(f'STOP: Quelldatei fehlt: {p}')
    if sha(SCRIPT_R19)!=EXPECTED_R19:raise RuntimeError('STOP: R19-Codehash verändert')
    obj=json.loads(RESULT.read_text())
    if obj.get('R19_baseline_reproduced') is not True:raise RuntimeError('STOP: R20 R19 baseline not verified')
    if obj.get('R19_frozen_sha256')!=EXPECTED_R19:raise RuntimeError('STOP: R20 R19 hash differs')
    if obj.get('source_sha256')!=sha(SCRIPT_R20):raise RuntimeError('STOP: R20 code no longer matches saved result')
    d=pd.read_csv(TRADES)
    needed={'ny_date','period','strategy','range_bp','signal_idx','entry_utc','direction','risk_bp','net_base_bp','net_stress_bp','exit_reason','entry_price'}
    if not needed.issubset(d.columns):raise RuntimeError(f'STOP: R20 Trades fields missing {needed-set(d.columns)}')
    if d.duplicated(['ny_date','strategy']).any():raise RuntimeError('STOP: duplicate method/day')
    if set(d.strategy)!={'ORB_5m','ORB_15m'}:raise RuntimeError('STOP: unrecognized R20 strategies')
    for per in obj['results']:
        for typ,tag in [('5m','ORB_5m'),('15m','ORB_15m')]:
            x=d[(d.period==per['period'])&(d.strategy==tag)]
            if len(x)!=per[typ]['trades'] or not np.isclose(x.net_base_bp.mean(),per[typ]['mean_net_trade_bp'],atol=1e-8):
                raise RuntimeError('STOP: CSV does not match R20 result '+per['period']+' '+tag)
    return d,obj


def attach_features(d):
    # Reuse pinned canonical loader only. Production datasets read-only.
    import importlib.util
    spec=importlib.util.spec_from_file_location('r21_pinned_r19',SCRIPT_R19)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    a=m.load();t=a['t'];o,h,l,c=[np.asarray(a[k],dtype=float) for k in ('o','h','l','c')]
    atr=np.asarray(m.atr14(a),dtype=float)
    ny=t.tz_convert(m.NY);starts={}
    for i,ts in enumerate(ny):
        if ts.hour==9 and ts.minute==30:starts[str(ts.date())]=i
    records=[]
    for r in d.itertuples(index=False):
        j=int(r.signal_idx)
        if j<15 or j+1>=len(t):raise RuntimeError('STOP: invalid signal index')
        if str(t[j])!=str(pd.Timestamp(r.signal_utc)):
            raise RuntimeError('STOP: signal timestamp/index mismatch')
        if str(t[j+1])!=str(pd.Timestamp(r.entry_utc)):
            raise RuntimeError('STOP: entry timestamp/index mismatch')
        s=starts.get(r.ny_date)
        if s is None or not(s+1<=j<s+24):raise RuntimeError('STOP: NY session index mismatch')
        bars=1 if r.strategy=='ORB_5m' else 3
        rh=np.max(h[s:s+bars]);rl=np.min(l[s:s+bars]);middle=(rh+rl)/2
        if not np.isclose((rh/rl-1)*1e4,r.range_bp,atol=1e-7):raise RuntimeError('STOP: opening range mismatch')
        if r.direction not in (-1,1):raise RuntimeError('STOP: direction')
        edge=rh if r.direction==1 else rl
        if r.direction*(c[j]-edge)<=0:raise RuntimeError('STOP: signal not a breakout')
        a14=atr[j]
        if not np.isfinite(a14) or a14<=0:raise RuntimeError('STOP: ATR unavailable')
        # All features available at completed signal bar j (or earlier).
        features={
          'atr14_bp_signal':a14/c[j]*1e4,
          'hour_return_bp_signal':(c[j]/c[j-12]-1)*1e4,
          'hour_aligned_bp_signal':r.direction*(c[j]/c[j-12]-1)*1e4,
          'body_to_atr_signal':abs(c[j]-o[j])/a14,
          'overshoot_to_atr_signal':r.direction*(c[j]-edge)/a14,
          'opening_range_to_atr_signal':(rh-rl)/a14,
          'risk_estimate_bp_signal':r.direction*(c[j]-middle)/c[j]*1e4,
          'minutes_after_0930_to_signal_close':(j-s+1)*5,
        }
        if any(not np.isfinite(v) for v in features.values()):raise RuntimeError('STOP: nonfinite feature')
        records.append(features)
    x=pd.concat([d.reset_index(drop=True),pd.DataFrame(records)],axis=1)
    x['outcome_class']=np.select([x.exit_reason.isin(['target','target_gap']),x.exit_reason.isin(['stop','stop_gap','ambiguous_stop_first'])],['target','stop'],default='time_or_other')
    return x,a


def report(x,src):
    fields=['atr14_bp_signal','hour_aligned_bp_signal','body_to_atr_signal','overshoot_to_atr_signal','opening_range_to_atr_signal','risk_estimate_bp_signal','minutes_after_0930_to_signal_close']
    results=[];lines=['# R21 BTC NY Opening-Range Einstiegsaudit','',
       '**Reine explorative Diagnose der unveränderten R20-Trades. Keine neuen Backtests, keine Auswahl einer Regel.**','',
       'Merkmale werden ausschließlich anhand des jeweils abgeschlossenen Signalbalkens und der Vergangenheit bestimmt.','',
       '| Zeitraum | OR | Trades | Ziel | Stop | Zeit/sonstige | Netto/Trade (bp) |',
       '|---|---|---:|---:|---:|---:|---:|']
    for (period,method),g in x.groupby(['period','strategy'],sort=True):
        counts=g.outcome_class.value_counts();n=len(g)
        lines.append(f'| {period} | {method} | {n} | {counts.get("target",0)} | {counts.get("stop",0)} | {counts.get("time_or_other",0)} | {g.net_base_bp.mean():+.2f} |')
        item={'period':period,'strategy':method,'trades':n,'net_bp_mean':float(g.net_base_bp.mean()),'outcomes':{k:int(v) for k,v in counts.items()},'features':{}}
        lines+=['',f'### {period}, {method}','',
                '| Vor dem Einstieg bekanntes Merkmal | Median Ziel-Trades | Median Stop-Trades | Gesamtmedian |',
                '|---|---:|---:|---:|']
        for f in fields:
            tw=g.loc[g.outcome_class=='target',f];sl=g.loc[g.outcome_class=='stop',f]
            vals={'median_target':safe_num(tw),'median_stop':safe_num(sl),'median_all':safe_num(g[f])}
            item['features'][f]=vals
            fmt=lambda v:'n/a' if v is None else f'{v:.3f}'
            lines.append(f'| {f} | {fmt(vals["median_target"])} | {fmt(vals["median_stop"])} | {fmt(vals["median_all"])} |')
        results.append(item)
    lines+=['','## Interpretation und Grenzen','',
      '- Medianunterschiede zwischen Ziel- und Stop-Trades sind **rückblickend konditioniert auf den Ausgang**. Kein Prognosevorteil bewiesen.',
      '- Die Öffnungsspanne wurde bereits in R18 als interessantes NY-Fenster ausgewählt; 2024/2025 sind kein unabhängiger Holdout.',
      '- Ein Merkmal mit scheinbar günstigem Unterschied darf **nicht** nachträglich als getesteter Filter oder Profitsignal bezeichnet werden.',
      '- R20-Kosten 14/24 bp sind Modellannahmen; Funding- und echte Ausführungskosten fehlen.',
      '- Unter den eingefrorenen R20-Regeln sind beide Strategien in beiden Jahren netto negativ.',
      '- Für eine spätere bestätigende Studie: genau **eine** sachlich begründete Filterhypothese vorab definieren und auf unabhängigem Zeitraum prüfen.','']
    return {'status':'EXPLORATORY_DIAGNOSTIC_ONLY','source_R20_code_sha256':src['source_sha256'],
            'R20_trades_sha256':sha(TRADES),'features_exante':fields,'results':results},'\n'.join(lines)


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--preflight',action='store_true');g.add_argument('--run',action='store_true')
    a=p.parse_args();assert test_synthetic();print('R21 SYNTHETIK PASS: feature isolation, NY timezone')
    d,s=load_and_audit();print(f'R21 R20 REPRODUKTION PASS: {len(d)} Trades, unveränderte Ergebnisse')
    if a.preflight:
        print('R21 PREFLIGHT ONLY: keine Merkmalsmessung');return
    if OUT.exists():raise RuntimeError('STOP: R21 result folder already exists')
    x,market=attach_features(d)
    out,txt=report(x,s)
    out['source_input_hashes']=market['hashes']
    OUT.mkdir(parents=True,exist_ok=False)
    x.to_csv(OUT/'R21_ENTRY_FEATURES.csv',index=False)
    (OUT/'R21_RESULTS.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    (OUT/'R21_REPORT.md').write_text(txt+'\n')
    print('R21 DIAGNOSE ABGESCHLOSSEN: keine neue Strategie, keine Orders')
    for r in out['results']:
        print(r['period'],r['strategy'],'Trades',r['trades'],'Netto',round(r['net_bp_mean'],3),
              'Ziel',r['outcomes'].get('target',0),'Stop',r['outcomes'].get('stop',0))
    print('BERICHT:',OUT/'R21_REPORT.md')

if __name__=='__main__':main()
