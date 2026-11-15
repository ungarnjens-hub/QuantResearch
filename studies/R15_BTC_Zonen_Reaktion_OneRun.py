#!/usr/bin/env python3
"""R15: explorative BTC zone-touch vs confirmed-reaction study. Read only.

Requires the frozen R12 market loader in ~/QuantResearch-Git/studies/ and
unmodified Binance USD-M perpetual 5-minute canonical parquet files.
No orders, no productive services, no parameter search.  See accompanying plan.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path.home()
REFERENCE = HOME / 'QuantResearch-Git/studies/R12_3_Strategien_BTC_Explorativ.py'
OUTPUT = HOME / 'QuantResearch/R15_BTC_ZonenReaktion/Sep2024_Dec2025_v1'
EXPECTED_R12_SHA256 = '7c434924f85cdd94fb09438dbf033cb797a946bc93ff8f3bdb82a9850839609d'
LOOKBACK_DAYS = (3, 14, 21)
ZONE_HALF_WIDTH = 0.0015  # +/- 15bp around prior rolling high/low
ATR_LEN = 14
STOP_BUFFER_ATR = .25
CONFIRM_BARS = 3  # 5m closed candles strictly after touch
EXIT_BARS = 24  # 120m
RR = 2.0
COST_BASE_BP = 14.0
COST_STRESS_BP = 24.0
COOLDOWN_BARS = 24
SEED = 20261115


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def data():
    if not REFERENCE.is_file() or digest(REFERENCE) != EXPECTED_R12_SHA256:
        raise RuntimeError('Frozen R12 loader missing or modified')
    spec = importlib.util.spec_from_file_location('r15_frozen_r12', REFERENCE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.load_and_audit()


def make_zones(a):
    """Build each UTC day's zones from completed PREVIOUS UTC days only.
    Outputs 6 levels/day: 3,14,21-day highs and lows (no fitted pivots).
    """
    t = a['t']; h = a['h']; l = a['l']
    days = pd.DatetimeIndex(t.floor('D').unique())
    starts = np.searchsorted(t.asi8, days.asi8)
    ends = np.r_[starts[1:], len(t)]
    high = np.array([h[i:j].max() for i, j in zip(starts, ends)])
    low = np.array([l[i:j].min() for i, j in zip(starts, ends)])
    zones = {}
    for d in range(max(LOOKBACK_DAYS), len(days)):
        rows = []
        for lb in LOOKBACK_DAYS:
            rows += [('support', lb, float(low[d-lb:d].min())),
                     ('resistance', lb, float(high[d-lb:d].max()))]
        # Do not deduplicate different origins; only choose one event per touch.
        zones[d] = rows
    return days, starts, ends, zones


def atr_series(a):
    o, h, l, c = (a[k] for k in ('o','h','l','c'))
    prev = np.r_[c[0],c[:-1]]
    tr = np.maximum.reduce((h-l, np.abs(h-prev),np.abs(l-prev)))
    return pd.Series(tr).rolling(ATR_LEN,min_periods=ATR_LEN).mean().to_numpy()


def simulate_trade(o, h, l, entry_idx, side, stop, target, last_exclusive):
    """Next-open entry, chronological first touch, stop wins OHLC collision.
    Adverse stop gap at open; favorable TP gap fills conservatively at TP.
    Timed exit is the open after the completed observation window.
    """
    if entry_idx+EXIT_BARS >= last_exclusive:
        raise ValueError('Trade crosses partition')
    entry = float(o[entry_idx])
    risk = side*(entry-stop)
    if risk <= 0 or stop <= 0 or target <= 0 or side*(target-entry) <= 0:
        raise ValueError('Invalid trade geometry')
    hit = 'time'; exi = entry_idx+EXIT_BARS; xp=float(o[exi]); collision=False
    for k in range(entry_idx,entry_idx+EXIT_BARS):
        op, hi, lo = float(o[k]),float(h[k]),float(l[k])
        sg = (op<=stop) if side==1 else (op>=stop)
        tg = (op>=target) if side==1 else (op<=target)
        sh = (lo<=stop) if side==1 else (hi>=stop)
        th = (hi>=target) if side==1 else (lo<=target)
        if sg: hit='stop_gap'; exi=k;xp=op;break
        if tg: hit='target_gap';exi=k;xp=target;break
        if sh and th:
            hit='ambiguous_stop_first';exi=k;xp=stop;collision=True;break
        if sh: hit='stop';exi=k;xp=stop;break
        if th: hit='target';exi=k;xp=target;break
    gross=side*(xp/entry-1)*10000
    return {'exit_index':int(exi),'exit_reason':hit,
            'ambiguous':bool(collision),'exit_bars':int(exi-entry_idx),
            'risk_bp':float(risk/entry*10000),
            'gross_bp':float(gross),'net_base_bp':float(gross-COST_BASE_BP),
            'net_stress_bp':float(gross-COST_STRESS_BP)}


def synthetic_tests():
    o=np.full(60,100.);h=o.copy();l=o.copy()
    # Next-open target / stop / ambiguity / adverse gap / time.
    h[5]=103
    assert simulate_trade(o,h,l,5,1,99,102,60)['exit_reason']=='target'
    l[5]=98
    assert simulate_trade(o,h,l,5,1,99,102,60)['exit_reason']=='ambiguous_stop_first'
    h[5]=100;l[5]=100;o[6]=97;h[6]=97;l[6]=97
    assert simulate_trade(o,h,l,5,1,99,102,60)['exit_reason']=='stop_gap'
    o.fill(100);h.fill(100);l.fill(100)
    assert simulate_trade(o,h,l,5,-1,101,98,60)['exit_reason']=='time'
    l[5]=97
    assert simulate_trade(o,h,l,5,-1,101,98,60)['exit_reason']=='target'
    try: simulate_trade(o,h,l,40,1,99,102,60)
    except ValueError: pass
    else: raise AssertionError('Partition cross must fail')
    # Daily barriers see prior day only; future-day OHLC cannot update them.
    days=pd.date_range('2025-01-01', periods=23, freq='D',tz='UTC')
    t=pd.date_range(days[0],periods=23*288,freq='5min')
    temp={'t':t,'h':np.full(len(t),101.),'l':np.full(len(t),99.)}
    _,_,_,z1=make_zones(temp)
    temp['h'][-1]=10000
    _,_,_,z2=make_zones(temp)
    assert z1[21]==z2[21]
    assert all(len(v)==6 for v in z1.values())
    print('R15 SYNTHETIK PASS: next-open, target, collision, gap, expiry, partition, historic zones')


def summarize(g):
    if g.empty:return {'n':0}
    return {'n':int(len(g)),'mean_net_bp':float(g.net_base_bp.mean()),
            'mean_gross_bp':float(g.gross_bp.mean()),
            'mean_stress_bp':float(g.net_stress_bp.mean()),
            'target_pct':float(g.exit_reason.isin(('target','target_gap')).mean()*100),
            'stop_pct':float(g.exit_reason.isin(('stop','stop_gap','ambiguous_stop_first')).mean()*100),
            'time_pct':float((g.exit_reason=='time').mean()*100),
            'ambiguous_pct':float(g.ambiguous.mean()*100),
            'median_risk_bp':float(g.risk_bp.median()),
            'mean_hold_bars':float(g.exit_bars.mean()),
            'profit_factor':float(g.loc[g.net_base_bp>0,'net_base_bp'].sum() / -g.loc[g.net_base_bp<0,'net_base_bp'].sum()) if (g.net_base_bp<0).any() else None}


def bootstrap_paired(events):
    if events.empty:return None
    d=events.copy();d['day']=pd.to_datetime(d.touch_time_utc,utc=True).dt.floor('D')
    # A non-confirmation counts as 0 return, explicitly an opportunity not a trade.
    d['delta']=d.confirmed_net_opportunity_bp-d.touch_net_bp
    by=d.groupby('day').agg(delta=('delta','sum'),count=('delta','size'))
    idx=pd.date_range(by.index.min(),by.index.max(),freq='D')
    by=by.reindex(idx,fill_value=0)
    a=by.delta.to_numpy();b=by['count'].to_numpy();n=len(a)
    if n<14 or b.sum()<20:return None
    rng=np.random.default_rng(SEED); samples=[]
    for _ in range(1000):
        picks=rng.integers(0,n,size=math.ceil(n/7))
        ids=np.concatenate([(s+np.arange(7))%n for s in picks])[:n]
        if b[ids].sum(): samples.append(float(a[ids].sum()/b[ids].sum()))
    return {'difference_opportunity_bp':float(a.sum()/b.sum()),
            'descriptive_ci95_bp':[float(v) for v in np.percentile(samples,[2.5,97.5])],
            'resamples':1000,'block_calendar_days':7,'calibration':'not confirmatory'}


def research(a):
    t=a['t'];o=a['o'];h=a['h'];l=a['l'];c=a['c'];N=len(t)
    days,starts,ends,zones=make_zones(a)
    atr=atr_series(a)
    periods=[('2024_SepDec',pd.Timestamp('2024-09-01',tz='UTC'),pd.Timestamp('2025-01-01',tz='UTC')),
             ('2025_JanDec',pd.Timestamp('2025-01-01',tz='UTC'),pd.Timestamp('2026-01-01',tz='UTC'))]
    results=[]; all_events=[]
    for name,begin,end in periods:
        lo=int(t.searchsorted(begin)); hi=int(t.searchsorted(end));
        next_allowed=lo
        for d,(dstart,dend) in enumerate(zip(starts,ends)):
            if d not in zones or dstart>=hi or dend<=lo:continue
            start=max(dstart,lo+1,next_allowed);stop=min(dend,hi-EXIT_BARS-1)
            for j in range(start,stop):
                if j<next_allowed:continue
                if not np.isfinite(atr[j]) or atr[j]<=0:continue
                candidates=[]
                for kind,lookback,level in zones[d]:
                    lower=level*(1-ZONE_HALF_WIDTH);upper=level*(1+ZONE_HALF_WIDTH)
                    # Approach from outside the price band; touch must reach band.
                    if kind=='support' and c[j-1]>upper and l[j]<=upper and h[j]>=lower:
                        candidates.append((abs(c[j-1]/level-1),-lookback,kind,lookback,level,lower,upper))
                    if kind=='resistance' and c[j-1]<lower and h[j]>=lower and l[j]<=upper:
                        candidates.append((abs(c[j-1]/level-1),-lookback,kind,lookback,level,lower,upper))
                if not candidates:continue
                # Frozen tie rule: nearest initial distance, then longest lookback.
                _,_,kind,lookback,level,lower,upper=min(candidates)
                side=1 if kind=='support' else -1
                touch_entry=j+1
                stop_touch=(l[j]-.25*atr[j]) if side==1 else (h[j]+.25*atr[j])
                risk_touch=side*(float(o[touch_entry])-stop_touch)
                valid_touch=(risk_touch>0 and stop_touch>0)
                if not valid_touch:continue
                tp_touch=float(o[touch_entry])+side*RR*risk_touch
                instant=simulate_trade(o,h,l,touch_entry,side,stop_touch,tp_touch,hi)
                # Reaction requires confirmation close 1..3 bars after touch, no zone break before.
                confirmation=None;flag='no_confirmation'
                for k in range(j+1,min(j+CONFIRM_BARS+1,hi-EXIT_BARS-1)):
                    # A close beyond the opposite band cancels the reaction thesis.
                    if (side==1 and c[k]<lower) or (side==-1 and c[k]>upper):
                        flag='zone_broken';break
                    good=(c[k]>upper and c[k]>o[k] and c[k]>c[k-1]) if side==1 else (c[k]<lower and c[k]<o[k] and c[k]<c[k-1])
                    if good:
                        confirmation=k;flag='confirmed';break
                chosen=None;net_confirm=0.;conf_risk=np.nan
                if confirmation is not None:
                    entry=confirmation+1
                    stop_conf=(np.min(l[j:confirmation+1])-.25*atr[confirmation]) if side==1 else (np.max(h[j:confirmation+1])+.25*atr[confirmation])
                    risk=side*(float(o[entry])-stop_conf)
                    if risk>0 and stop_conf>0 and entry+EXIT_BARS<hi:
                        tp=float(o[entry])+side*RR*risk
                        chosen=simulate_trade(o,h,l,entry,side,stop_conf,tp,hi)
                        net_confirm=chosen['net_base_bp'];conf_risk=chosen['risk_bp']
                    else:flag='untradeable_confirmation'
                tr60=float(side*(c[j]/c[j-12]-1)*10000) if j>=12 else float('nan')
                row={'period':name,'touch_time_utc':str(t[j]),'touch_idx':j,
                     'kind':kind,'side':side,'lookback_days':lookback,'zone_mid':level,
                     'prior_trend_bp_in_side':tr60,'atr_pct_at_touch':float(atr[j]/c[j]*100),
                     'touch_entry_utc':str(t[touch_entry]),'touch_net_bp':instant['net_base_bp'],
                     'touch_exit_reason':instant['exit_reason'],'touch_risk_bp':instant['risk_bp'],
                     'confirmation_state':flag,'confirmed':chosen is not None,
                     'confirmation_utc':str(t[confirmation]) if chosen is not None else '',
                     'confirmed_entry_utc':str(t[confirmation+1]) if chosen is not None else '',
                     'confirmed_net_bp':net_confirm if chosen is not None else np.nan,
                     'confirmed_net_opportunity_bp':net_confirm,
                     'confirmed_exit_reason':chosen['exit_reason'] if chosen is not None else 'no_trade',
                     'confirmed_risk_bp':conf_risk}
                all_events.append(row)
                next_allowed=j+COOLDOWN_BARS+1
        events=pd.DataFrame([x for x in all_events if x['period']==name])
        if events.empty:raise RuntimeError('No zone contacts in '+name)
        trades=events[events.confirmed].copy()
        a0=pd.DataFrame({'net_base_bp':events.touch_net_bp,'net_stress_bp':events.touch_net_bp-10,
                         'gross_bp':events.touch_net_bp+COST_BASE_BP,
                         'exit_reason':events.touch_exit_reason,
                         'risk_bp':events.touch_risk_bp,'exit_bars':0,'ambiguous':False})
        a1=pd.DataFrame({'net_base_bp':trades.confirmed_net_bp,
                         'net_stress_bp':trades.confirmed_net_bp-10,
                         'gross_bp':trades.confirmed_net_bp+COST_BASE_BP,
                         'exit_reason':trades.confirmed_exit_reason,
                         'risk_bp':trades.confirmed_risk_bp,'exit_bars':0,'ambiguous':False})
        z={'period':name,'zone_contact_opportunities':int(len(events)),
           'confirmation_rate_pct':float(100*len(trades)/len(events)),
           'no_trade_count':int(len(events)-len(trades)),
           'touch_immediate':summarize(a0),'confirmed_trades':summarize(a1),
           'confirmed_per_opportunity_net_bp':float(events.confirmed_net_opportunity_bp.mean()),
           'matched_paired_opportunity_bootstrap':bootstrap_paired(events),
           'by_zone_lookback_descriptive':[],'by_side_descriptive':[]}
        for lb,g in events.groupby('lookback_days'):
            tr=g[g.confirmed]
            z['by_zone_lookback_descriptive'].append({'days':int(lb),'opportunities':len(g),'confirmed':len(tr),
                    'net_confirm_mean_bp':float(tr.confirmed_net_bp.mean()) if len(tr) else None})
        for side,g in events.groupby('side'):
            tr=g[g.confirmed]
            z['by_side_descriptive'].append({'side':'long' if side==1 else 'short','opportunities':len(g),'confirmed':len(tr),
                    'net_confirm_mean_bp':float(tr.confirmed_net_bp.mean()) if len(tr) else None})
        results.append(z)
        print(f"R15 {name}: contacts={len(events)} confirmed={len(trades)} "
              f"touch={events.touch_net_bp.mean():+.2f}bp confirm_trades="
              f"{trades.confirmed_net_bp.mean() if len(trades) else float('nan'):+.2f}bp "
              f"confirm_per_contact={events.confirmed_net_opportunity_bp.mean():+.2f}bp")
    return results,pd.DataFrame(all_events)


if __name__ == '__main__':
    import sys
    try:
        synthetic_tests()
        if sys.argv[1:] not in (['--preflight'],['--run']):
            raise ValueError('Usage: python R15_BTC_Zonen_Reaktion_OneRun.py --preflight | --run')
        if sys.argv[1:] == ['--run'] and OUTPUT.exists():
            raise RuntimeError('FAIL CLOSED: result folder already exists')
        a=data()
        print(f"R15 DATA GATE PASS: {len(a['t'])} candles, {len(a['hashes'])} BTC source files")
        if sys.argv[1:] == ['--preflight']:
            print('R15 PREFLIGHT ONLY: no market result calculated')
        else:
            result,events=research(a)
            OUTPUT.mkdir(parents=True,exist_ok=False)
            events.to_csv(OUTPUT/'R15_ZONE_EVENTS.csv',index=False)
            report={'study':'R15 exploratory zone reaction',
                    'rules':{'lookbacks_utc_days':LOOKBACK_DAYS,'band_halfwidth_bp':ZONE_HALF_WIDTH*10000,
                             'confirm_next_closed_bars':CONFIRM_BARS,'stop_buffer_atr':STOP_BUFFER_ATR,
                             'target_R':RR,'max_hold_5min_bars':EXIT_BARS,
                             'cooldown_5min_bars':COOLDOWN_BARS,
                             'cost_roundtrip_base_bp':COST_BASE_BP,'cost_stress_bp':COST_STRESS_BP},
                    'market_hashes':a['hashes'],'r12_source_hash':EXPECTED_R12_SHA256,
                    'status':'exploratory; previously investigated 2024/2025; NOT confirmed',
                    'results':result}
            (OUTPUT/'R15_RESULTS.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
            lines=['# R15 BTC: Vorher bekannte Preiszonen und Reaktionsbestätigung','',
                   '**Explorativ; kein nachgewiesener Handelsvorteil.**','',
                   'Vergleich: Eintritt bei zonalem Kontakt vs Einstieg erst nach bestätigter Kursreaktion.',
                   'Kein vollständiger portfoliogerechter Backtest; overlapping positions möglich.',
                   'Über 3,14,21 Tage abgeleitete Hoch/Tief-Bänder waren bereits am Tagesbeginn bekannt.',
                   'Beim fehlenden Bestätigungssignal wird null Gewinn und null Kosten pro Gelegenheit verbucht.',
                   'Kosten sind konservative Modellannahmen; tatsächliche Funding-Flüsse fehlen.','',
                   '| Zeitraum | Zonenberührungen | Bestätigt | sofort Ø bp | bestätigt Ø bp/Trade | bestätigt Ø bp/Gelegenheit |',
                   '|---|---:|---:|---:|---:|---:|']
            for z in result:
                lines.append(f"| {z['period']} | {z['zone_contact_opportunities']} | {z['confirmed_trades']['n']} | {z['touch_immediate']['mean_net_bp']:.2f} | {z['confirmed_trades'].get('mean_net_bp',float('nan')):.2f} | {z['confirmed_per_opportunity_net_bp']:.2f} |")
            lines.extend(['','## Grenzen','',
                          '- Daten bereits zuvor erforscht, kein unverbrauchter Blindtest.',
                          '- Rückblicke 3/14/21 Tage sind vorab festgelegt, keine nachträgliche Siegerauswahl.',
                          '- Nicht bestätigte Kontakte gelten als ausgelassene Gelegenheit, nicht als Beweis für Unbrauchbarkeit.',
                          '- Intrabar Stop-/Ziel-Kollision konservativ zugunsten Stop aufgelöst.',
                          '- Keine Freqtrade-Paper-Order, kein produktives System berührt.',
                          '- Preiszone ist historische Hoch/Tief-Band-Operationalisierung, keine bewiesene institutionelle Orderzone.',
                          '- Die untersuchten Kontakte sind wegen Cooldown keine vollständige Aufzählung aller Zonenereignisse.'])
            (OUTPUT/'R15_REPORT.md').write_text('\n'.join(lines)+'\n')
            print('R15 EXPLORATORY COMPLETE, FILES:',OUTPUT/'R15_REPORT.md',OUTPUT/'R15_RESULTS.json',OUTPUT/'R15_ZONE_EVENTS.csv',sep='\n')
    except Exception as e:
        print('R15 FAIL CLOSED:',type(e).__name__,str(e))
        sys.exit(4)
