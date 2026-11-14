#!/usr/bin/env python3
"""R7 Phase B: offline synthetic-only diagnostic. No market data, requests, trading paths."""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm, binomtest
from scipy.signal import lfilter

SEED=20261114
TRAIN_START=pd.Timestamp('2026-04-01',tz='UTC')
TEST_START=pd.Timestamp('2027-01-01',tz='UTC')
END=pd.Timestamp('2027-04-01',tz='UTC')
IDX=pd.date_range(TRAIN_START, END, freq='5min',inclusive='left')
N=len(IDX)
TEST_N=2159
REPS=80
DRAWS=5000
BLOCK=7
LAG=7
# Hard-fixed simulation settings, independent of observed result:
SCENARIOS=('independent_null','shared_factor','btc_lead_weak')

# Precompute a single paired bootstrap calendar-index matrix and share across all scenarios.
def resample_index():
    rng=np.random.default_rng(SEED)
    out=np.empty((DRAWS,90),dtype=np.int16)
    for i in range(DRAWS):
        ix=[]
        while len(ix)<90:
            j=int(rng.integers(0,90-BLOCK+1))
            ix.extend(range(j,j+BLOCK))
        out[i]=ix[:90]
    return out
BIX=resample_index()

def generate(scenario, rep):
    rng=np.random.default_rng(SEED+1701+rep*17)
    # Persistent log-volatilities (GARCH-like clustering, not an estimated GARCH process).
    # Common factor and idiosyncratic vol components: stationary AR(1).
    z=rng.standard_normal((N,7))
    v=np.column_stack([
        lfilter([sigma],[1,-phi],z[:,j])
        for j,(phi,sigma) in enumerate(((.997,.06),(.995,.05),(.995,.05),(.995,.05)))
    ])
    if scenario=='independent_null':
        # BTC and ETH/SOL share neither volatility nor return innovations.
        bvol=v[:,1]
        evol=.75*v[:,2]+.35*v[:,3]
        svol=.7*v[:,3]+.3*v[:,2]
        rb=z[:,4]
        re=.2*z[:,5]+.98*z[:,6]
        rs=.25*z[:,5]+np.sqrt(1-.25**2)*z[:,6] # shared ETH/SOL shocks
    else:
        bvol=.75*v[:,0]+.55*v[:,1]
        evol=.70*v[:,0]+.48*v[:,2]
        svol=.75*v[:,0]+.45*v[:,3]
        # Common return innovations, but no BTC-specific lag under shared_factor.
        rb=.4*z[:,4]+np.sqrt(.84)*z[:,5]
        re=.35*z[:,4]+np.sqrt(1-.35**2)*z[:,6]
        rs=.38*z[:,4]+np.sqrt(1-.38**2)*z[:,3]  # caveat correlated vol/return shock, valid DGP
        if scenario=='btc_lead_weak':
            # Lagged BTC-specific vol shock affects later ETH conditional log-vol.
            # Lag 12 bars, beta fixed at 0.10; signal strength NOT tuned on results.
            evol=evol+.10*np.roll(v[:,1],12)
            evol[:12]=.70*v[:12,0]+.48*v[:12,2]
    r=pd.DataFrame({'BTC':.0012*np.exp(np.clip(bvol,-4,4))*rb,
                    'ETH':.0013*np.exp(np.clip(evol,-4,4))*re,
                    'SOL':.0015*np.exp(np.clip(svol,-4,4))*rs}, index=IDX)
    sq=r*r
    frame=pd.DataFrame(index=IDX)
    for market in ('ETH','SOL','BTC'):
        for w in (12,288,2016):
            frame[f'{market}_{w}']=np.log(sq[market].rolling(w).mean()+1e-12)
    frame['y']=np.log(sq['ETH'].rolling(12).sum().shift(-12)+1e-12)
    frame=frame.loc[frame.index.minute==55].dropna()
    return frame

def forecast(f):
    bcols=[f'{m}_{k}' for m in ('ETH','SOL') for k in (12,288,2016)]
    mcols=bcols+[f'BTC_{k}' for k in (12,288,2016)]
    out=[]
    for start,stop in (('2027-01-01','2027-02-01'),('2027-02-01','2027-03-01'),('2027-03-01','2027-04-01')):
        a=pd.Timestamp(start,tz='UTC');b=pd.Timestamp(stop,tz='UTC')
        # Label +65min after forecast hh:55. Training labels known at midnight.
        train=f.loc[(f.index+pd.Timedelta(minutes=65)<=a)]
        test=f.loc[(f.index>=a)&(f.index<b)&(f.index+pd.Timedelta(minutes=65)<=END)]
        preds=[]
        for cols in (bcols,mcols):
            x=np.column_stack([np.ones(len(train)),train[cols].to_numpy()])
            y=train['y'].to_numpy()
            coef=np.linalg.lstsq(x,y,rcond=None)[0]
            tx=np.column_stack([np.ones(len(test)),test[cols].to_numpy()])
            preds.append(tx@coef)
        out.append(pd.DataFrame({'y':test['y'].to_numpy(),'B2':preds[0],'M2':preds[1]},index=test.index))
    p=pd.concat(out)
    assert len(p)==TEST_N and p.index.is_unique and np.isfinite(p.to_numpy()).all()
    assert p.index[0]==pd.Timestamp('2027-01-01 00:55',tz='UTC')
    assert p.index[-1]==pd.Timestamp('2027-03-31 22:55',tz='UTC')
    return p

def summarize(p):
    a=(p.y-p.B2).pow(2)
    b=(p.y-p.M2).pow(2)
    daily=pd.DataFrame({'a':a.to_numpy(),'b':b.to_numpy()},index=p.index.floor('D')).groupby(level=0).sum()
    assert len(daily)==90 and sum(daily.a>0)==90
    x=daily.a.to_numpy();y=daily.b.to_numpy()
    ci=100*((x[BIX].sum(axis=1)-y[BIX].sum(axis=1))/x[BIX].sum(axis=1))
    lo,hi=np.percentile(ci,[2.5,97.5])
    counts=p.index.floor('D').value_counts().sort_index().to_numpy()
    d=(x-y)/counts
    c=d-d.mean();n=len(d)
    v=c@c/n
    for lag in range(1,LAG+1):v+=2*(1-lag/(LAG+1))*(c[lag:]@c[:-lag])/n
    z=float(d.mean()/np.sqrt(v/n)) if v>0 else np.nan
    pval=float(norm.sf(z)) if np.isfinite(z) else np.nan
    gain=float(100*(a.mean()-b.mean())/a.mean())
    # conservative compound gate from version 0.2, not sufficient validation per se
    supported=bool(gain>0 and lo>0 and pval<.05)
    return dict(gain=gain,lo=float(lo),hi=float(hi),p_hac=pval,supported=supported)

def main():
    outputs={}
    for scenario in SCENARIOS:
        v=[]
        for i in range(REPS):
            v.append(summarize(forecast(generate(scenario,i))))
        k=sum(t['supported'] for t in v)
        ci=binomtest(k,REPS).proportion_ci(confidence_level=.95,method='exact')
        outputs[scenario]={
            'n':REPS,'compound_gate_positives':k,'compound_gate_rate':k/REPS,
            'exact_binomial_95pct_rate_ci':[ci.low,ci.high],
            'mean_gain_pct':float(np.mean([t['gain'] for t in v])),
            'median_gain_pct':float(np.median([t['gain'] for t in v])),
            'pct_negative_gain':float(np.mean([t['gain']<=0 for t in v])),
            'mean_ci_lower':float(np.mean([t['lo'] for t in v])),
            'p_hac_lt_05_rate':float(np.mean([t['p_hac']<.05 for t in v])),
        }
        print(scenario,outputs[scenario],flush=True)
    manifest={
        'kind':'SYNTHETIC_ONLY_PHASE_B_NOT_MARKET_EVIDENCE',
        'seed':SEED,'scenarios':SCENARIOS,'replications_per_scenario':REPS,
        'bootstrap_draws':DRAWS,'block_days':BLOCK,'hac_daily_lags':LAG,
        'forecast_count_each':TEST_N,
        'simulation_design':{
            'independent_null':'Independent BTC volatility and returns; ETH/SOL joint shocks',
            'shared_factor':'Common persistent stochastic log-vol factor and return shocks; no imposed lagged BTC-specific effect',
            'btc_lead_weak':'Shared factor plus 12-bar lagged BTC-idiosyncratic logvol loading 0.10 in ETH',
            'limitation':'Shared-factor scenario may legitimately contain conditional BTC predictive signal; its positive rate is NOT an empirical type-I error rate.',
        },
        'result':outputs,
        'decision':'Diagnostic only. No Phase C authorization, no claim of general nominal coverage.'
    }
    path=Path('/mnt/data/R7_synthetik_realistische_nullkalibrierung_resultat.json')
    path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print('RESULT_FILE',path)
if __name__=='__main__':main()
