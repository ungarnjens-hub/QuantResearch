from pathlib import Path
import os, hashlib, calendar
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm

r = Path(os.environ["R"])
root = Path.home() / "Dokumente/TradingLab/data/canonical/binance/perpetual/klines"

expected = {
    "R4_FORSCHUNGSPROTOKOLL_FINAL.md":
    "832d6ea1d487943e7bb01acba1dfe7b6f0fad2e09cefc02769ff442c2be0453c",
    "R4_STATISTIK_ERGAENZUNG.md":
    "6a6fcc9d8181043b3bb9301892815e1ee17e0696f00853f3674e51ec10e7afc5"
}
for name, digest in expected.items():
    p = r / name
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
        raise SystemExit("STOP: Protokollprüfung fehlgeschlagen: " + name)

def load(coin):
    folder = root / f"{coin}_USDT/5m"
    files = sorted(
        p for p in folder.glob("*.parquet")
        if p.name.split("_5m_")[1][:7] <= "2026-06"
    )
    if not files:
        raise ValueError(f"Dateien fehlen: {coin}")
    frames = []
    for p in files:
        d = pd.read_parquet(
            p, columns=["open_time","close_time","close",
                        "is_closed","price_source"]
        )
        if not d["is_closed"].eq(True).all():
            raise ValueError("Offene Kerzen")
        if not d["price_source"].eq("last_trade").all():
            raise ValueError("Falsche Preisquelle")
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["time"] = pd.to_datetime(df.open_time, utc=True)
    end = pd.to_datetime(df.close_time, utc=True)
    if not ((end-df.time) == pd.Timedelta(milliseconds=299999)).all():
        raise ValueError("Kerzenabschluss fehlerhaft")
    df["close"] = pd.to_numeric(df["close"], errors="raise")
    if not np.isfinite(df["close"]).all() or (df["close"] <= 0).any():
        raise ValueError("Ungültige Schlusskurse")
    df = df.set_index("time").sort_index()
    if df.index.has_duplicates:
        raise ValueError("Doppelte Zeitstempel")
    if not (df.index.to_series().diff().dropna()
            == pd.Timedelta(minutes=5)).all():
        raise ValueError("Zeitlücken")
    return df["close"].rename(coin)

btc, eth = load("BTC"), load("ETH")
d = pd.concat([btc, eth], axis=1, join="inner")
if not (d.index.to_series().diff().dropna()
        == pd.Timedelta(minutes=5)).all():
    raise ValueError("Gemeinsame Zeitachse lückenhaft")

ret = np.log(d / d.shift(1))
x = pd.DataFrame(index=d.index)
x["intercept"] = 1.0
for lag in range(3):
    x[f"eth{lag}"] = ret["ETH"].shift(lag)
    x[f"btc{lag}"] = ret["BTC"].shift(lag)
y = ret["ETH"].shift(-1)

data = x.copy()
data["target"] = y
data["target_time"] = pd.Series(
    d.index, index=d.index
).shift(-1)
data = data.dropna()

# Spaltenreihenfolge explizit fixieren.
base_cols = ["intercept","eth0","eth1","eth2"]
full_cols = base_cols + ["btc0","btc1","btc2"]

records = []
monthly = []

for year in (2025, 2026):
    for month in range(1, 13):
        start = pd.Timestamp(year, month, 1, tz="UTC")
        if not (pd.Timestamp("2025-03-01", tz="UTC") <= start
                < pd.Timestamp("2026-07-01", tz="UTC")):
            continue

        finish = start + pd.DateOffset(months=1)
        train = data[
            (data.index >= pd.Timestamp("2024-09-01", tz="UTC")) &
            (data["target_time"] < start)
        ]
        test = data[(data.index >= start) & (data.index < finish)]
        if len(train) < 10000 or len(test) < 1000:
            raise ValueError(f"Zu wenig Beobachtungen: {start}")

        predictions = {}
        for name, cols in (("B1", base_cols), ("M1", full_cols)):
            a = train[cols].to_numpy(dtype=float)
            b = train["target"].to_numpy(dtype=float)
            coef = np.linalg.lstsq(a, b, rcond=None)[0]
            predictions[name] = test[cols].to_numpy(dtype=float) @ coef

        actual = test["target"].to_numpy(dtype=float)
        f0 = np.zeros(len(test))
        f1, f2 = predictions["B1"], predictions["M1"]
        for i, t in enumerate(test.index):
            records.append((t, actual[i], f0[i], f1[i], f2[i]))
        monthly.append((str(start.date()), len(test),
                        float(np.mean((actual-f1)**2)),
                        float(np.mean((actual-f2)**2))))

p = pd.DataFrame(
    records, columns=["time","y","B0","B1","M1"]
).set_index("time")
if p.index.has_duplicates or not p.index.is_monotonic_increasing:
    raise ValueError("Prognosezeitachse ungültig")

e0 = (p.y-p.B0).to_numpy()
e1 = (p.y-p.B1).to_numpy()
e2 = (p.y-p.M1).to_numpy()
mse0, mse1, mse2 = [float(np.mean(e**2)) for e in (e0,e1,e2)]
delta = mse1-mse2
relative = 100*delta/mse1

# Vier-Wochen-Moving-Block-Bootstrap.
week_id = p.index.strftime("%G-W%V")
groups = [
    np.flatnonzero(week_id == w)
    for w in pd.unique(week_id)
]
k = len(groups)
if k < 8:
    raise ValueError("Zu wenige Wochen")

rng = np.random.default_rng(20261114)
boot = np.empty(2000)
for j in range(2000):
    selected = []
    while len(selected) < k:
        start = int(rng.integers(0,k-3))
        selected.extend(range(start,start+4))
    idx = np.concatenate([groups[z] for z in selected[:k]])
    a = np.mean(e1[idx]**2)
    b = np.mean(e2[idx]**2)
    boot[j] = 100*(a-b)/a

ci = np.percentile(boot,[2.5,97.5])

# Sekundärer Clark-West-Vergleich.
cw = e1**2-e2**2+(p.B1.to_numpy()-p.M1.to_numpy())**2
fit = sm.OLS(cw,np.ones((len(cw),1))).fit(
    cov_type="HAC",cov_kwds={"maxlags":12}
)
stat = float(fit.tvalues[0])
pvalue = float(norm.sf(stat))

lines = [
    "R4 BTC-ETH LEAD-LAG | EXPLORATIVE FORSCHUNG",
    "Kein unabhängiger Blindtest; keine Handelsprofitabilität.",
    f"Prognosen: {len(p)}",
    f"Evaluationsmonate: {len(monthly)}",
    f"Kalenderwochen: {k}",
    f"MSE B0: {mse0:.12g}",
    f"MSE B1: {mse1:.12g}",
    f"MSE M1: {mse2:.12g}",
    f"Delta B1-M1: {delta:.12g}",
    f"Relative MSE-Verbesserung: {relative:+.5f} %",
    f"95%-Blockbootstrap-Intervall: [{ci[0]:+.5f}, {ci[1]:+.5f}] %",
    f"Clark-West HAC z: {stat:+.4f}",
    f"Clark-West einseitig p (asymptotisch): {pvalue:.6g}",
    "",
    "Monat | N | MSE B1 | MSE M1",
]
lines += [
    f"{a} | {n} | {b:.9g} | {c:.9g}"
    for a,n,b,c in monthly
]
lines += [
    "",
    "Bewertung: Explorativ, historisch bereits betrachtete Daten.",
    "Bootstrap berücksichtigt Zeitabhängigkeit nur approximativ.",
    "CW-Inferenz ist ergänzend und asymptotisch.",
    "Keine zusätzliche Parametersuche nach dieser Auswertung."
]

report = r / "R4_ERGEBNIS.txt"
with report.open("x") as f:
    f.write("\n".join(lines)+"\n")
print("\n".join(lines))
print("\nBERICHT:", report)
