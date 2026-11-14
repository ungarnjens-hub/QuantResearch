#!/usr/bin/env python3
"""R7 Phase B: synthetic-only test. No market file, API, trading directory accessed."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import norm

SEED=20261114
RNG=np.random.default_rng(SEED)


def bootstrap_interval(daily_a, daily_b, *, draws=500, block=7, seed=SEED):
    n=len(daily_a)
    rng=np.random.default_rng(seed)
    result=np.empty(draws)
    for i in range(draws):
        ix=[]
        while len(ix)<n:
            j=int(rng.integers(n-block+1))
            ix.extend(range(j,j+block))
        ix=ix[:n]
        a,b=daily_a[ix].sum(),daily_b[ix].sum()
        result[i]=100*(a-b)/a
    return np.percentile(result,[2.5,97.5])


def hac_daily(d, lag=7):
    n=len(d)
    c=d-d.mean()
    v=float(c@c/n)
    for k in range(1,min(n,lag+1)):
        v+=2*(1-k/(lag+1))*float(c[k:]@c[:-k]/n)
    return float(d.mean()/np.sqrt(v/n)) if v>0 else float('nan')


def evaluate(loss_b,loss_m,draws=400):
    # 90 UTC days * 24 forecasts, no partial days.
    a=loss_b.reshape(90,24).sum(axis=1)
    b=loss_m.reshape(90,24).sum(axis=1)
    lo,hi=bootstrap_interval(a,b,draws=draws)
    gain=100*(loss_b.mean()-loss_m.mean())/loss_b.mean()
    d=(loss_b-loss_m).reshape(90,24).mean(axis=1)
    z=hac_daily(d)
    return gain,lo,hi,z


def synthetic_case(beta,rep):
    # Construct a fixed predictive linear DGP with persistent, correlated regressors.
    # ETH(3), SOL(3), BTC(3) each available as of identical forecast cutoff.
    ntrain=24*365
    ntest=24*90
    n=ntrain+ntest
    rng=np.random.default_rng(SEED+rep)
    x=np.empty((n,9),float)
    latent=np.empty((n,3),float)
    latent[0]=rng.normal(size=3)
    shocks=rng.normal(size=(n,3))
    for t in range(1,n):
        latent[t]=.92*latent[t-1]+shocks[t]
    for j in range(3):
        x[:,j]=.7*latent[:,0]+.3*rng.normal(size=n)
        x[:,j+3]=.6*latent[:,1]+.25*latent[:,0]+.3*rng.normal(size=n)
        x[:,j+6]=.6*latent[:,2]+.25*latent[:,0]+.3*rng.normal(size=n)
    # shared shocks induce serial correlation in forecast errors
    errors=np.empty(n)
    white=rng.normal(size=n)
    errors[0]=white[0]
    for t in range(1,n): errors[t]=.35*errors[t-1]+white[t]
    # BTC residual information only when beta > 0.
    y=0.5 + 0.17*x[:,0]+.12*x[:,3]+beta*x[:,6]+errors
    pred_b=np.empty(ntest);pred_m=np.empty(ntest)
    # fixed monthly refits on 2027 Jan, Feb, Mar (31,28,31 days)
    idx=0
    for month_days in (31,28,31):
        train_end=ntrain+idx
        # conservative label-unavailability: last 2 hourly target labels excluded
        available=train_end-2
        assert available < train_end
        # stable solution using lstsq; 3 extra BTC features in candidate
        def forecast(k):
            mat=np.column_stack((np.ones(available),x[:available,:k]))
            co=np.linalg.lstsq(mat,y[:available],rcond=None)[0]
            horizon=month_days*24
            future=np.column_stack((np.ones(horizon),x[train_end:train_end+horizon,:k]))
            return future@co
        a=forecast(6);b=forecast(9)
        pred_b[idx:idx+month_days*24]=a
        pred_m[idx:idx+month_days*24]=b
        idx+=month_days*24
    loss_b=(y[ntrain:]-pred_b)**2
    loss_m=(y[ntrain:]-pred_m)**2
    return evaluate(loss_b,loss_m)


def temporal_gate():
    idx=pd.date_range('2027-01-01', '2027-04-01', freq='5min',inclusive='left',tz='UTC')
    pred=idx[idx.minute==55]
    # following original R5/R6 convention forecast hh:55, decision hh+1:00, label hh+2:00
    allowed=pred[pred+pd.Timedelta(minutes=65)<=pd.Timestamp('2027-04-01',tz='UTC')]
    assert len(allowed)==2159  # 90 days times 24 forecasts minus final 1
    assert allowed[0]==pd.Timestamp('2027-01-01 00:55',tz='UTC')
    assert allowed[-1]==pd.Timestamp('2027-03-31 22:55',tz='UTC')
    assert len(allowed.normalize().unique())==90
    assert (allowed+pd.Timedelta(minutes=5)<=allowed+pd.Timedelta(minutes=65)).all()
    # missing bars and duplicate timestamps must fail checked frequency
    assert idx.is_unique and (idx.to_series().diff().dropna()==pd.Timedelta(minutes=5)).all()
    corrupt=idx.delete(100)
    assert not (corrupt.to_series().diff().dropna()==pd.Timedelta(minutes=5)).all()
    return len(allowed)



def five_minute_gate():
    """One full synthetic 3-market 5m feature/target/OLS path."""
    rng=np.random.default_rng(SEED+333)
    index=pd.date_range('2025-11-01', '2027-04-01',freq='5min',inclusive='left',tz='UTC')
    n=len(index)
    shared=rng.normal(0,.001,size=n)
    rets=np.column_stack((
       .55*shared+rng.normal(0,.0008,size=n),
       .65*shared+rng.normal(0,.0010,size=n),
       .60*shared+rng.normal(0,.0011,size=n)))
    price=pd.DataFrame(np.exp(np.log([30000.,2000.,100.])+np.cumsum(rets,axis=0)),index=index,columns=['BTC','ETH','SOL'])
    ret=np.log(price).diff(); sq=ret**2
    features=pd.DataFrame(index=index)
    features['intercept']=1.
    for m in ('ETH','SOL','BTC'):
       for w in (12,288,2016):
           features[f'{m}{w}']=np.log(sq[m].rolling(w).mean()+1e-12)
    features['target']=np.log(sq['ETH'].rolling(12).sum().shift(-12)+1e-12)
    features['available']=pd.Series(index,index=index).shift(-12)+pd.Timedelta(minutes=5)
    data=features.loc[features.index.minute==55].dropna()
    bcols=['intercept']+[f'{m}{w}' for m in ('ETH','SOL') for w in (12,288,2016)]
    mcols=bcols+[f'BTC{w}' for w in (12,288,2016)]
    predictions=[];sizes=[]
    for start,stop in [('2027-01-01','2027-02-01'),('2027-02-01','2027-03-01'),('2027-03-01','2027-04-01')]:
        month=pd.Timestamp(start,tz='UTC');end=pd.Timestamp(stop,tz='UTC')
        train=data.loc[(data.index>=pd.Timestamp('2025-11-01',tz='UTC'))&(data.available<=month)]
        test=data.loc[(data.index>=month)&(data.index<end)&(data.available<=pd.Timestamp('2027-04-01',tz='UTC'))]
        assert len(train)>1000 and len(test)>500
        assert train.available.max()<=month
        assert (test.index+pd.Timedelta(minutes=5)<=test.index+pd.Timedelta(minutes=65)).all()
        assert np.linalg.matrix_rank(train[bcols].to_numpy())==len(bcols)
        assert np.linalg.matrix_rank(train[mcols].to_numpy())==len(mcols)
        coeff_b=np.linalg.lstsq(train[bcols].to_numpy(),train.target.to_numpy(),rcond=None)[0]
        coeff_m=np.linalg.lstsq(train[mcols].to_numpy(),train.target.to_numpy(),rcond=None)[0]
        predictions.extend(zip(test.index,test.target.to_numpy(),test[bcols].to_numpy()@coeff_b,test[mcols].to_numpy()@coeff_m))
        sizes.append((start,len(train),len(test)))
    p=pd.DataFrame(predictions,columns=['time','y','B2','M2']).set_index('time')
    expected=index[(index.minute==55)&(index>=pd.Timestamp('2027-01-01',tz='UTC'))]
    expected=expected[expected+pd.Timedelta(minutes=65)<=pd.Timestamp('2027-04-01',tz='UTC')]
    assert len(p)==2159 and p.index.equals(expected)
    assert np.isfinite(p.to_numpy()).all()
    # explicit same-time information boundary, no target from future train
    # Target can differ after future changes, but HAR at decision time cannot.
    t=pd.Timestamp('2027-01-05 12:55',tz='UTC')
    assert features.loc[t,'available']==t+pd.Timedelta(minutes=65)
    prior_eth=features.loc[t,'ETH12']
    altered=price['ETH'].copy()
    altered.loc[altered.index>t]*=1.2
    altered_ret=np.log(altered).diff().pow(2)
    assert np.isclose(prior_eth,np.log(altered_ret.rolling(12).mean().loc[t]+1e-12),atol=1e-12,rtol=0)
    return {'forecasts':len(p),'monthly_training_test':sizes,'finite':True,'times_pass':True}


def main():
    number=temporal_gate()
    pipeline=five_minute_gate()
    # representative only: not a complete price/candle/HAR construction or leakage proof
    samples=240
    rows={}
    for title,beta in [('null',0.0),('alternative',0.35)]:
        v=np.array([synthetic_case(beta,i+(0 if beta==0 else 10000)) for i in range(samples)])
        positive=(v[:,1]>0)
        rows[title]={
            'runs':samples,'beta':beta,
            'positive_ci_rate':float(positive.mean()),
            'positive_point_gain_rate':float((v[:,0]>0).mean()),
            'mean_gain_pct':float(v[:,0].mean()),
            'median_gain_pct':float(np.median(v[:,0])),
            'ci_lower_5_95':np.percentile(v[:,1],[5,95]).tolist(),
            'hac_positive_rate':float((v[:,3]>norm.isf(.05)).mean())}
    result={'kind':'R7 Phase-B SYNTHETIC, not market evidence',
        'temporal_allowed_forecasts':number,'five_minute_pipeline':pipeline,'simulations':rows,
        'interpretation':'One full synthetic 5m HAR/realized-volatility pipeline + separate partial Monte Carlo calibration with 240 hourly nested-model simulations per scenario. Simulation does not replicate full RV price DGP and nominal error coverage is not proven.',
        'decision':'No Phase C approval; complete 5m end-to-end synthetic gate and inference-method audit still required.'}
    Path('/mnt/data/R7_phase_b_synthetik_resultat.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
