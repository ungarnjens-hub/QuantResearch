from pathlib import Path
import sys, hashlib
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm

R = Path.home() / "QuantResearch/R5_BTC_ETH_Volatilitaet"
BASE = Path.home() / "Dokumente/TradingLab/data/canonical/binance/perpetual/klines"
START = pd.Timestamp("2024-09-01", tz="UTC")
FIRST = pd.Timestamp("2025-03-01", tz="UTC")
END = pd.Timestamp("2026-07-01", tz="UTC")
EPS = 1e-12

def features(frame):
    ret = np.log(frame / frame.shift(1))
    sq = ret ** 2
    x = pd.DataFrame(index=frame.index)
    x["intercept"] = 1.0
    for coin in ("ETH", "BTC"):
        for w in (12, 288, 2016):
            x[f"{coin}{w}"] = np.log(
                sq[coin].rolling(w).mean() + EPS
            )
    x["target"] = np.log(
        sq["ETH"].rolling(12).sum().shift(-12) + EPS
    )
    x["available"] = pd.Series(
        frame.index, index=frame.index
    ).shift(-12) + pd.Timedelta(minutes=5)
    x = x[x.index.minute == 55]
    return x.dropna()

def selftest():
    idx = pd.date_range(
        "2025-01-01", periods=3500,
        freq="5min", tz="UTC"
    )
    n = np.arange(len(idx))
    frame = pd.DataFrame({
        "ETH": 2000*np.exp(np.cumsum(
            0.001*np.sin(n/17))),
        "BTC": 50000*np.exp(np.cumsum(
            0.001*np.cos(n/23)))
    }, index=idx)

    a = features(frame)
    assert len(a) > 50
    assert (a.index.minute == 55).all()
    assert (a.available > a.index).all()
    assert (a.available-a.index ==
            pd.Timedelta(minutes=65)).all()

    t = a.index[0]
    pos = frame.index.get_loc(t)
    ret = np.log(frame.ETH).diff().to_numpy()
    expected = np.log(
        np.sum(ret[pos+1:pos+13]**2) + EPS
    )
    assert np.isclose(a.loc[t, "target"], expected)

    changed = frame.copy()
    changed.loc[changed.index > t, "BTC"] *= 2
    b = features(changed)
    cols = [c for c in a if c.startswith("BTC")]
    assert np.allclose(a.loc[t, cols].astype(float),
                       b.loc[t, cols].astype(float))

    print("R5 CODE-SELBSTTEST: PASS")

def load(coin):
    folder = BASE / f"{coin}_USDT/5m"
    files = sorted(folder.glob("*.parquet"))
    files = [p for p in files
             if p.name.split("_5m_")[1][:7] <= "2026-06"]
    if not files:
        raise ValueError(f"Keine Daten: {coin}")

    df = pd.concat([
        pd.read_parquet(
            p, columns=["open_time","close",
                        "is_closed","price_source"]
        )
        for p in files
    ], ignore_index=True)

    if not df.is_closed.eq(True).all():
        raise ValueError("Offene Kerzen")
    if not df.price_source.eq("last_trade").all():
        raise ValueError("Falsche Preisquelle")

    df["time"] = pd.to_datetime(df.open_time, utc=True)
    df = df.set_index("time").sort_index()
    if df.index.has_duplicates:
        raise ValueError("Doppelte Zeitstempel")
    if not (df.index.to_series().diff().dropna() ==
            pd.Timedelta(minutes=5)).all():
        raise ValueError("Zeitlücke")

    s = pd.to_numeric(df.close, errors="raise")
    if not np.isfinite(s).all() or (s <= 0).any():
        raise ValueError("Ungültige Preise")
    return s.rename(coin)

def run():
    checks = {
        "00_FORSCHUNGSDESIGN.md":
        "83e4b71e0046a43d59bdbc18f896704019c2e616af9231b4e40d00f6c71d7bff",
        "02_METHODENPROTOKOLL.md":
        "d0927b9a77f7642c10662e7e39e957fe499a8d0f68b68386d62961acecfa15f1"
    }
    for name, digest in checks.items():
        p = R/name
        if not p.is_file() or hashlib.sha256(
                p.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Protokoll verändert: {name}")

    frame = pd.concat(
        [load("BTC"), load("ETH")],
        axis=1, join="inner"
    )
    if not (frame.index.to_series().diff().dropna() ==
            pd.Timedelta(minutes=5)).all():
        raise ValueError("BTC/ETH nicht synchron")

    data = features(frame)
    bcols = ["intercept","ETH12","ETH288","ETH2016"]
    mcols = bcols + ["BTC12","BTC288","BTC2016"]
    records = []
    months = []

    for start in pd.date_range(
            FIRST, END, freq="MS", inclusive="left"):
        finish = start + pd.DateOffset(months=1)
        train = data[
            (data.index >= START) &
            (data.available <= start)
        ]
        test = data[
            (data.index >= start) &
            (data.index < finish) &
            (data.available <= END)
        ]
        if len(train) < 1000 or len(test) < 100:
            raise ValueError(f"Zu wenig Daten: {start}")

        ytr = train.target.to_numpy(dtype=float)
        yte = test.target.to_numpy(dtype=float)
        forecasts = {
            "B0": np.full(len(test), ytr.mean())
        }
        for name, cols in (("B1",bcols),("M1",mcols)):
            coef = np.linalg.lstsq(
                train[cols].to_numpy(dtype=float),
                ytr, rcond=None
            )[0]
            forecasts[name] = (
                test[cols].to_numpy(dtype=float) @ coef
            )

        for i, t in enumerate(test.index):
            records.append([
                t, yte[i], forecasts["B0"][i],
                forecasts["B1"][i], forecasts["M1"][i]
            ])
        months.append(str(start.date()))

    p = pd.DataFrame(
        records, columns=["time","y","B0","B1","M1"]
    ).set_index("time")
    if p.empty or p.index.has_duplicates:
        raise ValueError("Ungültige Prognosezeitachse")

    e0 = (p.y-p.B0).to_numpy()
    e1 = (p.y-p.B1).to_numpy()
    e2 = (p.y-p.M1).to_numpy()
    mse = [float(np.mean(e*e))
           for e in (e0,e1,e2)]
    improvement = 100*(mse[1]-mse[2])/mse[1]

    week = p.index.strftime("%G-W%V")
    groups = [
        np.flatnonzero(week == w)
        for w in pd.unique(week)
    ]
    k = len(groups)
    if k < 8:
        raise ValueError("Zu wenige Wochen")

    rng = np.random.default_rng(20261114)
    boot = []
    for _ in range(2000):
        selected = []
        while len(selected) < k:
            j = int(rng.integers(0,k-3))
            selected.extend(range(j,j+4))
        ix = np.concatenate([
            groups[j] for j in selected[:k]
        ])
        a = np.mean(e1[ix]**2)
        b = np.mean(e2[ix]**2)
        boot.append(100*(a-b)/a)
    ci = np.percentile(boot,[2.5,97.5])

    cw = e1**2-e2**2+(
        p.B1.to_numpy()-p.M1.to_numpy()
    )**2
    fit = sm.OLS(cw,np.ones((len(cw),1))).fit(
        cov_type="HAC",cov_kwds={"maxlags":4}
    )
    z = float(fit.tvalues[0])
    pv = float(norm.sf(z))

    lines = [
        "R5 BTC -> ETH VOLATILITAET",
        "STATUS: EXPLORATIV, KEIN BLINDTEST",
        f"Prognosen: {len(p)}",
        f"Evaluationsmonate: {len(months)}",
        f"Kalenderwochen: {k}",
        f"MSE B0: {mse[0]:.10g}",
        f"MSE B1: {mse[1]:.10g}",
        f"MSE M1: {mse[2]:.10g}",
        f"Relative MSE-Verbesserung: {improvement:+.5f} %",
        f"95%-Bootstrap-Intervall: [{ci[0]:+.5f}, {ci[1]:+.5f}] %",
        f"Clark-West HAC z: {z:+.4f}",
        f"Clark-West einseitig p: {pv:.6g}",
        "",
        "Keine Handelsprofitabilitaet nachgewiesen.",
        "Bootstrap-Inferenz approximativ.",
        "Keine nachtraegliche Parametersuche."
    ]

    path = R/"R5_ERGEBNIS.txt"
    with path.open("x") as f:
        f.write("\n".join(lines)+"\n")
    print("\n".join(lines))
    print("BERICHT:", path)

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        run()
