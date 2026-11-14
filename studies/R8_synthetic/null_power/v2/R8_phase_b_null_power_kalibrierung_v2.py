#!/usr/bin/env python3
"""R8-B synthetic calibration, isolated; preflight only until protocol audit.

Usage:
  python R8_phase_b_null_power_kalibrierung.py --preflight
  python R8_phase_b_null_power_kalibrierung_v2.py --smoke --source /path/to/R8_phase_b_synthetischer_e2e_test.py --output-dir /tmp/R8_smoke
  python R8_phase_b_null_power_kalibrierung_v2.py --run --approval-file /path/to/approved_manifest.json --source /path/to/R8_phase_b_synthetischer_e2e_test.py --output-dir /tmp/R8_full

--run is subject to separate, explicit methodological approval.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sys, traceback, tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import lfilter
from scipy.stats import beta as beta_dist

EXPECTED_PROTOCOL_SHA = 'b3284c6e92e1de529b300b51556990e6b2d8076f06c2685fead783a6bde49bff'
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


def atomic_json(path: Path, payload: dict) -> None:
    """Crash-safe for process exceptions (not power-loss guarantees)."""
    fd, tmp = tempfile.mkstemp(prefix=".r8_", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def verify_approval(path: Path | None, source: Path, script_sha: str) -> None:
    """Separate human-reviewed approval manifest; never infer permission from --run."""
    if path is None or not path.is_file():
        raise RuntimeError("RUN_NOT_APPROVED: separate --approval-file required")
    approval = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "approved": True,
        "scope": "R8_B_SYNTHETIC_600_ONLY",
        "source_sha256": EXPECTED_SOURCE_SHA,
        "protocol_sha256": EXPECTED_PROTOCOL_SHA,
        "runner_v2_sha256": script_sha,
        "repetitions_per_scenario": 200,
    }
    if any(type(approval.get(k)) is not type(v) or approval.get(k) != v
           for k,v in required.items()):
        raise RuntimeError("RUN_NOT_APPROVED: approval manifest invalid or version mismatch")
    if hashlib.sha256(source.read_bytes()).hexdigest() != EXPECTED_SOURCE_SHA:
        raise RuntimeError("SOURCE_HASH_MISMATCH")
    print("APPROVAL_GATE: PASS (synthetic calibration only)", flush=True)


def execute_simulations(m, out: Path, reps: int, script_sha: str) -> None:
    results={'status':'SYNTHETIC_ONLY','mode':'smoke' if reps==1 else 'full',
             'source_sha256':EXPECTED_SOURCE_SHA,'script_sha256':script_sha,
             'protocol_sha256':EXPECTED_PROTOCOL_SHA,
             'versions':{'numpy':np.__version__,'pandas':pd.__version__,
                         'scikit_learn':__import__('sklearn').__version__},
             'n_per_scenario':reps,'scenarios':{},'phase_c_approved':False}
    for i, scenario in enumerate(SCENARIOS):
        rows=[]
        for j in range(reps):
            seed=SEED_BASE+1000*i+j
            try:
                row=simulate(m,scenario,seed)
                if not isinstance(row,dict) or row.get("seed") != seed:
                    raise RuntimeError("Simulation result contract violation")
                rows.append(row)
                with (out/f'{scenario}.jsonl').open('a',encoding='utf-8') as fh:
                    fh.write(json.dumps(row,ensure_ascii=False)+'\n')
                    fh.flush()
                    os.fsync(fh.fileno())
            except BaseException as exc:
                failure = {
                    "status": "ABORTED_FAIL_CLOSED", "scenario":scenario,
                    "seed":seed, "replication":j,
                    "error_type":type(exc).__name__,
                    "error_message":str(exc),
                    "traceback":traceback.format_exc(),
                    "source_sha256":EXPECTED_SOURCE_SHA,
                    "runner_v2_sha256":script_sha,
                    "protocol_sha256":EXPECTED_PROTOCOL_SHA,
                    "phase_c_approved":False,
                }
                atomic_json(out/"FAILURE.json",failure)
                raise RuntimeError(
                    f"FAIL-CLOSED: scenario={scenario} seed={seed}; "
                    f"details: {out/'FAILURE.json'}") from exc
        yes=sum(x['positive_gate'] for x in rows)
        results['scenarios'][scenario]={
            'n':reps,'positive_gate_n':yes,'positive_gate_rate':yes/reps,
            'exact_95_binomial_ci':clopper_pearson(yes,reps),
            'mean_delta':float(np.mean([x['delta'] for x in rows]))}
        print(scenario, results['scenarios'][scenario],flush=True)
    atomic_json(out/'summary.json',results)
    print('DONE:',out/'summary.json','PHASE_C_APPROVED: FALSE')


def selftest_gates():
    """No model fits or simulated prices; injection of deterministic failure."""
    import unittest.mock as mock
    with tempfile.TemporaryDirectory(prefix="R8_v2_gate_selftest_") as work:
        root=Path(work)
        sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        source=Path(__file__)  # a stand-in, never accepted as frozen source
        # A validly shaped file with missing approval must be rejected.
        try:
            verify_approval(None,source,sha)
        except RuntimeError as e:
            assert "RUN_NOT_APPROVED" in str(e)
        else:
            raise AssertionError("Approval gate bypass")
        try:
            verify_approval(root/"missing.json",source,sha)
        except RuntimeError as e:
            assert "RUN_NOT_APPROVED" in str(e)
        else:
            raise AssertionError("Missing-file gate bypass")
        # Inject a deterministic exception before any model call.
        with mock.patch(__name__+".simulate", side_effect=ValueError("INJECTED_FAILURE")):
            try:
                execute_simulations(None,root,1,sha)
            except RuntimeError as e:
                assert "FAIL-CLOSED" in str(e)
            else:
                raise AssertionError("Injected failure not propagated")
        obj=json.loads((root/"FAILURE.json").read_text())
        assert obj["status"]=="ABORTED_FAIL_CLOSED"
        assert obj["scenario"]==SCENARIOS[0] and obj["seed"]==SEED_BASE
        assert obj["error_type"]=="ValueError" and "INJECTED_FAILURE" in obj["traceback"]
        assert obj["source_sha256"]==EXPECTED_SOURCE_SHA
        assert not (root/"summary.json").exists()
    print("GATE_SELFTEST: PASS; no model fitting; no market data")


def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--preflight',action='store_true')
    group.add_argument('--smoke',action='store_true')
    group.add_argument('--run',action='store_true')
    group.add_argument('--selftest-gates',action='store_true')
    ap.add_argument('--source',type=Path)
    ap.add_argument('--output-dir',type=Path)
    ap.add_argument('--approval-file',type=Path,
                    help="Required for --run; separate versioned human approval")
    args=ap.parse_args()
    if args.selftest_gates:
        selftest_gates()
        return
    if args.preflight:
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
    script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.run:
        verify_approval(args.approval_file,args.source,script_sha)
    elif args.approval_file:
        ap.error('--approval-file is permitted only with --run')
    # Frozen reference source is loaded only after the run gate has passed.
    m=load_frozen(args.source)
    out=args.output_dir
    out.mkdir(parents=True,exist_ok=False)
    execute_simulations(m,out,1 if args.smoke else 200,script_sha)


if __name__=='__main__':
    main()
