#!/usr/bin/env python3
"""R11 BTC multi-timeframe exploratory study, version 1.0. No trading/orders.
Run --preflight first; --run only after archived design. Outputs exclusive directory.
"""
import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import brier_score_loss, log_loss

ROOT = Path.home()/"Dokumente/TradingLab/data/canonical/binance/perpetual/klines/BTC_USDT/5m"
OUT = Path.home()/"QuantResearch/R11_BTC_MTF/2024_train_2025_exploratory_v1"
FIRST = pd.Timestamp("2024-09-01",tz="UTC")
SPLIT = pd.Timestamp("2025-01-01",tz="UTC")
END = pd.Timestamp("2026-01-01",tz="UTC")
SEED = 20261115


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()


def load_data():
    files=sorted(ROOT.glob('BTC_USDT_5m_20??-??_v1.0.parquet'))
    files=[p for p in files if '2024-09'<=p.name.split('_5m_')[1][:7]<='2025-12']
    if len(files)!=16:raise ValueError('Expected exactly 16 monthly source files')
    fields=['open_time','close_time','open','high','low','close','volume_base','is_closed','exchange','market_type','contract_type','price_source','source_endpoint','timeframe']
    df=pd.concat([pd.read_parquet(p,columns=fields) for p in files],ignore_index=True)
    ts=pd.DatetimeIndex(df.open_time)
    expected=pd.date_range(FIRST,END,freq='5min',inclusive='left')
    if len(df)!=140256 or not ts.equals(expected) or not ts.is_unique:raise ValueError('Non-contiguous UTC series')
    if not bool((pd.DatetimeIndex(df.close_time)+pd.Timedelta(milliseconds=1)==ts+pd.Timedelta(minutes=5)).all()):raise ValueError('Candle closing timestamps inconsistent')
    if not bool(df.is_closed.all()):raise ValueError('Unclosed candles')
    for col,required in [('exchange','binance'),('market_type','perpetual'),('contract_type','linear'),('price_source','last_trade'),('source_endpoint','/fapi/v1/klines'),('timeframe','5m')]:
        if not bool(df[col].eq(required).all()):raise ValueError(f'Invalid {col}')
    ohlc=df[['open','high','low','close']].to_numpy(dtype=float)
    volume=df.volume_base.to_numpy(dtype=float)
    if not (np.isfinite(ohlc).all() and (ohlc>0).all() and np.isfinite(volume).all() and (volume>=0).all()):raise ValueError('Nonpositive/nonfinite prices or invalid volume')
    if not ((ohlc[:,1]>=np.maximum(ohlc[:,0],ohlc[:,3])).all() and (ohlc[:,2]<=np.minimum(ohlc[:,0],ohlc[:,3])).all()):raise ValueError('OHLC consistency fail')
    return ts+pd.Timedelta(minutes=5),ohlc[:,3],{p.name:sha256(p) for p in files}


def build_features(times,close):
    """Only actual closed 5m bars; coarser bars end at aligned UTC boundaries."""
    n=len(close)
    logp=np.log(np.asarray(close,dtype=float))
    if n!=len(times) or not np.isfinite(logp).all():raise ValueError('bad data')
    r=np.empty(n);r[:]=np.nan;r[1:]=np.diff(logp)
    # for decision j, historical sd is 288 5m returns strictly prior to current r[j]
    prior_sd=pd.Series(r,index=times).shift(1).rolling(288,min_periods=288).std(ddof=1).to_numpy()
    f={'5m':r/prior_sd}
    for minutes in (15,30,60):
        align=np.asarray((times.minute.to_numpy()%minutes==0)&(times.second.to_numpy()==0))
        aligned_times=times[align]
        aligned_logp=logp[align]
        series=pd.Series(np.diff(aligned_logp,prepend=np.nan),index=aligned_times)
        # Each return only available at the *end* of its full clock-aligned candle.
        latest=series.reindex(times,method='ffill').to_numpy()
        f[f'{minutes}m']=latest/(np.sqrt(minutes/5)*prior_sd)
    x=np.column_stack([f['5m'],f['60m'],f['15m'],f['30m']])
    future15=np.full(n,np.nan); future30=np.full(n,np.nan)
    future15[:-3]=logp[3:]-logp[:-3]
    future30[:-6]=logp[6:]-logp[:-6]
    return x,prior_sd,future15,future30


def extract_events(times,close):
    x,sd,f15,f30=build_features(times,close)
    sel=(np.isfinite(x).all(axis=1)&np.isfinite(f15)&np.isfinite(f30)&(x[:,0]<-0.5)&(np.abs(x[:,1])>0))
    # Avoid labels crossing either study partition. The split is a UTC-close boundary.
    complete15=times+pd.Timedelta(minutes=15)
    complete30=times+pd.Timedelta(minutes=30)
    train=sel&(times>=FIRST)&(times<SPLIT)&(complete30<=SPLIT)
    test=sel&(times>=SPLIT)&(times<END)&(complete30<=END)
    out={}
    for k,mask in [('2024_train_exploration',train),('2025_exploratory_temporal',test)]:
        out[k]={'times':times[mask],'X':x[mask],'forward15':f15[mask], 'forward30':f30[mask], 'y':(f15[mask]>0).astype(int), 'zero':int(np.count_nonzero(f15[mask]==0))}
    return out


def model():
    return make_pipeline(StandardScaler(),LogisticRegression(C=1.0,solver='lbfgs',max_iter=600,random_state=SEED))


def resample_daily_ci(t,diff,draws=5000,seed=SEED):
    """Paired 7-UTC-calendar-day circular moving blocks on daily sum/count."""
    dates=pd.DatetimeIndex(t).normalize()
    days=pd.date_range(SPLIT,END,freq='D',inclusive='left')
    dframe=pd.DataFrame({'day':dates,'diff':diff}).groupby('day').agg(s=('diff','sum'),n=('diff','size'))
    daily_s=dframe.s.reindex(days,fill_value=0).to_numpy(dtype=float)
    daily_n=dframe.n.reindex(days,fill_value=0).to_numpy(dtype=int)
    rng=np.random.default_rng(seed);n=len(days);blocks=math.ceil(n/7)
    deltas=np.empty(draws)
    for i in range(draws):
        starts=rng.integers(0,n,size=blocks)
        idx=np.concatenate([(s+np.arange(7))%n for s in starts])[:n]
        den=daily_n[idx].sum()
        deltas[i]=daily_s[idx].sum()/den if den else np.nan
    valid=deltas[np.isfinite(deltas)]
    if len(valid)!=draws:raise ValueError('Empty block bootstrap draw')
    return [float(v) for v in np.quantile(valid,[.025,.975])]


def description(e):
    prior=e['X'][:,1]
    res={'n':len(prior),'zero_15m':e['zero'],'base_positive_rate_15m':float(e['y'].mean()),'categories':{}}
    for name,mask in [('hour_up',prior>0),('hour_down',prior<0)]:
        n=int(mask.sum())
        res['categories'][name]={'n':n,'mean_next15m_bp':float(e['forward15'][mask].mean()*1e4) if n else None,'mean_next30m_bp':float(e['forward30'][mask].mean()*1e4) if n else None,'p_next15m_up':float(e['y'][mask].mean()) if n else None,'p_next30m_up':float((e['forward30'][mask]>0).mean()) if n else None}
    return res


def evaluate(events):
    a=events['2024_train_exploration'];b=events['2025_exploratory_temporal']
    if len(a['y'])<100 or len(b['y'])<100:raise ValueError('Insufficient events')
    maska=a['forward15']!=0;maskb=b['forward15']!=0
    xa=a['X'][maska];ya=a['y'][maska]
    xb=b['X'][maskb];yb=b['y'][maskb];tt=b['times'][maskb]
    if len(np.unique(ya))!=2:raise ValueError('One-class train')
    preds={}
    preds['constant_2024_base_rate']=np.full(len(yb),float(ya.mean()))
    for name,columns in [('A_5m',[0]),('B_5m_60m',[0,1]),('C_5m_60m_15m_30m',[0,1,2,3])]:
        clf=model();clf.fit(xa[:,columns],ya)
        preds[name]=np.clip(clf.predict_proba(xb[:,columns])[:,1],1e-7,1-1e-7)
    stats={name:{'brier':float(brier_score_loss(yb,p)),'logloss':float(log_loss(yb,p,labels=[0,1]))} for name,p in preds.items()}
    a_loss=(preds['A_5m']-yb)**2
    b_loss=(preds['B_5m_60m']-yb)**2
    c_loss=(preds['C_5m_60m_15m_30m']-yb)**2
    diffs={'B_minus_A_improvement':a_loss-b_loss,'C_minus_B_improvement':b_loss-c_loss}
    compare={k:{'mean_brier_reduction':float(v.mean()),'95pct_descriptive_daily_block_ci':resample_daily_ci(tt,v)} for k,v in diffs.items()}
    return {'2024_exploratory':description(a),'2025_exploratory':description(b),
            'model_scored_2025_nonzero':len(yb),'model_train_2024_nonzero':len(ya),
            'models_2025':stats,'incremental_2025':compare,
            'labels_zero_excluded_from_brier':{'2024':a['zero'],'2025':b['zero']},
            'notes':['2025 is not a pristine blind test; previously used history','Not a strategy PnL. Entry at historical close is not guaranteed','Overlapping 15m labels; 7-day block CI descriptive, not calibrated p-values']}


def synthetic():
    times=pd.date_range('2024-09-01 00:05',periods=1000,freq='5min',tz='UTC')
    rng=np.random.default_rng(411)
    prices=100*np.exp(np.cumsum(rng.normal(0,.001,len(times))))
    x,sd,_,_=build_features(times,prices)
    j=499 # at 17:40 UTC, latest complete 1h close at 17:00
    assert np.isfinite(x[j]).all()
    assert abs(x[j,1]-x[j-1,1]*sd[j-1]/sd[j])<1e-9 if times[j].minute%60!=0 else True
    # Changing all future prices must not change features at index j.
    mutated=prices.copy();mutated[j+1:]*=1.10
    xm,_,_,_=build_features(times,mutated)
    assert np.allclose(x[j],xm[j],atol=1e-11)
    # 15/30/1h features only advance at their actual completion times.
    for m,col in [(15,2),(30,3),(60,1)]:
        mask=np.asarray(times.minute%m!=0)
        shift=np.r_[False,mask[1:]]&mask
        # normalization changes with sd, therefore compare unnormalized numerator
        numer=x[:,col]*sd*np.sqrt(m/5)
        idx=np.flatnonzero(shift & np.isfinite(numer) & np.isfinite(np.roll(numer,1)))
        assert np.allclose(numer[idx],numer[idx-1])
    ev=extract_events(times,prices)
    for k,v in ev.items():
        times2=v['times']
        end=SPLIT if '2024' in k else END
        assert all(times2+pd.Timedelta(minutes=30)<=end)
    # Stable standard score: 288 historical returns before current bar.
    rr=np.diff(np.log(prices),prepend=np.nan)
    assert np.isclose(sd[j],np.std(rr[j-288:j],ddof=1),rtol=1e-8)
    # Paired day-block CI must reproduce a known constant paired delta.
    t=pd.date_range('2025-01-01',periods=60,freq='D',tz='UTC')
    ci=resample_daily_ci(t,np.ones(len(t))*.003,draws=60)
    assert np.allclose(ci,[.003,.003])
    return {'synthetic_no_future_data_in_features':True,'true_utc_coarse_bar_closures':True,'288_preceding_returns_no_overlap':True,'partition_no_crossing_labels':True,'paired_7day_bootstrap_known_delta':True}


def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight',action='store_true')
    mode.add_argument('--run',action='store_true')
    args=ap.parse_args()
    tests=synthetic()
    print('R11 SYNTHETIC:', 'PASS',json.dumps(tests,ensure_ascii=False))
    times,close,hashes=load_data()
    print('R11 DATA GATE: PASS, BTC, 140256 closed 5m candles, 16 files')
    if args.preflight:
        print('R11 PREFLIGHT ONLY. NO MARKET EVENT OR FUTURE RETURN MEASUREMENT.');return
    if OUT.exists():raise SystemExit(f'STOP: result directory already exists: {OUT}')
    if not OUT.parent.is_dir():OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(exist_ok=False)
    events=extract_events(times,close)
    result=evaluate(events)
    payload={'study':'R11 BTC MTF','date_utc':datetime.now(timezone.utc).isoformat(),'scope':'exploratory ONLY; no trading, no confirmatory inference',
             'source_sha256':hashes,'runner_sha256':sha256(Path(__file__)),
             'fixed_rule':'5m pullback r5 < -0.5x preceding 288 return sd; one 15m label; 30m descriptive; 15/30/60 completed UTC-aligned candles; 2024 fit, 2025 evaluate',
             'resampling':'paired UTC 7d circular moving-block; 5000; seed 20261115; descriptive CI only',**result}
    (OUT/'R11_RESULTS.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8')
    lines=['# R11 – BTC Multi-Timeframe, explorative Auswertung','','**Keine unabhängige Validierung oder handelbare Strategie.**','',
           '## Vorab festgelegte Bedingungen','2024 Modelltraining, 2025 zeitliche explorative Prüfung. Ein 5m-Rücksetzer: r5 < −0.5 × SD der 288 vorherigen 5m-Renditen. Die 15m/30m/1h-Merkmale verwenden nur tatsächlich abgeschlossene UTC-Kerzen. Prognoseziel: Vorzeichen der nächsten 15m-Rendite.','',
           '## Deskriptive Marktsituationen']
    for name in ['2024_exploratory','2025_exploratory']:
        d=result[name];lines.append(f'### {name}: {d["n"]} Rücksetzer')
        for group,st in d['categories'].items():
            lines.append(f'- {group}: n={st["n"]}, nächste 15m Ø {st["mean_next15m_bp"]:+.3f} bp, nächste 30m Ø {st["mean_next30m_bp"]:+.3f} bp, 15m-Aufwärtsanteil {st["p_next15m_up"]:.3%}')
    lines+=['','## Modellergebnisse: 2025 nur explorativ','']
    for name,d in result['models_2025'].items():lines.append(f'- {name}: Brier={d["brier"]:.8f}, LogLoss={d["logloss"]:.8f}')
    lines+=['','## Inkrementeller Brier-Gewinn (positiv = besser)','']
    for name,d in result['incremental_2025'].items():lines.append(f'- {name}: {d["mean_brier_reduction"]:+.8f}, deskriptives 95%-7-Tage-Blockintervall {d["95pct_descriptive_daily_block_ci"]}')
    lines+=['','## Interpretation','Keine Handelskosten berücksichtigt, kein Entry, kein Stop, kein PnL. Keine kalibrierten p-Werte; 2025 wurde in anderen Studien bereits betrachtet und ist kein unverbrauchter Blindtest. Nach Sichtung keine stillschweigende Änderung von Merkmalen, Schwellen oder Zeitfenstern.']
    (OUT/'R11_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('R11 EXPLORATORY COMPLETE | 2024 events=',result['2024_exploratory']['n'],'2025 events=',result['2025_exploratory']['n'])
    for key,val in result['incremental_2025'].items():print(key,val)
    print('REPORT:',OUT/'R11_REPORT.md')
    print('RESULT:',OUT/'R11_RESULTS.json')
    print('NO CONFIRMATORY CLAIM; NO NET PROFITABILITY CLAIM')


if __name__=='__main__':
    main()
