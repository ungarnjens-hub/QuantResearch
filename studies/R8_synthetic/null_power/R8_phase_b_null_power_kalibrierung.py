#!/usr/bin/env python3
"""R8-B synthetic calibration, isolated; preflight only until protocol audit.

Usage:
  python R8_phase_b_null_power_kalibrierung.py --preflight
  python R8_phase_b_null_power_kalibrierung.py --smoke --source /path/to/R8_phase_b_synthetischer_e2e_test.py --output-dir /tmp/R8_smoke
  python R8_phase_b_null_power_kalibrierung.py --run --source /path/to/R8_phase_b_synthetischer_e2e_test.py --output-dir /tmp/R8_full

--run is subject to separate, explicit methodological approval.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import lfilter
from scipy.stats import beta as beta_dist

EXPECTED_SOURCE_SHA = '6a8e3393952536706d6751d039577d21dd390bcab0107148275229e0221eddff'
SEED_BASE = 20261114000
SCENARIOS = ('independent_null', 'common_factor_null', 'lagged_btc_alternative')
FIVE = pd.Timedelta(minutes=5)
TRAIN_START = pd.Timestamp('2025-01-01', tz='UTC')
TRAIN_END = pd.Timestamp('2027-01-01', tz='UTC')
TEST_START = pd.Timestamp('2027-04-01', tz='UTC')
TEST_END = pd.Timestamp('2027-07-01', tz='UTC')
REFITS = (TEST_START, pd.Timestamp('2027-05-01', tz='UTC'), pd.Timestamp('2027-06-01', tz='UTC'))


def prices(index: pd.DatetimeIndex, rng: np.random.Generator, scenario: str):
    """Construct strictly synthetic trade-close series, indexed by candle OPEN times.

    Null conditional outcome sign is symmetric independently of BTC and SOL history.
    A persistent shared stochastic scale and contemporaneous return correlation
    do not create conditional directional predictability under these nulls.
    """
    n=len(index)
    zcommon = rng.standard_normal(n)
    if scenario == 'independent_null':
        shared=np.zeros(n)
    else:
        shared=lfilter([0.04],[1.0,-0.98],zcommon)  # AR(1) log-vol scale
    scale=np.exp(np.clip(shared,-1.5,1.5))
    esol=rng.standard_normal(n)
    ebtc=rng.standard_normal(n)
    eeth=rng.standard_normal(n)
    rho=0.0 if scenario == 'independent_null' else 0.65
    btc_innov=rho*esol+np.sqrt(1-rho*rho)*ebtc
    beta=0.20 if scenario == 'lagged_btc_alternative' else 0.0
    # A genuinely prior BTC-specific shock; causal synthetic alternative only.
    lagged_btc_specific=np.r_[0.0,ebtc[:-1]]
    ret_sol=0.0016*scale*(esol+beta*lagged_btc_specific)
    ret_btc=0.0010*scale*btc_innov
    ret_eth=0.0012*scale*(0.6*esol+0.8*eeth)
    # Fixed zero-return mask, decided before any model fitting and independent of innovations.
    ret_sol[::97]=0.0
    array=np.column_stack([ret_btc,ret_eth,ret_sol])
    logp=np.cumsum(array,axis=0)+np.log([50000.,2500.,150.])
    p=pd.DataFrame(np.exp(logp),index=index,columns=['BTC','ETH','SOL'])
    assert np.isfinite(p.to_numpy()).all() and (p.to_numpy()>0).all()
    return p


def load_frozen(path: Path):
    assert path.is_file(), f'Missing frozen source: {path}'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SOURCE_SHA:
        raise RuntimeError(f'SOURCE_HASH_MISMATCH {digest}')
    spec=importlib.util.spec_from_file_location('r8_frozen_synthetic_e2e',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name,value in [('TRAIN_START',TRAIN_START),('TRAIN_END',TRAIN_END),('TEST_START',TEST_START),('TEST_END',TEST_END)]:
        if getattr(module,name)!=value: raise RuntimeError(f'Frozen contract mismatch {name}')
    return module


def simulate(m, scenario: str, seed: int):
    rng=np.random.default_rng(seed)
    hi=pd.date_range(TRAIN_START,TRAIN_END, inclusive='left',freq='5min',tz='UTC')
    ti=pd.date_range(TEST_START,TEST_END, inclusive='left',freq='5min',tz='UTC')
    ph=prices(hi,rng,scenario)
    pt=prices(ti,rng,scenario)
    _,xh=m.build(ph)
    _,xt=m.build(pt)
    output=[]
    for i,start in enumerate(REFITS):
        end=REFITS[i+1] if i+1<len(REFITS) else TEST_END
        tr=m.training_rows(xh,xt,start)
        te=xt.loc[(xt.index>=start)&(xt.index<end)&m.valid_features(xt)]
        te=te.loc[te.label_available_at<=TEST_END]
        pred=m.fit_predict(tr,te)
        q=te[['target']].copy()
        q['B0']=pred['B0'];q['B1']=pred['B1'];q['M1']=pred['M1']
        output.append(q)
    allp=pd.concat(output).sort_index()
    if len(allp)!=26204 or len(allp.index.unique())!=26204:
        raise RuntimeError(f'Forecast coverage mismatch {len(allp)}')
    valid=allp.target.notna()
    e=allp.loc[valid]
    if e.empty: raise RuntimeError('No scored forecasts')
    y=e.target.to_numpy()
    loss0=m.score(y,e.B0.to_numpy()).mean()
    loss1=m.score(y,e.B1.to_numpy()).mean()
    loss2=m.score(y,e.M1.to_numpy()).mean()
    diff=m.score(y,e.B1.to_numpy())-m.score(y,e.M1.to_numpy())
    ci=m.bootstrap(diff,e.index.floor('D'),n_draws=5000,block=7)
    return {'scenario':scenario,'seed':seed,'all_predictions':len(allp),
            'scored':len(e),'zero_label':int((~valid).sum()),
            'logloss_B0':float(loss0),'logloss_B1':float(loss1),
            'logloss_M1':float(loss2),'delta':float(diff.mean()),
            'ci_95':ci,'positive_gate':bool(diff.mean()>0 and ci[0]>0)}


def clopper_pearson(successes: int, n: int):
    if n<1: return [None,None]
    lo=0.0 if successes==0 else float(beta_dist.ppf(.025,successes,n-successes+1))
    hi=1.0 if successes==n else float(beta_dist.ppf(.975,successes+1,n-successes))
    return [lo,hi]


def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--preflight',action='store_true')
    group.add_argument('--smoke',action='store_true')
    group.add_argument('--run',action='store_true')
    ap.add_argument('--source',type=Path)
    ap.add_argument('--output-dir',type=Path)
    args=ap.parse_args()
    if args.preflight:
        # No fitting, no market data and no filesystem changes.
        n=30000
        ix=pd.date_range('2027-04-01',periods=n,freq='5min',tz='UTC')
        for j,name in enumerate(SCENARIOS):
            p=prices(ix,np.random.default_rng(SEED_BASE+j),name)
            assert len(p)==n and p.index.is_unique
            assert np.isfinite(np.log(p).diff().iloc[1:].to_numpy()).all()
            print('PREFLIGHT:',name,'PASS')
        print('STATUS: SYNTHETIC_DGP_PREFLIGHT_ONLY; NO_INFERENCE_OR_MARKET_RELEASE')
        return
    if not args.source or not args.output_dir:
        ap.error('--source and --output-dir required for smoke/run')
    m=load_frozen(args.source)
    # One new directory per run, never overwrite results.
    out=args.output_dir
    out.mkdir(parents=True,exist_ok=False)
    reps=1 if args.smoke else 200
    results={'status':'SYNTHETIC_ONLY','mode':'smoke' if args.smoke else 'full',
             'source_sha256':EXPECTED_SOURCE_SHA,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'versions':{'numpy':np.__version__,'pandas':pd.__version__,'scikit_learn':__import__('sklearn').__version__},
             'n_per_scenario':reps,'scenarios':{},'phase_c_approved':False}
    for i,scenario in enumerate(SCENARIOS):
        rows=[]
        for j in range(reps):
            seed=SEED_BASE+1000*i+j
            row=simulate(m,scenario,seed)
            rows.append(row)
            # Durable append-only checkpoint for failures; never count an aborted run as PASS.
            with (out/f'{scenario}.jsonl').open('a',encoding='utf-8') as fh:
                fh.write(json.dumps(row,ensure_ascii=False)+'\n')
        yes=sum(x['positive_gate'] for x in rows)
        results['scenarios'][scenario]={
            'n':reps,'positive_gate_n':yes,'positive_gate_rate':yes/reps,
            'exact_95_binomial_ci':clopper_pearson(yes,reps),
            'mean_delta':float(np.mean([x['delta'] for x in rows]))}
        print(scenario, results['scenarios'][scenario],flush=True)
    (out/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('DONE:',out/'summary.json','PHASE_C_APPROVED: FALSE')

if __name__=='__main__':
    main()
