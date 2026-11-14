#!/usr/bin/env python3
"""R7 phase B: pure synthetic hourly reduced-form nested-model inference audit.
No market access, filesystem reads, network, orders or trading systems.
Ex ante scripted scenarios and rules. Results are diagnostic, never market evidence.
"""
import json
from pathlib import Path
import numpy as np
from scipy.stats import norm, binomtest

SEED=20261114
REPS=300
HOURS_TRAIN=24*275
HOURS_TEST=2159
TOTAL=HOURS_TRAIN+HOURS_TEST
REFITS=(0, 744, 1416) # Jan 31d, Feb 28d, Mar 31d (last 23h)
BLOCK_DAYS=7
BOOT=1000
HAC_LAGS=7
SCENARIOS=('independent_null','correlated_null','weak_added_signal')

# Set in source before any results are calculated.
# Six baseline predictors: 3 ETH / 3 SOL; three extra BTC predictors.
# All values are known at forecast time; response is generated afterwards.

def generate(rep, scenario):
    rng=np.random.default_rng(SEED+1009*rep+{'independent_null':0,'correlated_null':1,'weak_added_signal':2}[scenario]*1000000)
    e=rng.standard_normal((TOTAL+300,13))
    f=np.zeros((TOTAL+300,4),float)
    for j in range(4):
        for t in range(1,len(f)):
            f[t,j]=(.965 if j==0 else .90)*f[t-1,j]+(.23 if j==0 else .42)*e[t,j]
    f=f[300:]; e=e[300:]
    x=np.zeros((TOTAL,9))
    # Correlated NULL: all predictors share common factor, but BTC coefficients = 0 exactly.
    # Independent NULL: BTC from independent shocks, no signal.
    for j in range(6):
        x[:,j] = (.60*f[:,0] + .30*f[:,1+j%3]+ .42*e[:,4+j]) if scenario!='independent_null' else (.32*f[:,1+j%3]+ .70*e[:,4+j])
    for j in range(3):
        x[:,6+j]=(.66*f[:,0]+.22*f[:,1+j]+.52*e[:,j+8]) if scenario!='independent_null' else (.55*f[:,3]+.73*e[:,j+8])
    # Persistent, heteroskedastic forecast error innovation; future y is not an input.
    v=np.zeros(TOTAL)
    for t in range(1,TOTAL):
        v[t]=.975*v[t-1]+.065*e[t,11]
    eps=np.exp(np.clip(v,-1,1))*e[:,12]
    y=.20*x[:,0] + .11*x[:,1]-.14*x[:,3]+.16*x[:,4]+.25*eps
    if scenario=='weak_added_signal':
        y=y+.060*x[:,6]  # fixed modest effect; NOT calibrated to yield 1-2% MSE
    return x,y

def forecast(x,y):
    b=np.empty(HOURS_TEST);m=np.empty(HOURS_TEST)
    for k,i in enumerate(REFITS):
        end=REFITS[k+1] if k+1<len(REFITS) else HOURS_TEST
        history=HOURS_TRAIN+i
        Xb=np.column_stack((np.ones(history),x[:history,:6]))
        Xm=np.column_stack((Xb,x[:history,6:]))
        bcoef=np.linalg.lstsq(Xb,y[:history],rcond=None)[0]
        mcoef=np.linalg.lstsq(Xm,y[:history],rcond=None)[0]
        xb=np.column_stack((np.ones(end-i),x[history:HOURS_TRAIN+end,:6]))
        xm=np.column_stack((xb,x[history:HOURS_TRAIN+end,6:]))
        b[i:end]=xb@bcoef;m[i:end]=xm@mcoef
    return y[-HOURS_TEST:],b,m

def metrics(y,b,m,bix):
    eb=(y-b)**2;em=(y-m)**2
    gain=100*(eb.mean()-em.mean())/eb.mean()
    # Calendar day bootstrap (89 * 24 + last 23).
    ds=np.repeat(np.arange(90),24)[:HOURS_TEST]
    # note: final day is 23 hours: 90*24 - 1 = 2159
    s1=np.bincount(ds,weights=eb,minlength=90)
    s2=np.bincount(ds,weights=em,minlength=90)
    bg=100*(s1[bix].sum(axis=1)-s2[bix].sum(axis=1))/s1[bix].sum(axis=1)
    lower,upper=np.percentile(bg,[2.5,97.5])
    # CW correction for nested model. Use HAC only as diagnostic, not as exact-size test.
    diff=b-m
    cw=eb-em+diff*diff
    def hac_one_sided(values):
        n=len(values); z=values-values.mean(); v=(z@z)/n
        for lag in range(1,HAC_LAGS+1):
            v+=2*(1-lag/(HAC_LAGS+1))*(z[lag:]@z[:-lag])/n
        return float(norm.sf(values.mean()/np.sqrt(v/n))) if v>0 else float('nan')
    p_raw=hac_one_sided(np.bincount(ds,weights=eb-em,minlength=90)/np.bincount(ds,minlength=90))
    p_cw=hac_one_sided(np.bincount(ds,weights=cw,minlength=90)/np.bincount(ds,minlength=90))
    gate=bool(gain>0 and lower>0 and p_raw<.05)
    return gain,float(lower),float(upper),p_raw,p_cw,gate

def main():
    rng=np.random.default_rng(SEED+7)
    bix=np.empty((BOOT,90),np.int16)
    for k in range(BOOT):
        ix=[]
        while len(ix)<90:
            st=int(rng.integers(0,90-BLOCK_DAYS+1))
            ix.extend(range(st,st+BLOCK_DAYS))
        bix[k]=ix[:90]
    result={}
    for scenario in SCENARIOS:
        v=[]
        for r in range(REPS):
            x,y=generate(r,scenario)
            v.append(metrics(*forecast(x,y),bix))
        arr=np.array(v)
        counts={
            'raw_hac_p_lt_05':int(np.sum(arr[:,3]<.05)),
            'cw_hac_p_lt_05':int(np.sum(arr[:,4]<.05)),
            'raw_compound_gate':int(np.sum(arr[:,5]>0)),
            'raw_boot_lower_gt_0':int(np.sum(arr[:,1]>0)),
        }
        cis={key:[float(binomtest(n,REPS).proportion_ci(.95,method='exact').low),float(binomtest(n,REPS).proportion_ci(.95,method='exact').high)] for key,n in counts.items()}
        result[scenario]={
            'replications':REPS,'counts':counts,'rate_exact_binomial_95pct_ci':cis,
            'mean_gain_pct':float(arr[:,0].mean()),
            'median_gain_pct':float(np.median(arr[:,0])),
            'gain_pct_10_90_quantile':[float(i) for i in np.quantile(arr[:,0],[.1,.9])]
        }
        print(scenario, result[scenario],flush=True)
    manifest={
        'status':'PHASE_B_DIAGNOSTIC_ONLY_NO_MARKET_DATA_NO_PHASE_C',
        'model':'hourly reduced-form proxy for R7 nested B2 vs M2; NOT full 5m HAR DGP',
        'seed':SEED,'reps':REPS,'test_hours':HOURS_TEST,
        'train_hours':HOURS_TRAIN,'refits':list(REFITS),
        'bootstrap_reps':BOOT,'block_days':BLOCK_DAYS,'hac_lags':HAC_LAGS,
        'data_generated':'synthetic linear y with serially clustered conditional variance',
        'nulls':'exact zero BTC regression coefficient by construction, correlated null includes common predictor factor',
        'weak_effect':'BTC coefficient 0.060 ex ante, not guaranteed 1-2 percent gain',
        'cw_caveat':'daily CW-HAC secondary diagnostic; no formal finite-sample size assurance',
        'result':result
    }
    target=Path('/mnt/data/R7_phase_b_verschachtelte_inferenz_results.json')
    target.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print('Saved',target,flush=True)
if __name__=='__main__':main()
