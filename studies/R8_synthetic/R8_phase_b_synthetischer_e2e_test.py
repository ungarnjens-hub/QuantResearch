#!/usr/bin/env python3
"""R8 Phase B: standalone synthetic-only E2E self-test, no market data / trading systems.
Run: python R8_phase_b_synthetischer_e2e_test.py [output.json]
"""
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy.special import xlogy

SEED = 20261114
FIVE = pd.Timedelta(minutes=5)
TRAIN_START = pd.Timestamp('2025-01-01', tz='UTC')
TRAIN_END = pd.Timestamp('2027-01-01', tz='UTC')
TEST_START = pd.Timestamp('2027-04-01', tz='UTC')
TEST_END = pd.Timestamp('2027-07-01', tz='UTC')
REFITS = (TEST_START, pd.Timestamp('2027-05-01', tz='UTC'), pd.Timestamp('2027-06-01', tz='UTC'))
FEATURES_SOL = ['SOL_l0', 'SOL_l1', 'SOL_l2']
FEATURES_BTC = ['BTC_l0', 'BTC_l1', 'BTC_l2']


def synthetic_prices():
    """Closed 5m prices; two separated time intervals; no Jan-Mar 2027 values generated."""
    hist = pd.date_range(TRAIN_START, TRAIN_END, inclusive='left', freq='5min', tz='UTC')
    test = pd.date_range(TEST_START, TEST_END, inclusive='left', freq='5min', tz='UTC')
    rng = np.random.default_rng(SEED)
    def one(idx):
        n = len(idx)
        common = rng.normal(size=n)
        btc = .0010*(.60*common + .8*rng.normal(size=n))
        eth = .0012*(.65*common + .76*rng.normal(size=n))
        sol = .0016*(.55*common + .84*rng.normal(size=n))
        # True zero returns are deliberately present and are NEVER relabeled negative.
        sol[::97] = 0.0
        changes = np.column_stack([btc, eth, sol])
        prices = np.exp(np.cumsum(changes, axis=0))*np.array([50_000, 2_500, 150])
        out = pd.DataFrame(prices, index=idx, columns=['BTC','ETH','SOL'])
        return out
    return one(hist), one(test)


def build(prices):
    """Input indexes are candle OPEN times. Returns indexed by close times."""
    if prices.index.tz is None or str(prices.index.tz) != 'UTC':
        raise ValueError('Timezone not UTC')
    if not prices.index.is_unique or not prices.index.is_monotonic_increasing:
        raise ValueError('Duplicate or unordered open times')
    if not (prices.index.to_series().diff().dropna() == FIVE).all():
        raise ValueError('Missing open intervals / gap')
    if not np.isfinite(prices.to_numpy()).all() or not (prices.to_numpy()>0).all():
        raise ValueError('Bad prices')
    r = np.log(prices).diff().iloc[1:]
    # The open-time row at 00:05 closes at 00:10; index is close time, not open time.
    r.index = r.index + FIVE
    r.index.name = 'decision_close_time'
    x = pd.DataFrame(index=r.index)
    for col in ('BTC','SOL'):
        for lag in range(3):
            x[f'{col}_l{lag}'] = r[col].shift(lag)
    x['future_SOL_return'] = r['SOL'].shift(-1)
    x['label_available_at'] = x.index + FIVE
    x['target'] = np.where(x['future_SOL_return']>0, 1., np.where(x['future_SOL_return']<0, 0., np.nan))
    return r, x


def valid_features(x):
    return x[FEATURES_SOL + FEATURES_BTC].notna().all(axis=1)


def training_rows(xhist, xtest, refit):
    hist = xhist.loc[(xhist.index >= TRAIN_START) & (xhist['label_available_at'] <= TRAIN_END)]
    # Forbidden Jan-Mar 2027 never supplied; use only past April/May labels at next refit.
    past = xtest.loc[(xtest.index >= TEST_START) & (xtest['label_available_at'] <= refit)]
    combined = pd.concat([hist, past])
    combined = combined.loc[valid_features(combined) & combined['target'].notna()]
    if (combined.index >= refit).any() or (combined.label_available_at > refit).any():
        raise AssertionError('Label leakage at refit')
    forbidden = (combined.index >= TRAIN_END) & (combined.index < TEST_START)
    if forbidden.any():
        raise AssertionError('Forbidden gap in training')
    return combined


def fit_predict(train, test):
    y = train['target'].astype(int).to_numpy()
    if not set(np.unique(y)) == {0,1}:
        raise RuntimeError('Only one train class')
    outputs={}
    for name, cols in [('B1', FEATURES_SOL), ('M1', FEATURES_SOL+FEATURES_BTC)]:
        a=train[cols].to_numpy(float)
        b=test[cols].to_numpy(float)
        if not (np.isfinite(a).all() and np.isfinite(b).all()):
            raise RuntimeError('Nonfinite feature')
        scale = StandardScaler().fit(a)
        if np.any(scale.var_ == 0):
            raise RuntimeError('Constant column')
        za=scale.transform(a); zb=scale.transform(b)
        model=LogisticRegression(penalty=None, solver='lbfgs', max_iter=300, tol=1e-7)
        model.fit(za, y)
        if model.n_iter_[0] >= model.max_iter:
            raise RuntimeError('Logistic fit did not converge')
        outputs[name] = model.predict_proba(zb)[:, 1]
    outputs['B0']=np.full(len(test),y.mean())
    return outputs


def score(y, p):
    p=np.clip(p,1e-12,1-1e-12)
    return -(xlogy(y,p)+xlogy(1-y,1-p))


def bootstrap(scores, dates, n_draws=5000, block=7):
    # All predictions are made before applying nonzero-label evaluation mask.
    rec=pd.DataFrame({'difference':scores, 'day':dates}).groupby('day')['difference'].agg(['sum','count'])
    n=len(rec)
    assert n == 91, f'Expected 91 days, got {n}'
    rng=np.random.default_rng(SEED)
    s=rec['sum'].to_numpy(); c=rec['count'].to_numpy()
    draws=np.empty(n_draws)
    for i in range(n_draws):
        days=[]
        while len(days)<n:
            j=int(rng.integers(0, n-block+1))
            days.extend(range(j,j+block))
        ix=np.asarray(days[:n])
        draws[i]=s[ix].sum()/c[ix].sum()
    return np.percentile(draws,[2.5,97.5]).tolist()


def unit_checks():
    checks=[]
    def yes(name, expr):
        if not expr: raise AssertionError(name)
        checks.append(name)
    opens=pd.date_range('2027-04-01',periods=8,freq='5min',tz='UTC')
    ex = pd.DataFrame({'BTC':np.exp(np.arange(8)*.001)*100,
                       'ETH':np.exp(np.arange(8)*.002)*150,
                       'SOL':np.exp(np.arange(8)*.003)*200},index=opens)
    ret,rows=build(ex)
    yes('open_time_to_close_time', ret.index[0] == opens[1]+FIVE)
    yes('latest_complete_feature', np.isclose(rows.loc[opens[4]+FIVE, 'SOL_l0'], .003))
    yes('target_next_closed_candle', np.isclose(rows.loc[opens[4]+FIVE, 'future_SOL_return'], .003))
    yes('label_known_only_next_close', rows.loc[opens[4]+FIVE, 'label_available_at'] == opens[4]+2*FIVE)
    yes('3_lags_require_history', rows.loc[opens[2]+FIVE,'SOL_l2']!=rows.loc[opens[2]+FIVE,'SOL_l2'])
    ex2=ex.copy();ex2.iloc[3,2]=ex2.iloc[2,2]
    _,row2=build(ex2)
    yes('zero_label_is_NA_not_negative', np.isnan(row2.loc[opens[2]+FIVE,'target']))
    try:
        build(ex.drop(index=opens[3]))
    except ValueError: checks.append('missing_candle_rejected')
    else: raise AssertionError('Failed to catch gap')
    try:
        build(pd.concat([ex,ex.iloc[[0]]]).sort_index())
    except ValueError: checks.append('duplicate_rejected')
    else: raise AssertionError('Failed to catch duplicate')
    try:
        build(ex.tz_localize(None))
    except ValueError: checks.append('naive_time_rejected')
    else: raise AssertionError('Failed to catch naive time')
    # Fail closed fit cases
    rng=np.random.default_rng(8)
    sample=pd.DataFrame(rng.normal(size=(20,6)),columns=FEATURES_SOL+FEATURES_BTC)
    sample['target']=np.tile([0.,1.],10)
    for name, data in [('only_one_class',sample.assign(target=0.)),
                       ('constant_feature',sample.assign(SOL_l0=0.))]:
        try: fit_predict(data, sample.iloc[:2]); raise AssertionError(name)
        except RuntimeError: checks.append(name+'_rejected')
    return checks


def main():
    checks=unit_checks()
    hist,test=synthetic_prices()
    # No synthetic record from the reserved R7 window is generated.
    assert len(hist)==210240 and len(test)==26208, (len(hist),len(test))
    _,xh=build(hist); _,xt=build(test)
    assert xh.index.max() <= TRAIN_END and xt.index.min() >= TEST_START
    actual=[]; refits=[]
    for i,start in enumerate(REFITS):
        end=REFITS[i+1] if i+1<len(REFITS) else TEST_END
        tr=training_rows(xh,xt,start)
        te=xt.loc[(xt.index>=start) & (xt.index<end) & valid_features(xt)]
        te=te.loc[te.label_available_at <= TEST_END]
        outputs=fit_predict(tr,te)
        part=te[['target','label_available_at']].copy()
        for k,v in outputs.items(): part[k]=v
        part['refit']=str(start)
        actual.append(part)
        refits.append({'refit':str(start),'training_n':len(tr),'max_label_available':str(tr.label_available_at.max()),
                       'forecast_n':len(part),'first':str(part.index.min()),'last':str(part.index.max())})
    p=pd.concat(actual).sort_index()
    assert p.index.is_unique and p.index.is_monotonic_increasing
    assert len(p)==len(xt)-2-1, (len(p),len(xt))
    valid=p.target.notna()
    evalp=p.loc[valid]
    delta=(score(evalp.target.to_numpy(),evalp.B1.to_numpy())-
           score(evalp.target.to_numpy(),evalp.M1.to_numpy()))
    ci=bootstrap(delta,evalp.index.floor('D'))
    results={
      'status':'SYNTHETIC_ONLY_NO_MARKET_MEASUREMENT',
      'seed':SEED,
      'versions': {'numpy':np.__version__,'pandas':pd.__version__,
                   'sklearn':__import__('sklearn').__version__},
      'unit_checks':checks,
      'training_candles':len(hist),'test_candles':len(test),
      'excluded_reserved_window':'2027-01-01/2027-04-01',
      'refits':refits,'all_predictions':len(p),
      'scored_nonzero':int(valid.sum()),'zero_future_returns':int((~valid).sum()),
      'logloss_b0':float(np.mean(score(evalp.target.to_numpy(),evalp.B0.to_numpy()))),
      'logloss_b1':float(np.mean(score(evalp.target.to_numpy(),evalp.B1.to_numpy()))),
      'logloss_m1':float(np.mean(score(evalp.target.to_numpy(),evalp.M1.to_numpy()))),
      'delta_b1_minus_m1':float(delta.mean()),
      'bootstrap_95ci_delta':ci,
      'null_calibration_performed':False,
      'market_test_approved':False,
    }
    source=Path(__file__)
    results['script_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    output=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('R8_phase_b_synthetischer_e2e_resultat.json')
    output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
