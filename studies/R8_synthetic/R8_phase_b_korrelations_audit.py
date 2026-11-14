#!/usr/bin/env python3
"""R8-A Phase-B: synthetische Korrelation, Tagesblockbootstrap, Fail-Closed.
Keine Marktdateien, Netzzugriffe oder produktiven Systeme.
"""
import json
import hashlib
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261114
DAYS = 92
SLOTS = 288
DRAWS = 5000
BLOCK = 7
PAIRS = [('BTC','ETH'),('BTC','SOL'),('ETH','SOL')]
OUT = Path(__file__).with_name('R8_phase_b_korrelations_resultat.json')


def strict_returns(close, open_idx):
    """Close prices indexed by OPEN time; return indexed by CLOSE time."""
    if close.index.has_duplicates or not close.index.equals(open_idx):
        raise ValueError('uneindeutige/off-grid/fehlende open timestamps')
    if not np.all(np.isfinite(close.to_numpy(dtype=float))) or (close.to_numpy(dtype=float) <= 0).any():
        raise ValueError('ungueltige/fehlende close prices')
    r = np.log(close).diff().iloc[1:]
    r.index = r.index + pd.Timedelta(minutes=5)
    if not np.isfinite(r.to_numpy(dtype=float)).all():
        raise ValueError('ungueltige returns')
    return r


def validate_grid(r):
    if r.index.tz is None or str(r.index.tz) != 'UTC':
        raise ValueError('UTC notwendig')
    if r.index.has_duplicates or not r.index.is_monotonic_increasing:
        raise ValueError('Duplikate/Unordnung')
    if list(r.columns) != ['BTC','ETH','SOL']:
        raise ValueError('Spalten oder Alignment')
    if not np.isfinite(r.to_numpy(dtype=float)).all():
        raise ValueError('fehlende/ungueltige Daten')
    idx = pd.date_range(r.index[0], r.index[-1], freq='5min', tz='UTC')
    if not r.index.equals(idx):
        raise ValueError('Luecken/Alignment')
    counts = r.groupby(r.index.floor('D')).size()
    if not (counts == SLOTS).all() or not (r.index[0].hour == r.index[0].minute == 0):
        raise ValueError('Teil-Tage: nur vollstaendige UTC-Tage erlaubt')
    return int(len(counts))


def daily_stats(r):
    daily=[]
    for day, grp in r.groupby(r.index.floor('D'), sort=True):
        mat=grp[['BTC','ETH','SOL']].to_numpy(dtype=np.float64)
        vals=[]
        for ai,bi in [(0,1),(0,2),(1,2)]:
            x,y=mat[:,ai],mat[:,bi]
            active=(x != 0) & (y != 0)
            vals.extend([len(x),float(x.sum()),float(y.sum()),float(x@x),float(y@y),float(x@y),
                         int(active.sum()),int(np.sum(np.sign(x[active]) == np.sign(y[active]))),
                         int((~active).sum())])
        daily.append(vals)
    return np.array(daily, dtype=np.float64).reshape(-1,3,9)


def metric(s):
    n,sx,sy,sxx,syy,sxy,nonzero,same,excluded=np.moveaxis(s, -1, 0)
    cov=sxy-sx*sy/n
    v1=sxx-sx*sx/n; v2=syy-sy*sy/n
    if np.any(v1<=0) or np.any(v2<=0):
        raise ValueError('konstante Renditen')
    corr=cov/np.sqrt(v1*v2)
    signs=same/nonzero
    if not np.isfinite(corr).all() or not np.isfinite(signs).all():
        raise ValueError('unbestimmte Korrelation/Vorzeichen')
    return corr, signs, nonzero, same, excluded


def bootstrap(r):
    ndays=validate_grid(r)
    if ndays < BLOCK:
        raise ValueError('zu wenige Tage')
    ds=daily_stats(r)
    point=metric(ds.sum(axis=0))
    rng=np.random.default_rng(SEED)
    ix=np.empty((DRAWS,ndays),dtype=np.int16)
    for j in range(DRAWS):
        chosen=[]
        while len(chosen)<ndays:
            start=int(rng.integers(0,ndays-BLOCK+1))
            chosen.extend(range(start,start+BLOCK))
        ix[j]=chosen[:ndays]
    # Each resampled day is used identically across all three pairs.
    samples=ds[ix].sum(axis=1)
    corr,sign,_,_,_=metric(samples)
    return {'pairs': {label: {
       'pearson':float(point[0][k]),
       'pearson_ci95':np.percentile(corr[:,k],[2.5,97.5]).tolist(),
       'sign_agreement_nonzero':float(point[1][k]),
       'sign_ci95':np.percentile(sign[:,k],[2.5,97.5]).tolist(),
       'nonzero_n':int(point[2][k]),'matching_n':int(point[3][k]),
       'excluded_zero_n':int(point[4][k])}
       for k,(a,b) in enumerate(PAIRS) for label in [a+'_'+b]},
       'n_returns':len(r),'n_complete_days':ndays,'bootstrap_draws':DRAWS,
       'block_days':BLOCK,'seed':SEED}


def must_fail(func):
    try:
        func()
    except ValueError:
        return
    raise AssertionError('fehlender Fail-Closed-Schutz')


def main():
    # 93 whole days of synthetic close prices give 92 complete days of returns,
    # because return at day 1 00:00 requires preceding close.
    ret_times=pd.date_range('2026-08-01',periods=DAYS*SLOTS,freq='5min',tz='UTC')
    open_times=ret_times-pd.Timedelta(minutes=5)
    rng=np.random.default_rng(SEED)
    factor=rng.normal(size=len(ret_times))
    idiosyncratic=rng.normal(size=(len(ret_times),3))
    simulated=0.001*(factor[:,None]+idiosyncratic*0.7)
    # deterministic zero-return examples in different combinations.
    simulated[::113,0]=0
    simulated[::137,1]=0
    simulated[::173,2]=0
    # Append an initial preceding CLOSE and construct 3 price series indexed by candle OPEN time.
    # Close of candle open T-5 is known at T: return at time T is log(C[T-5]/C[T-10]).
    prev_close_idx=ret_times[0]-pd.Timedelta(minutes=10)
    all_open_idx=pd.DatetimeIndex([prev_close_idx]).append(open_times)
    logprices=np.vstack([np.log([50000,3000,100]),np.log([50000,3000,100])+simulated.cumsum(axis=0)])
    closes=pd.DataFrame(np.exp(logprices),index=all_open_idx,columns=['BTC','ETH','SOL'])
    r=strict_returns(closes,all_open_idx)
    assert r.index.equals(ret_times)
    assert np.max(np.abs(r.to_numpy()-simulated))<1e-12
    out=bootstrap(r)
    assert out['n_returns']==DAYS*SLOTS and out['n_complete_days']==DAYS
    for pair in out['pairs'].values():
        assert -1<=pair['pearson']<=1
        assert pair['excluded_zero_n']>0
        assert pair['nonzero_n']+pair['excluded_zero_n']==DAYS*SLOTS
        assert pair['sign_ci95'][0] <= pair['sign_ci95'][1]
    # Analytic invariance: positive unit scaling does not change Pearson or sign agreement.
    scaled=r.mul([1e3, 1e-1, 1e2],axis='columns')
    out_scaled=bootstrap(scaled)
    for name in out['pairs']:
        for field in ['pearson','sign_agreement_nonzero']:
            assert abs(out['pairs'][name][field]-out_scaled['pairs'][name][field])<1e-10
        for field in ['pearson_ci95','sign_ci95']:
            assert np.allclose(out['pairs'][name][field],out_scaled['pairs'][name][field],atol=1e-10)
    # Exact pairwise Pearson compared with independent numpy implementation.
    for a,b in PAIRS:
        name=a+'_'+b
        assert np.isclose(out['pairs'][name]['pearson'],np.corrcoef(r[a],r[b])[0,1],atol=1e-10)
    # Zero-return filter: pair-specific with explicit complete-case denominator.
    for a,b in PAIRS:
        mask=(r[a]!=0)&(r[b]!=0)
        nm=a+'_'+b
        assert out['pairs'][nm]['nonzero_n']==int(mask.sum())
        assert out['pairs'][nm]['matching_n']==int((np.sign(r[a][mask])==np.sign(r[b][mask])).sum())
    checks=['all_three_pairs','time_open_close','closed_returns_no_lookahead',
            '92_complete_days','pairwise_zero_policy','pearson_numpy_crosscheck',
            'unit_scale_invariance','paired_block_resampling','deterministic_seed']
    must_fail(lambda:validate_grid(r.iloc[1:]))
    checks.append('partial_day_rejected')
    must_fail(lambda:validate_grid(r.drop(r.index[120])))
    checks.append('missing_candle_rejected')
    must_fail(lambda:validate_grid(pd.concat([r,r.iloc[[12]]]).sort_index()))
    checks.append('duplicate_rejected')
    tampered=r.copy();tampered.loc[tampered.index[30],'ETH']=np.nan
    must_fail(lambda:validate_grid(tampered))
    checks.append('nan_rejected')
    corrupt=closes.copy(); corrupt.iloc[3,0]=0
    must_fail(lambda:strict_returns(corrupt,all_open_idx))
    checks.append('nonpositive_price_rejected')
    bad=closes.copy();bad.index=bad.index+pd.Timedelta(minutes=1)
    must_fail(lambda:strict_returns(bad,all_open_idx))
    checks.append('misaligned_open_rejected')
    # Independent and anti-correlated synthetic control cases.
    rng_checks=np.random.default_rng(SEED+1)
    indep=pd.DataFrame(rng_checks.normal(size=(DAYS*SLOTS,3)),index=ret_times,
                       columns=['BTC','ETH','SOL'])
    independent_out=bootstrap(indep)
    assert all(abs(v['pearson'])<0.04 for v in independent_out['pairs'].values())
    assert all(v['pearson_ci95'][0]<v['pearson']<v['pearson_ci95'][1] for v in independent_out['pairs'].values())
    checks.append('independent_returns_control')
    opposite=indep.copy()
    opposite['SOL']=-opposite['BTC']
    opposite_out=bootstrap(opposite)
    assert abs(opposite_out['pairs']['BTC_SOL']['pearson']+1)<1e-10
    assert opposite_out['pairs']['BTC_SOL']['sign_agreement_nonzero']==0
    checks.append('perfect_negative_control')
    degenerate=indep.copy(); degenerate['BTC']=0
    must_fail(lambda:bootstrap(degenerate))
    checks.append('zero_variance_rejected')
    # Independence baseline: do not claim significance; this dataset intentionally correlated.
    out.update({'status':'SYNTHETIC_TECH_AUDIT_ONLY','checks_passed':len(checks),
                'check_names':checks,'python_version':platform.python_version(),
                'numpy_version':np.__version__,'pandas_version':pd.__version__,
                'seed_note':'Same seed used for synthetic prices and for resampling; reproducible.',
                'no_real_market_data':True,'no_phase_c_release':True})
    OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('PASS',len(checks),'Pruefungen; synthetic 5m returns',len(r),'days',DAYS)
    for pair,v in out['pairs'].items():
        print(pair,'r',round(v['pearson'],5),'CI',np.round(v['pearson_ci95'],5),
              'sign',round(v['sign_agreement_nonzero'],5),'n_nonzero',v['nonzero_n'])
    print('RESULT',OUT)

if __name__=='__main__':
    main()
