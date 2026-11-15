#!/usr/bin/env python3
"""R12 fixed three strategy BTC comparison. Offline, exploratory, NEVER orders.
Usage: python R12_3_Strategien_BTC_Explorativ.py --preflight | --run
"""
import argparse, hashlib, json, math, sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.home() / 'Dokumente/TradingLab/data/canonical/binance/perpetual/klines/BTC_USDT/5m'
DEST = Path.home() / 'QuantResearch/R12_BTC_3Strategien/Sep2024_Dec2025_v1'
PERIODS = [('2024_SepDec','2024-09-01','2025-01-01'),('2025_JanDec','2025-01-01','2026-01-01')]
EXPECTED_MONTHS = [f'{y}-{m:02}' for y,m0,m1 in [(2024,9,12),(2025,1,12)] for m in range(m0,m1+1)]
SEED = 20261115
NOTIONAL=100.0
INITIAL_EQUITY=10000.0
STOP_ATR=1.5
TAKE_ATR=3.0
MAX_HOLD=12
WARMUP=300
# Assumed, not actual exchange fees/funding payments (basis points per side)
SCENARIOS = {'base': {'fee_side':4.0,'slippage_side':2.0,'funding_reserve_roundtrip':2.0},
             'stress': {'fee_side':6.0,'slippage_side':4.0,'funding_reserve_roundtrip':4.0}}
STRATEGIES=('pullback','breakout','reversion')


def sha256(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()


def load_and_audit():
    parts=[]; hashes={}; issues=[]
    for ym in EXPECTED_MONTHS:
        p=ROOT/f'BTC_USDT_5m_{ym}_v1.0.parquet'
        if not p.is_file():raise RuntimeError('Missing raw source: '+str(p))
        hashes[p.name]=sha256(p)
        d=pd.read_parquet(p)
        required={'open_time','close_time','open','high','low','close','is_closed','exchange','market_type','contract_type','timeframe','price_source','source_endpoint','volume_base'}
        if required-set(d.columns):raise RuntimeError(f'{p.name}: missing {required-set(d.columns)}')
        if not (d['exchange'].eq('binance').all() and d['market_type'].eq('perpetual').all()
                and d['contract_type'].eq('linear').all() and d['timeframe'].eq('5m').all()
                and d['price_source'].eq('last_trade').all() and d['source_endpoint'].eq('/fapi/v1/klines').all()
                and d['is_closed'].all()):raise RuntimeError(f'{p.name}: provenance/closed bar mismatch')
        parts.append(d[['open_time','close_time','open','high','low','close','volume_base']])
    d=pd.concat(parts,ignore_index=True)
    t=pd.DatetimeIndex(d['open_time'])
    want=pd.date_range('2024-09-01','2026-01-01',freq='5min',tz='UTC',inclusive='left')
    if not t.equals(want):raise RuntimeError(f'Timestamp grid mismatch / duplicates: n={len(t)} expected={len(want)}')
    close_ts=pd.DatetimeIndex(d['close_time'])
    if not bool(((close_ts+pd.Timedelta(milliseconds=1))==(t+pd.Timedelta(minutes=5))).all()):
        raise RuntimeError('close_time UTC misalignment')
    prices=d[['open','high','low','close']].to_numpy(dtype=np.float64)
    vols=d['volume_base'].to_numpy(dtype=np.float64)
    if not (np.isfinite(prices).all() and (prices>0).all() and np.isfinite(vols).all() and (vols>=0).all()):
        raise RuntimeError('Invalid OHLCV')
    o,h,l,c=prices.T
    if not ((h>=np.maximum(o,c)).all() and (l<=np.minimum(o,c)).all() and (h>=l).all()):
        raise RuntimeError('OHLC inconsistency')
    return {'t':t,'o':o,'h':h,'l':l,'c':c,'hashes':hashes,'v':vols, 'issues':issues}


def features(a):
    o,h,l,c=a['o'],a['h'],a['l'],a['c']
    ema12=pd.Series(c).ewm(span=12,adjust=False).mean().to_numpy()
    ema48=pd.Series(c).ewm(span=48,adjust=False).mean().to_numpy()
    prev=np.r_[c[0],c[:-1]]
    tr=np.maximum.reduce([h-l,np.abs(h-prev),np.abs(l-prev)])
    atr=pd.Series(tr).rolling(14,min_periods=14).mean().to_numpy()
    prevmax=pd.Series(h).shift(1).rolling(12,min_periods=12).max().to_numpy()
    prevmin=pd.Series(l).shift(1).rolling(12,min_periods=12).min().to_numpy()
    # index j=signal-close, signal is available at open of j+1 only
    pp3=np.full(len(c),np.nan)
    pp3[4:]=np.log(c[3:-1]/c[:-4])  # past 3 bars from j-4 to j-1
    impulse=np.full(len(c),np.nan)
    impulse[6:]=np.log(c[6:]/c[:-6])
    r=np.diff(np.log(c))
    pastsd=np.full(len(c),np.nan)
    # last historical return is r[j-7], strictly before six-bar impulse [j-6,j]
    # r[k]=ln(C[k+1]/C[k]), so r[j-294:j-6] length 288
    rv=pd.Series(r).rolling(288,min_periods=288).std(ddof=1).to_numpy()
    pastsd[294:]=rv[287:len(c)-7]  # j=294 -> rv[287] covers r[0:288]
    z=np.abs(impulse)/(np.sqrt(6)*pastsd)
    z[~np.isfinite(z)]=np.nan
    sig={}
    sig['pullback']=np.where((ema12>ema48)&(pp3<=-0.001)&(c>o),1,
                             np.where((ema12<ema48)&(pp3>=0.001)&(c<o),-1,0))
    sig['breakout']=np.where((c>prevmax)&(c>o),1,np.where((c<prevmin)&(c<o),-1,0))
    sig['reversion']=np.where((z>=2)&(impulse>0),-1,np.where((z>=2)&(impulse<0),1,0))
    return sig,atr


def simulate(o,h,l,atr,signal,lo,hi,strategy):
    """A single isolated strategy ledger. No same-candle execution.
    Signals evaluated at end of j, entry next bar open j+1.
    Stops/targets tested using bars j+1..j+12, SL always wins ties.
    If no touch, time exit at open j+13 (strictly later).
    """
    trades=[]; j=max(lo+WARMUP,300)
    while j+13<hi:
        side=int(signal[j])
        if not side or not np.isfinite(atr[j]) or atr[j]<=0:
            j+=1;continue
        entry_i=j+1
        ent=float(o[entry_i]); d=float(atr[j])*STOP_ATR
        if not (ent>0 and d>0):j+=1;continue
        stop=ent-side*d
        target=ent+side*(TAKE_ATR*float(atr[j]))
        if stop<=0:j+=1;continue
        exit_i=j+13;exitprice=float(o[exit_i]); reason='time'
        for k in range(entry_i,j+13):
            op=float(o[k]);hi_k=float(h[k]);lo_k=float(l[k])
            if side==1:
                # Opening gap crossing stop (conservatively use worse gap open).
                if op<=stop:exit_i=k;exitprice=op;reason='stop_gap';break
                if lo_k<=stop:exit_i=k;exitprice=stop;reason='stop';break
                if op>=target:exit_i=k;exitprice=target;reason='target';break
                if hi_k>=target:exit_i=k;exitprice=target;reason='target';break
            else:
                if op>=stop:exit_i=k;exitprice=op;reason='stop_gap';break
                if hi_k>=stop:exit_i=k;exitprice=stop;reason='stop';break
                if op<=target:exit_i=k;exitprice=target;reason='target';break
                if lo_k<=target:exit_i=k;exitprice=target;reason='target';break
        # Position in units of BTC held fixed between entry and exit, notional set at entry.
        units=NOTIONAL/ent
        gross=units*side*(exitprice-ent)
        costs={}
        for name,p in SCENARIOS.items():
            slip_in=ent*(p['slippage_side']/10000)*side
            slip_out=exitprice*(p['slippage_side']/10000)*(-side)
            e_actual=ent+slip_in
            x_actual=exitprice+slip_out
            # Approximate notional fees on modeled execution prices.
            fees=(abs(units*e_actual)+abs(units*x_actual))*(p['fee_side']/10000)
            funding_buffer=NOTIONAL*p['funding_reserve_roundtrip']/10000
            costs[name]=float(units*side*(x_actual-e_actual)-fees-funding_buffer)
        trades.append({'strategy':strategy,'signal_index':j,'entry_index':entry_i,'exit_index':exit_i,
                       'side':side,'entry':ent,'exit':exitprice,'exit_reason':reason,
                       'gross_usdt':float(gross),'base_usdt':costs['base'],'stress_usdt':costs['stress'],
                       'risk_usdt':float(d*units),'holding_bars':int(exit_i-entry_i)})
        j=exit_i+1  # no same-bar re-entry; one position at a time
    return trades


def summaries(trades):
    if not trades:return {'trades':0,'status':'INSUFFICIENT_NO_TRADES'}
    a=np.array([t['base_usdt'] for t in trades]); b=np.array([t['stress_usdt'] for t in trades]);
    gross=np.array([t['gross_usdt'] for t in trades]);risk=np.array([t['risk_usdt'] for t in trades]);
    eq=INITIAL_EQUITY+np.r_[0,np.cumsum(a)]
    draw=eq/np.maximum.accumulate(eq)-1
    pf=float(a[a>0].sum()/-a[a<0].sum()) if (a<0).any() else None
    win=int((a>0).sum());loss=int((a<0).sum())
    return {'trades':len(a),'wins':win,'losses':loss,'win_rate':float(win/len(a)),
            'mean_gross_usdt':float(gross.mean()),'mean_base_usdt':float(a.mean()),
            'mean_stress_usdt':float(b.mean()),'mean_base_r':float(np.mean(a/risk)),
            'sum_base_usdt':float(a.sum()),'sum_stress_usdt':float(b.sum()),
            'fixed_equity_return_base_pct':float(100*a.sum()/INITIAL_EQUITY),
            'max_closed_trade_drawdown_base_pct':float(100*np.min(draw)),
            'profit_factor_base':pf,
            'profit_per_trade_bps_of_fixed_notional_base':float(a.mean()/NOTIONAL*10000),
            'mean_hold_bars':float(np.mean([t['holding_bars'] for t in trades])),
            'exit_reasons':{v:sum(t['exit_reason']==v for t in trades) for v in ('stop','stop_gap','target','time')}}


def block_ci(trades, t, lo, hi):
    # Daily realized P&L including zero-trade days. Resample pairs as 7-day blocks;
    # relative income / calendar day, does not confer p-values after strategy selection.
    daystart=t[lo].floor('D');dayend=(t[hi-1]+pd.Timedelta(minutes=5)).floor('D')
    days=pd.date_range(daystart,dayend,freq='D',inclusive='left')
    daily=np.zeros(len(days))
    for x in trades:
        day=t[x['exit_index']].floor('D')
        idx=int((day-daystart)/pd.Timedelta(days=1))
        if 0<=idx<len(daily):daily[idx]+=x['base_usdt']
    n=len(daily)
    if n<14:return None
    rng=np.random.default_rng(SEED)
    k=math.ceil(n/7)
    ci=[]
    for _ in range(2000):
        starts=rng.integers(0,n,size=k)
        ids=np.concatenate([(s+np.arange(7))%n for s in starts])[:n]
        ci.append(daily[ids].mean())
    return {'estimate_mean_base_usdt_per_day':float(daily.mean()),
            'ci95_descriptive_block_usdt_per_day':[float(v) for v in np.percentile(ci,[2.5,97.5])],
            'utc_days':int(n),'block_days':7,'draws':2000,'seed':SEED,
            'not_confirmatory':True}


def synthetic_tests():
    checks={}
    n=650
    x=np.linspace(100,105,n)
    data={'o':x.copy(),'h':x+0.5,'l':x-0.5,'c':x.copy()}
    entry_idx=311
    data['o'][entry_idx]=102.0
    data['h'][entry_idx]=103.0
    data['l'][entry_idx]=101.0
    a=np.zeros(n,dtype=np.int8)
    a[entry_idx-1]=1
    atr=np.ones(n)
    tr=simulate(data['o'],data['h'],data['l'],atr,a,0,n,'unit')
    checks['next_open_not_signal_close']=(len(tr)==1 and tr[0]['entry_index']==entry_idx
                                            and tr[0]['entry']==102.0)
    h=data['h'].copy();l=data['l'].copy()
    h[entry_idx]=110;l[entry_idx]=99.0
    both=simulate(data['o'],h,l,atr,a,0,n,'unit')
    checks['stop_first_if_same_bar_touches_both']=(len(both)==1 and both[0]['exit_reason']=='stop')
    # Gap below stop after entry, test separate from same-candle stop scenario.
    o=data['o'].copy();h=data['h'].copy();l=data['l'].copy()
    o[entry_idx]=102;h[entry_idx]=102.1;l[entry_idx]=101.8
    o[entry_idx+1]=90.0;h[entry_idx+1]=90.2;l[entry_idx+1]=89.8
    gap=simulate(o,h,l,atr,a,0,n,'unit')
    checks['gap_uses_adverse_open']=(len(gap)==1 and gap[0]['exit_reason']=='stop_gap'
                                     and gap[0]['exit']==90.0)
    rng=np.random.default_rng(20261115)
    c=np.exp(np.cumsum(rng.normal(0,.001,n)))*50000
    d={'o':c.copy(),'h':c*1.0005,'l':c*.9995,'c':c.copy()}
    sig1,at1=features(d);cut=400
    d2={k:v.copy() for k,v in d.items()}
    for k in d2:d2[k][cut+1:]*=1.3
    sig2,at2=features(d2)
    checks['no_future_in_signals_all_three']=all(np.array_equal(sig1[k][:cut+1],sig2[k][:cut+1]) for k in STRATEGIES)
    checks['no_future_in_atr']=np.allclose(at1[:cut+1],at2[:cut+1],equal_nan=True)
    boundary=np.zeros(n,dtype=np.int8);boundary[615]=1
    checks['no_cross_period_trade']=len(simulate(d['o'],d['h'],d['l'],at1,boundary,300,620,'unit'))==0
    checks['costs_deducted']=(len(tr)==1 and tr[0]['base_usdt']<tr[0]['gross_usdt']
                             and tr[0]['stress_usdt']<tr[0]['base_usdt'])
    checks['one_position_at_a_time']=all(x['entry_index']>tr[k-1]['exit_index'] for k,x in enumerate(tr) if k>0)
    # Verify CI against a deterministic 28-day sample with identical daily profits.
    t=pd.date_range('2024-09-01',periods=28*288,freq='5min',tz='UTC')
    toy=[{'exit_index':i*288+10,'base_usdt':2.0} for i in range(28)]
    ci=block_ci(toy,t,0,len(t))
    checks['7day_block_known_constant']=(ci is not None and ci['utc_days']==28
        and np.allclose(ci['ci95_descriptive_block_usdt_per_day'],[2,2]))
    return checks


def main():
    parser=argparse.ArgumentParser()
    g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--preflight',action='store_true');g.add_argument('--run',action='store_true')
    args=parser.parse_args()
    checks=synthetic_tests()
    print('R12 SYNTHETIK:', 'PASS' if all(checks.values()) else 'FAIL',json.dumps(checks,ensure_ascii=False))
    if not all(checks.values()):return 2
    a=load_and_audit()
    print('R12 BTC DATENGATE: PASS',len(a['t']),'5m-Kerzen',len(a['hashes']),'Originaldateien')
    if args.preflight:
        print('PREFLIGHT ONLY: keine Trades/Marktergebnisse berechnet');return 0
    if DEST.exists():
        print('STOP: Ergebnisordner existiert bereits:',DEST);return 3
    sig,atr=features(a)
    result={'study':'R12 BTC three fixed strategy classes','exploratory':True,'confirmatory':False,
            'research_periods':PERIODS,'inputs_sha256':a['hashes'],
            'code_sha256':sha256(Path(__file__).resolve()),'python':sys.version.split()[0],
            'pandas':pd.__version__,'numpy':np.__version__,
            'entry_rule':'signal at completed bar j, buy/sell next bar j+1 open',
            'exit_rule':'SL/TP first touch (SL wins ties), gap adverse open, otherwise j+13 open',
            'scenario_costs_bps':SCENARIOS,'trade_notional_usdt':NOTIONAL,
            'stop_ATR_multiple':STOP_ATR,'target_ATR_multiple':TAKE_ATR,'time_limit_5m_bars':MAX_HOLD,
            'funding_caveat':'Assumed per-roundtrip reserve, not actual settlement cash flows; indicative net only',
            'statistical_caveat':'descriptive paired-day block bootstrap, uncalibrated; three candidates and past dataset used',
            'results':{}}
    all_trades=[]
    for label,start,end in PERIODS:
        lo=int(a['t'].searchsorted(pd.Timestamp(start,tz='UTC')))
        hi=int(a['t'].searchsorted(pd.Timestamp(end,tz='UTC')))
        r={}
        for name in STRATEGIES:
            trades=simulate(a['o'],a['h'],a['l'],atr,sig[name],lo,hi,name)
            r[name]={'summary':summaries(trades),'daily_bootstrap':block_ci(trades,a['t'],lo,hi)}
            for x in trades:
                all_trades.append({'period':label,'entry_time_utc':str(a['t'][x['entry_index']]),
                                   'exit_time_utc':str(a['t'][x['exit_index']]),**x})
            m=r[name]['summary']
            print(f'{label} {name:10s} n={m["trades"]:4d} mean_base={m.get("mean_base_usdt",0):+.4f} USDT'
                  f' mean_stress={m.get("mean_stress_usdt",0):+.4f} sum_base={m.get("sum_base_usdt",0):+.2f}'
                  f' PF={m.get("profit_factor_base")} DD={m.get("max_closed_trade_drawdown_base_pct")}')
        result['results'][label]=r
    DEST.mkdir(parents=True,exist_ok=False)
    (DEST/'R12_RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    pd.DataFrame(all_trades).to_csv(DEST/'R12_TRADES.csv',index=False)
    lines=['# R12 – BTC: Drei feste Strategien (explorativ)','',
           '**Keine unabhängige Bestätigung; kein Beleg für reale Nettoprofitabilität.**',
           'Daten 2024/2025 waren Gegenstand früherer Forschung. Kosten sind Annahmen, Funding ist ein pauschaler Reserveposten.',
           'Keine Orders, keine Verbindung zu einer Börse, kein Freqtrade- oder Paper-Bot-Eingriff.','',
           '| Periode | Kandidat | Trades | Ø nach Basiskosten USDT | Ø Stresstest USDT | Summe Basiskosten USDT | PF | MaxDD geschlossene Trades % |',
           '|---|---|---:|---:|---:|---:|---:|---:|']
    for period,rr in result['results'].items():
        for name,z in rr.items():
            s=z['summary'];fmt=lambda v:(f'{v:.3f}' if isinstance(v,(float,int)) else '–')
            lines.append(f'| {period} | {name} | {s["trades"]} | {fmt(s.get("mean_base_usdt"))} | {fmt(s.get("mean_stress_usdt"))} | {fmt(s.get("sum_base_usdt"))} | {fmt(s.get("profit_factor_base"))} | {fmt(s.get("max_closed_trade_drawdown_base_pct"))} |')
    lines+=['','## Einschränkungen','Die Fills für Stop/TP stammen aus 5m OHLC, ohne Orderbuch; gleichzeitige Berührung führt pessimistisch zum Stop.',
            'Spread und Slippage werden pauschal modelliert; Funding ist eine pauschale Kostenreserve, keine historische Funding-Abrechnung.',
            'Drawdown wird auf geschlossenen Trades bestimmt, nicht auf Mark-to-Market-Equity.',
            'Die 7-Tage-Blockintervalle sind rein beschreibend, nicht multiple-test-kalibrierte Signifikanz.',
            'Keine Parametervariationen, keine Siegeroptimierung; spätere Bestätigung nur auf neuen, unberührten Daten.']
    (DEST/'R12_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('R12 EXPLORATIVE COMPLETE | KEINE LIVE ORDERS | KEIN BLINDTEST')
    print('REPORT:',DEST/'R12_REPORT.md')
    print('RESULT:',DEST/'R12_RESULTS.json')
    print('TRADES:',DEST/'R12_TRADES.csv')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('R12 FAIL CLOSED:',type(exc).__name__,str(exc));sys.exit(4)
