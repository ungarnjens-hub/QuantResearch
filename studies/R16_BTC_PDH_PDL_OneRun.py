#!/usr/bin/env python3
"""R16: Frozen BTC previous-day high/low event study. Research only, no orders.

Use previously audited R12 Binance Futures loader, only read local canonical 5m data.
Daily UTC boundaries, no future information in levels or signals. No tuning.
"""
from __future__ import annotations
import hashlib, importlib.util, json, math, sys
from pathlib import Path
import numpy as np
import pandas as pd

HOME=Path.home()
REF=HOME/'QuantResearch-Git/studies/R12_3_Strategien_BTC_Explorativ.py'
REF_SHA='7c434924f85cdd94fb09438dbf033cb797a946bc93ff8f3bdb82a9850839609d'
OUT=HOME/'QuantResearch/R16_BTC_PDH_PDL/Sep2024_Dec2025_v1'
HORIZONS=(12,24,288)   # 60min, 120min, 24h
CONFIRM_BARS=3
BREAK_BUFFER_BP=15.
ATR_LEN=14
ATR_STOP_BUFFER=.25
RR=2.0
EXIT_BARS=24
COST_BP=14.
STRESS_BP=24.
SEED=20261115


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for z in iter(lambda:f.read(1<<20),b''):h.update(z)
    return h.hexdigest()


def load():
    if not REF.is_file() or sha(REF)!=REF_SHA:raise RuntimeError('Frozen R12 loader missing or changed')
    spec=importlib.util.spec_from_file_location('r16_frozen_loader',REF)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.load_and_audit()


def levels(a):
    """UTC day levels from completed preceding day ONLY; no in-day future."""
    t=a['t'];dates=pd.DatetimeIndex(t.floor('D').unique())
    starts=np.searchsorted(t.asi8, dates.asi8)
    ends=np.r_[starts[1:],len(t)]
    pdh=np.full(len(dates),np.nan);pdl=pdh.copy()
    for d in range(1,len(dates)):
        p=starts[d-1];q=ends[d-1]
        if q-p!=288:raise RuntimeError('Previous UTC day incomplete')
        pdh[d]=float(a['h'][p:q].max());pdl[d]=float(a['l'][p:q].min())
    return dates,starts,ends,pdh,pdl


def atr(a):
    h,l,c=a['h'],a['l'],a['c'];previous=np.r_[c[0],c[:-1]]
    tr=np.maximum.reduce((h-l,abs(h-previous),abs(l-previous)))
    return pd.Series(tr).rolling(ATR_LEN,min_periods=ATR_LEN).mean().to_numpy()


def path(a,idx,side,horizon):
    """All 5m highs/lows from actual next-open entry until horizon expiry.
    MFE is an *oracle* upper bound; intrabar peak time is known only as a bar.
    """
    j=idx;stop=idx+horizon
    if stop>=len(a['o']):return None
    entry=float(a['o'][j]);h=a['h'][j:stop];l=a['l'][j:stop]
    fav=(h/entry-1)*10000 if side==1 else (1-l/entry)*10000
    adv=(1-l/entry)*10000 if side==1 else (h/entry-1)*10000
    k=int(fav.argmax());v=int(adv.argmax())
    gross=float(side*(a['o'][stop]/entry-1)*10000)
    return {'mfe_bp':float(max(0.,fav[k])),'mae_bp':float(max(0.,adv[v])),
            'peak_bar_from_entry':k+1,'peak_minutes_upper':5*(k+1),
            'max_adverse_bar_from_entry':v+1,'fixed_exit_gross_bp':gross,
            'fixed_exit_net14_bp':gross-COST_BP}


def trade(a,idx,side,stop_level,upper_exclusive):
    o,h,l=a['o'],a['h'],a['l']
    if idx+EXIT_BARS>=upper_exclusive:return None
    e=float(o[idx]);risk=side*(e-stop_level)
    if risk<=0 or stop_level<=0:return None
    target=e+side*RR*risk
    exit_index=idx+EXIT_BARS;exit_price=float(o[exit_index]);reason='time';collision=False
    for k in range(idx,idx+EXIT_BARS):
        op,hi,lo=float(o[k]),float(h[k]),float(l[k])
        gap_stop=op<=stop_level if side==1 else op>=stop_level
        gap_tp=op>=target if side==1 else op<=target
        hit_stop=lo<=stop_level if side==1 else hi>=stop_level
        hit_tp=hi>=target if side==1 else lo<=target
        if gap_stop:reason='stop_gap';exit_price=op;exit_index=k;break
        if gap_tp:reason='target_gap';exit_price=target;exit_index=k;break
        if hit_stop and hit_tp:reason='ambiguous_stop_first';collision=True;exit_price=stop_level;exit_index=k;break
        if hit_stop:reason='stop';exit_price=stop_level;exit_index=k;break
        if hit_tp:reason='target';exit_price=target;exit_index=k;break
    gross=side*(exit_price/e-1)*10000
    return {'trade_gross_bp':gross,'trade_net14_bp':gross-COST_BP,
            'trade_net24_bp':gross-STRESS_BP,'trade_risk_bp':risk/e*10000,
            'trade_exit_reason':reason,'trade_bars':int(exit_index-idx),
            'trade_collision':collision,'trade_exit_index':int(exit_index)}


def run_research(a):
    t=a['t'];o,h,l,c=(a[z] for z in ('o','h','l','c'))
    days,starts,ends,pdh,pdl=levels(a);atr_vals=atr(a)
    records=[]
    bounds=[('2024_SepDec','2024-09-01','2025-01-01'),('2025_JanDec','2025-01-01','2026-01-01')]
    for label,start,end in bounds:
        low=int(t.searchsorted(pd.Timestamp(start,tz='UTC')))
        high=int(t.searchsorted(pd.Timestamp(end,tz='UTC')))
        for d in range(1,len(days)):
            s=int(starts[d]);endday=int(ends[d])
            if not (low<=s<high):continue
            for kind,level,side in [('PDH',pdh[d],-1),('PDL',pdl[d],1)]:
                # Only FIRST actual approach/crossing of each level per UTC day.
                touch=None
                for j in range(s,max(s,endday-1)):
                    if not (np.isfinite(atr_vals[j]) and atr_vals[j]>0):continue
                    prev=c[j-1] if j>s else o[j]  # no previous-day close mistaken as intra-day approach
                    if kind=='PDH' and prev<level and h[j]>=level:touch=j;break
                    if kind=='PDL' and prev>level and l[j]<=level:touch=j;break
                if touch is None:continue
                j=touch
                row={'period':label,'day_utc':str(days[d].date()),'kind':kind,'level':float(level),
                     'touch_time_utc':str(t[j]),'touch_close':float(c[j]),
                     'touch_candle_high':float(h[j]),'touch_candle_low':float(l[j]),
                     'side':side,'atr_pct_at_touch':float(100*atr_vals[j]/c[j]),
                     'prev_day_range_bp':float(10000*(pdh[d]/pdl[d]-1)),
                     'touch_to_level_bp':float(side*(c[j]/level-1)*10000)}
                # Observe touch entry next open and full following movement.
                if j+1>=high:continue
                touch_entry=j+1
                row['touch_entry_utc']=str(t[touch_entry]);row['touch_entry_price']=float(o[touch_entry])
                for n in HORIZONS:
                    p=path(a,touch_entry,side,n) if touch_entry+n<high else None
                    for metric in ('mfe_bp','mae_bp','peak_minutes_upper','fixed_exit_gross_bp','fixed_exit_net14_bp'):
                        row[f'touch_{n*5}m_{metric}']=p[metric] if p else np.nan
                # Confirmation: after touch, within next three COMPLETED bars,
                # rejection close back inside prior-day range and candle in reversal direction.
                confirm=None;state='no_confirmation'
                for k in range(j+1,min(j+CONFIRM_BARS+1,endday,high-1)):
                    if side==1 and c[k]<level*(1-BREAK_BUFFER_BP/10000):state='broken';break
                    if side==-1 and c[k]>level*(1+BREAK_BUFFER_BP/10000):state='broken';break
                    good=(c[k]>level and c[k]>o[k] and c[k]>c[k-1]) if side==1 else (c[k]<level and c[k]<o[k] and c[k]<c[k-1])
                    if good:confirm=k;state='confirmed';break
                row['confirmation_state']=state
                row['confirmed']=confirm is not None
                row['confirmation_utc']=str(t[confirm]) if confirm is not None else ''
                row['confirmed_entry_utc']=''
                row['confirm_entry_price']=np.nan
                row['travel_contact_to_confirmation_bp']=np.nan
                row['confirm_trade_net14_bp']=np.nan
                row['confirm_trade_net24_bp']=np.nan
                row['confirm_trade_gross_bp']=np.nan
                row['confirm_trade_exit_reason']='no_trade'
                row['confirm_trade_risk_bp']=np.nan
                row['confirm_trade_bars']=np.nan
                if confirm is not None:
                    entry=confirm+1
                    row['confirmed_entry_utc']=str(t[entry]);row['confirm_entry_price']=float(o[entry])
                    # Favorable move already used up between first touch entry and confirmed entry.
                    row['travel_contact_to_confirmation_bp']=float(side*(o[entry]/o[touch_entry]-1)*10000)
                    for n in HORIZONS:
                        p=path(a,entry,side,n) if entry+n<high else None
                        for metric in ('mfe_bp','mae_bp','peak_minutes_upper','fixed_exit_gross_bp','fixed_exit_net14_bp'):
                            row[f'confirm_{n*5}m_{metric}']=p[metric] if p else np.nan
                    stop=float(min(l[j:confirm+1])-.25*atr_vals[confirm]) if side==1 else float(max(h[j:confirm+1])+.25*atr_vals[confirm])
                    result=trade(a,entry,side,stop,high)
                    if result:
                        row.update({f'confirm_{key}':v for key,v in result.items() if key!='trade_exit_index'})
                    else:
                        row['confirmation_state']='untradeable_confirmation'
                        row['confirmed']=False
                records.append(row)
    return pd.DataFrame(records)


def safe_float(value):
    return float(value) if pd.notna(value) else None


def summary(data):
    ret=[]
    for (period,kind),g in data.groupby(['period','kind'],sort=True):
        good=g[g.confirmed & g.confirm_trade_net14_bp.notna()]
        obj={'period':period,'level':kind,'first_contacts':len(g),'confirmed':len(good),
             'confirmation_fraction':len(good)/len(g),
             'confirmation_states':{str(k):int(v) for k,v in g.confirmation_state.value_counts().items()}}
        for n in HORIZONS:
            key=f'confirm_{n*5}m_';m=good[key+'mfe_bp'].dropna();ad=good[key+'mae_bp'].dropna()
            obj[f'{n*5}m']={'valid':len(m),
                'median_mfe_bp':safe_float(m.median()),'p75_mfe_bp':safe_float(m.quantile(.75)),
                'p90_mfe_bp':safe_float(m.quantile(.90)),'median_mae_bp':safe_float(ad.median()),
                'median_peak_minutes_upper':safe_float(good[key+'peak_minutes_upper'].median()),
                'mean_fixed_net14_bp':safe_float(good[key+'fixed_exit_net14_bp'].mean()),
                'mfe_ge_28bp_fraction':safe_float((m>=28).mean()) if len(m) else None}
        if len(good):
            obj['structural_trade_120m']={'n':len(good),'mean_net14_bp':safe_float(good.confirm_trade_net14_bp.mean()),
                'mean_net24_bp':safe_float(good.confirm_trade_net24_bp.mean()),
                'target_fraction':safe_float(good.confirm_trade_exit_reason.isin(('target','target_gap')).mean()),
                'stop_fraction':safe_float(good.confirm_trade_exit_reason.isin(('stop','stop_gap','ambiguous_stop_first')).mean()),
                'time_fraction':safe_float((good.confirm_trade_exit_reason=='time').mean()),
                'median_risk_bp':safe_float(good.confirm_trade_risk_bp.median()),
                'median_hold_bars':safe_float(good.confirm_trade_bars.median())}
            obj['per_original_contact_net14_bp']=safe_float(good.confirm_trade_net14_bp.sum()/len(g))
        ret.append(obj)
    return ret


def synthetic():
    t=pd.date_range('2025-01-01',periods=3*288,freq='5min',tz='UTC')
    x={'t':t,'o':np.full(len(t),100.),'h':np.full(len(t),101.),'l':np.full(len(t),99.),'c':np.full(len(t),100.)}
    dates,starts,ends,pdh,pdl=levels(x)
    assert len(dates)==3 and pdh[1]==101 and pdl[1]==99
    x['h'][2*288+7]=999
    assert levels(x)[3][1]==101 and levels(x)[3][2]==101
    assert path(x,290,1,12)['mfe_bp']>0
    y={k:np.full(60,100.) for k in ('o','h','l','c')}
    y['h'][5]=103
    assert trade(y,5,1,99,60)['trade_exit_reason']=='target'
    y['l'][5]=98
    assert trade(y,5,1,99,60)['trade_exit_reason']=='ambiguous_stop_first'
    y['h'][5]=100;y['l'][5]=100;y['o'][6]=97;y['h'][6]=97;y['l'][6]=97
    assert trade(y,5,1,99,60)['trade_exit_reason']=='stop_gap'
    y['o'].fill(100);y['h'].fill(100);y['l'].fill(100)
    assert trade(y,5,-1,101,60)['trade_exit_reason']=='time'
    assert trade(y,40,1,99,60) is None
    print('R16 SYNTHETIC PASS: prior UTC day, future isolation, OHLC paths, TP/SL, tie, gap, expiry')


def main():
    synthetic()
    if sys.argv[1:] not in (['--preflight'],['--run']):raise RuntimeError('Usage: --preflight | --run')
    if sys.argv[1:]==['--run'] and OUT.exists():raise RuntimeError('FAIL CLOSED: existing result folder')
    a=load();print('R16 DATA GATE PASS',len(a['t']),'closed BTC 5m bars; files',len(a['hashes']))
    if sys.argv[1:]==['--preflight']:
        print('R16 PREFLIGHT ONLY: no real market events calculated');return
    events=run_research(a)
    if len(events)==0:raise RuntimeError('No PDH/PDL first touch events')
    output=summary(events)
    result={'study':'R16 BTC prior day high/low first-touch, confirmed reversal',
            'status':'EXPLORATORY_NOT_BLINDTEST',
            'market_hashes':a['hashes'],'frozen_R12_loader_sha256':REF_SHA,
            'study_script_sha256':sha(Path(__file__)),
            'fixed_parameters':{'utc_previous_day':True,'first_contact_per_day_per_level':True,
              'confirmation_following_closed_5m_bars':CONFIRM_BARS,'break_buffer_bp':BREAK_BUFFER_BP,
              'horizons_minutes':[5*v for v in HORIZONS], 'stop_buffer_atr':ATR_STOP_BUFFER,
              'rr':RR,'trade_limit_minutes':5*EXIT_BARS,'cost_base_bp':COST_BP,'cost_stress_bp':STRESS_BP},
            'limitations':['No tick-level path; same-bar collision stop first','MFE and peak time oracle (not executable)',
              'Existing 2024/2025 data heavily explored; no independent holdout',
              'Unconfirmed contacts counted in per-opportunity average as zero; no live order',
              'One first approach per level per UTC day; no inference on later touches',
              'PDH/PDL do not imply true liquidity clusters','No actual historical funding or orderbook'],
            'results':output}
    lines=['# R16 BTC Vortageshoch/Vortagestief: explorative Untersuchung','',
           '**Nicht unabhängig bestätigt; keine produktive Handelsstrategie.**','',
           'PDH/PDL: Hoch und Tief der abgeschlossenen vorherigen UTC-Tageskerze. '
           'Erster Kontakt pro Level und Tag. Short bei PDH, Long bei PDL; Bestätigung innerhalb '
           'der folgenden drei abgeschlossenen 5m-Kerzen; Entry zur nächsten 5m-Open.','',
           'Maximale günstige Kursbewegung (MFE) und Peak-Zeitpunkt sind **nur rückblickend bekannt**. '
           'Ausführbarer Diagnose-Trade: struktureller Stop mit 0,25 ATR Puffer, TP 2R, 120 Minuten, '
           '14bp/24bp Kostenannahmen.','',
           '| Periode | Level | Kontakte | Bestätigt | Median MFE 60m | Median MFE 24h | Median Peak 60m | Netto/Trade | Netto/Kontakt |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for x in output:
        z=x.get('structural_trade_120m',{});p=x['60m'];q=x['1440m']
        f=lambda y: 'n/a' if y is None else f'{y:.2f}'
        lines.append(f"| {x['period']} | {x['level']} | {x['first_contacts']} | {x['confirmed']} | {f(p['median_mfe_bp'])} bp | {f(q['median_mfe_bp'])} bp | {f(p['median_peak_minutes_upper'])} min | {f(z.get('mean_net14_bp'))} bp | {f(x.get('per_original_contact_net14_bp'))} bp |")
    lines+=['','## Interpretation','',
             'MFE ist rückblickende Reichweite, kein ausgeführter Take-Profit. Die Stop-/Ziel-Reihenfolge '
             'wird konservativ mit OHLC-Kerzen und einem 120m-Diagnose-Trade gemessen. Ergebnisse sind '
             'deskriptiv, ohne Hypothesentest oder optimierte Parameter.','',
             'Unbestätigte oder gebrochene Zonen sind vollständige Teilmenge der Opportunities. '
             'Ein bestätigter Entry kann bereits zu spät stattfinden.','',
             'Originaldaten nur gelesen; vollständige Ereignisse in R16_PDH_PDL_EVENTS.csv.']
    OUT.mkdir(parents=True,exist_ok=False)
    events.to_csv(OUT/'R16_PDH_PDL_EVENTS.csv',index=False)
    (OUT/'R16_RESULTS.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,default=str)+'\n')
    (OUT/'R16_REPORT.md').write_text('\n'.join(lines)+'\n')
    print('R16 EXPLORATORY COMPLETE, events=',len(events))
    for x in output:
        f=x.get('structural_trade_120m',{})
        print(x['period'],x['level'],'touches',x['first_contacts'],'confirmed',x['confirmed'],
              'median_MFE_60m_bp',round(x['60m']['median_mfe_bp'],2) if x['60m']['median_mfe_bp'] is not None else None,
              'mean_net_trade_bp',round(f['mean_net14_bp'],2) if f else None)
    print('REPORT:',OUT/'R16_REPORT.md')
    print('RESULT:',OUT/'R16_RESULTS.json')
    print('EVENTS:',OUT/'R16_PDH_PDL_EVENTS.csv')

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('R16 FAIL CLOSED:',type(e).__name__,str(e),file=sys.stderr)
        sys.exit(1)
