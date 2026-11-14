#!/usr/bin/env python3
"""R8-BX strictly exploratory one-shot market analysis; source frozen before use."""
import argparse, hashlib, importlib.util, json, platform
from pathlib import Path
import numpy as np
import pandas as pd

HOME = Path.home()
REPO = HOME/'QuantResearch-Git'
DATA = HOME/'QuantResearch/Validation_2026_AugOct/data'
SRC = REPO/'studies/R8_synthetic/R8_phase_b_synthetischer_e2e_test.py'
PROTOCOL = REPO/'studies/R8_BX_EXPLORATIVER_VORVERSUCH_PROTOKOLL_2026-11-14.md'
SHA_SRC='6a8e3393952536706d6751d039577d21dd390bcab0107148275229e0221eddff'
OUT=HOME/'QuantResearch/R8_BX_Explorativ/JulTrain_AugOktTest_v1'
START=pd.Timestamp('2026-07-01T00:00Z')
TRAIN_END=pd.Timestamp('2026-08-01T00:00Z')
TEST_END=pd.Timestamp('2026-11-01T00:00Z')
FIVE=pd.Timedelta(minutes=5)
MONTHS=[TRAIN_END,pd.Timestamp('2026-09-01T00:00Z'),pd.Timestamp('2026-10-01T00:00Z'),TEST_END]

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def fail(s):raise SystemExit('R8-BX STOP: '+s)

def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight',action='store_true')
    mode.add_argument('--run',action='store_true')
    a=ap.parse_args()
    if not SRC.is_file() or sha(SRC)!=SHA_SRC:fail('frozen E2E source changed')
    if not PROTOCOL.is_file():fail('registered protocol absent')
    import subprocess
    for f in (SRC,PROTOCOL):
        rel=f.relative_to(REPO)
        if subprocess.run(['git','-C',str(REPO),'cat-file','-e',f'HEAD:{rel}'],capture_output=True).returncode:
            fail('not committed: '+str(rel))
        blob=subprocess.run(['git','-C',str(REPO),'show',f'HEAD:{rel}'],capture_output=True,check=True).stdout
        if hashlib.sha256(blob).hexdigest()!=sha(f):fail('committed source differs: '+str(rel))
    if subprocess.run(['git','-C',str(REPO),'status','--porcelain'],capture_output=True,check=True).stdout.strip():
        fail('git working tree not clean')
    if subprocess.run(['git','-C',str(REPO),'rev-parse','HEAD'],capture_output=True,check=True).stdout != subprocess.run(['git','-C',str(REPO),'rev-parse','@{upstream}'],capture_output=True,check=True).stdout:
        fail('upstream not synchronized')
    if OUT.exists():fail('one-shot output already exists')
    manifest_file=DATA/'manifest.json'
    if not manifest_file.is_file():fail('manifest missing')
    mf=json.loads(manifest_file.read_text())
    ix=pd.date_range(START,TEST_END,freq='5min',inclusive='left')
    closes={};provenance={}
    for coin in ('BTC','SOL'):
        path=DATA/f'{coin}_USDT_5m_2026-07_2026-10.parquet'
        if not path.is_file():fail(f'{coin}: file absent')
        meta=mf.get(coin,{})
        for k,v in {'exchange':'binance','market_type':'perpetual','contract_type':'linear',
                    'price_source':'last_trade','timeframe':'5m','endpoint':'/fapi/v1/klines',
                    'rows':35424}.items():
            if meta.get(k)!=v:fail(f'{coin}: provenance {k}')
        digest=sha(path)
        if digest!=meta.get('sha256'):fail(f'{coin}: hash mismatch')
        d=pd.read_parquet(path)
        if list(d.columns)!=['open_time','open','high','low','close','volume']:
            fail(f'{coin}: schema changed')
        times=pd.DatetimeIndex(d.open_time)
        if not times.equals(ix):fail(f'{coin}: UTC raster missing/duplicates/unsorted')
        arr=d[['open','high','low','close','volume']].to_numpy(float)
        if not np.isfinite(arr).all() or (arr[:,:4]<=0).any() or (arr[:,4]<0).any():
            fail(f'{coin}: bad numbers')
        op,high,low,close,vol=arr.T
        if (high<np.maximum(op,close)).any() or (low>np.minimum(op,close)).any() or (high<low).any():
            fail(f'{coin}: inconsistent OHLC')
        closes[coin]=pd.Series(close,index=ix)
        provenance[coin]={'sha256':digest,'path':str(path),'rows':len(d)}
    print('R8-BX DATENGATE: PASS (BTC,SOL; 35.424 rows each)')
    if a.preflight:
        print('R8-BX PREFLIGHT ONLY; NO MARKET PREDICTIONS, NO SCORE')
        return
    spec=importlib.util.spec_from_file_location('r8bx_frozen',SRC)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    if not all(hasattr(m,k) for k in ('build','valid_features','fit_predict','score','FEATURES_SOL','FEATURES_BTC')):
        fail('missing frozen callable')
    price=pd.DataFrame(closes,index=ix)
    _,x=m.build(price)
    prediction=[]; fits=[]
    for i,refit in enumerate(MONTHS[:-1]):
        end=MONTHS[i+1]
        train=x.loc[(x.index<refit)&(x.label_available_at<=refit)]
        train=train.loc[m.valid_features(train)&train.target.notna()]
        test=x.loc[(x.index>=refit)&(x.index<end)&m.valid_features(x)]
        test=test.loc[test.label_available_at<=TEST_END]
        if train.empty or test.empty:fail('empty train/test split')
        if (train.label_available_at>refit).any():fail('label leakage')
        prob=m.fit_predict(train,test)
        f=test[['target','label_available_at']].copy()
        for key,values in prob.items():f[key]=values
        f['refit']=refit.isoformat()
        prediction.append(f)
        fits.append({'refit':refit.isoformat(),'train_n':len(train),'forecast_n':len(test),
                     'max_known_label':str(train.label_available_at.max())})
    pred=pd.concat(prediction).sort_index()
    if pred.index.has_duplicates or pred.index.min()<TRAIN_END or pred.index.max()>=TEST_END:
        fail('bad forecast timestamps')
    counts=pred.index.floor('D').value_counts()
    if len(counts)!=92 or set(counts.index)!=set(pd.date_range(TRAIN_END,TEST_END,freq='D',inclusive='left')):
        fail('missing test days')
    good=pred.target.notna()
    scored=pred.loc[good]
    yy=scored.target.to_numpy(int)
    losses={key:m.score(yy,scored[key].to_numpy(float)) for key in ('B0','B1','M1')}
    d=losses['B1']-losses['M1']
    byday=pd.DataFrame({'sum':d,'day':scored.index.floor('D')}).groupby('day')['sum'].agg(['sum','count'])
    if len(byday)!=92:fail('bootstrap day coverage')
    rng=np.random.default_rng(20261114);n=len(byday); s=byday['sum'].to_numpy(); c=byday['count'].to_numpy()
    boot=np.empty(5000)
    for k in range(5000):
        days=[]
        while len(days)<n:
            j=int(rng.integers(0,n-7+1));days.extend(range(j,j+7))
        aidx=np.array(days[:n]);boot[k]=s[aidx].sum()/c[aidx].sum()
    ci=np.percentile(boot,[2.5,97.5]).tolist()
    delta=float(np.mean(d))
    result={'status':'EXPLORATORY_ONLY_ALREADY_USED_DATA_NOT_BLIND',
      'train':'2026-07','test':'2026-08-01/2026-11-01',
      'forecasts_all':len(pred),'scored_nonzero':int(good.sum()),'excluded_zero':int((~good).sum()),
      'refits':fits,'logloss':{k:float(v.mean()) for k,v in losses.items()},
      'delta_b1_minus_m1':delta,'relative_logloss_gain_pct':100*delta/losses['B1'].mean(),
      'bootstrap_95ci':ci,
      'classification_accuracy':{key:float(np.mean((scored[key].to_numpy()>=0.5)==yy)) for key in ('B0','B1','M1')},
      'source_sha256':SHA_SRC,'protocol_sha256':sha(PROTOCOL), 'runner_sha256':sha(Path(__file__)),
      'manifest_sha256':sha(manifest_file),'inputs':provenance,
      'versions':{'python':platform.python_version(),'numpy':np.__version__,
                 'pandas':pd.__version__,'sklearn':__import__('sklearn').__version__},
      'r8_b_independent_validation':False,'profitability_proven':False}
    OUT.mkdir(parents=True,exist_ok=False)
    (OUT/'R8_BX_RESULTS.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    (OUT/'R8_BX_FORECASTS.csv').write_text(pred.to_csv(index_label='decision_close_utc'))
    report=['# R8-BX: Explorative BTC→SOL-Richtungsprognose','',
       '**KEIN Blindtest. KEIN Profitabilitätsnachweis.**',
       'Zeitraum: Training Juli 2026; Auswertung August–Oktober 2026.',
       f'Gesamtprognosen: {len(pred)}; Score: {good.sum()}; Nullrenditen: {(~good).sum()}.',
       f'B0/B1/M1 LogLoss: {losses["B0"].mean():.8f} / {losses["B1"].mean():.8f} / {losses["M1"].mean():.8f}.',
       f'Delta B1−M1: {delta:+.9f}; relativ {result["relative_logloss_gain_pct"]:+.5f} %.',
       f'Exploratives 95%-Bootstrapintervall: [{ci[0]:+.9f}, {ci[1]:+.9f}].',
       'Alle Modellparameter und der Vergleich wurden vor der explorativen Messung fixiert.',
       'R8-B-Blindtest 2027 bleibt unverändert reserviert.']
    (OUT/'R8_BX_REPORT.md').write_text('\n\n'.join(report)+'\n')
    print('R8-BX EXPLORATORY FINISHED, NOT CONFIRMATORY')
    print(f'forecasts={len(pred)} scored={good.sum()} zero={int((~good).sum())}')
    print(f'LogLoss B1={losses["B1"].mean():.8f} M1={losses["M1"].mean():.8f}')
    print(f'Delta B1-M1={delta:+.9f}; 95%-CI={ci}')
    print('REPORT:',OUT/'R8_BX_REPORT.md')
    print('RESULT:',OUT/'R8_BX_RESULTS.json')
    print('R8-B INDEPENDENT TEST: NOT RUN')

if __name__=='__main__':main()
