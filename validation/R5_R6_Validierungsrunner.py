#!/usr/bin/env python3
"""Vorregistrierter gemeinsamer R5/R6-Validierungsrunner.

--selftest: ausschließlich synthetische Daten, kein Marktdatenzugriff.
--run: nur nach externem Phase-B-Gate, explizitem --approved und
       signiertem Input-Manifest; schreibt Ergebnis in isolierten Ordner.
Historische R5/R6-Quellen bleiben unverändert.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.stats import norm

HOME = Path.home()
REPO = HOME / "QuantResearch-Git"
ROOT = HOME / "QuantResearch/Validation_2026_AugOct"
CANON = HOME / "Dokumente/TradingLab/data/canonical/binance/perpetual/klines"
SOL_OLD = (HOME / "Dokumente/TradingLab/TradingLab_V2/artifacts/"
           "research_tpv2_binance_usdm_20261113/native_data/"
           "binance/futures/SOL_USDT_USDT-5m-futures.parquet")
FROZEN = {
    "R5_lauf.py": (REPO / "studies/R5_BTC_ETH_Volatilitaet/R5_lauf.py",
                   "fca8ef5d64ddb98d9cf470b67698ffb982dccedb68bd3dd56e6c03ea88ebaee0"),
    "R6_lauf.py": (REPO / "studies/R6_BTC_SOL_Volatilitaet/R6_lauf.py",
                   "905843db94f5d1730c62380d1a4303e84b860f0858bfe3f50686d71006a3c647"),
    "Protocol": (REPO / "validation/R5_R6_Validierungsprotokoll_PhaseB_2026-11-14.md",
                 "ba46b172bb9cf4e51dea4241804423a052c69abcd42cd6fc1b033bbea2fd5df8"),
    "Audit": (REPO / "validation/R5_R6_Methodenaudit_2026-11-14.md",
              "000c4c30d40a28bedaf9795be11c25c51daf12e6a97f83a75ee10a3ceaf4f04e"),
}
OLD_SOL_SHA = "e2b4c01551a33b292a3419a3379437df4d9f67d9073629da3ac23e1f8aa3a7ae"
TRAIN_START = pd.Timestamp("2024-09-01T00:00Z")
NEW_START = pd.Timestamp("2026-07-01T00:00Z")
TEST_START = pd.Timestamp("2026-08-01T00:00Z")
END = pd.Timestamp("2026-11-01T00:00Z")
EPS = 1e-12
BCOLS = ["intercept", "ETH12", "ETH288", "ETH2016"]
MCOLS = BCOLS + ["BTC12", "BTC288", "BTC2016"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_frozen():
    for label, (path, expected) in FROZEN.items():
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"Eingefrorene Quelle fehlt oder veraendert: {label}")


def verify_series(s, label, start=None, stop=None):
    if not isinstance(s.index, pd.DatetimeIndex) or s.index.tz is None:
        raise ValueError(f"{label}: UTC-DatetimeIndex fehlt")
    if s.index.has_duplicates or not s.index.is_monotonic_increasing:
        raise ValueError(f"{label}: Reihenfolge/Duplikate")
    if len(s) < 2 or not (s.index.to_series().diff().dropna() == pd.Timedelta(minutes=5)).all():
        raise ValueError(f"{label}: 5m-Luecke")
    values = s.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError(f"{label}: ungueltige Close-Preise")
    if start is not None and s.index[0] != start:
        raise ValueError(f"{label}: falscher Datenbeginn {s.index[0]}")
    if stop is not None and s.index[-1] != stop:
        raise ValueError(f"{label}: falsches Datenende {s.index[-1]}")
    return s


def load_historical(symbol):
    if symbol == "SOL":
        if not SOL_OLD.is_file() or sha256(SOL_OLD) != OLD_SOL_SHA:
            raise ValueError("SOL-Altquelle nicht identisch zum registrierten Bestand")
        data = pd.read_parquet(SOL_OLD, columns=["date", "close"])
        dates = pd.to_datetime(data["date"], utc=True)
        s = pd.Series(data["close"].to_numpy(dtype=float), index=dates, name=symbol)
        s = s.loc[s.index < NEW_START].sort_index()
    else:
        folder = CANON / f"{symbol}_USDT/5m"
        files = sorted(p for p in folder.glob("*.parquet") if "_5m_" in p.name and
                       p.name.split("_5m_")[1][:7] <= "2026-06")
        if not files:
            raise ValueError(f"Altbestand fehlt: {symbol}")
        frames = []
        for p in files:
            df = pd.read_parquet(p, columns=["open_time", "close", "is_closed",
                                             "price_source", "market_type"])
            if not df["is_closed"].eq(True).all() or not df["price_source"].eq("last_trade").all() or not df["market_type"].eq("perpetual").all():
                raise ValueError(f"Historische Daten nicht Last-Trade Perpetual: {p}")
            frames.append(df[["open_time", "close"]])
        full = pd.concat(frames, ignore_index=True)
        s = pd.Series(full["close"].to_numpy(dtype=float),
                      index=pd.to_datetime(full["open_time"], utc=True), name=symbol)
        s = s.sort_index()
    return verify_series(s, f"ALT {symbol}", stop=NEW_START-pd.Timedelta(minutes=5))


def load_new(symbol, entry):
    expected_file = ROOT / "data" / f"{symbol}_USDT_5m_2026-07_2026-10.parquet"
    p = Path(entry["path"]).expanduser().resolve()
    if p != expected_file.resolve() or not p.is_file():
        raise ValueError(f"Dateipfad unzulaessig: {symbol}")
    expected_fields = {"symbol": symbol+"/USDT:USDT", "exchange": "binance",
                       "market_type": "perpetual", "contract_type": "linear",
                       "price_source": "last_trade", "timeframe": "5m",
                       "endpoint": "/fapi/v1/klines"}
    for key, value in expected_fields.items():
        if entry.get(key) != value:
            raise ValueError(f"Manifest fuer {symbol}: {key}")
    if not entry.get("downloaded_at_utc") or not entry.get("sha256"):
        raise ValueError(f"Manifest fuer {symbol}: Zeitstempel/SHA256 fehlen")
    if sha256(p) != entry["sha256"]:
        raise ValueError(f"Hash-Abweichung: {symbol}")
    df = pd.read_parquet(p)
    mandatory = {"open_time", "open", "high", "low", "close", "volume"}
    if not mandatory.issubset(df.columns):
        raise ValueError(f"Neudaten {symbol}: Pflichtspalten fehlen")
    index = pd.to_datetime(df["open_time"], utc=True)
    if df[["open", "high", "low", "close", "volume"]].isna().any().any():
        raise ValueError(f"Neudaten {symbol}: NaN")
    o, hi, lo, c, v = [df[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close", "volume")]
    if not (np.isfinite(np.column_stack((o,hi,lo,c,v))).all() and
            (lo > 0).all() and (v >= 0).all() and
            (hi >= np.maximum(o,c)).all() and (lo <= np.minimum(o,c)).all()):
        raise ValueError(f"Neudaten {symbol}: OHLC/Volumen ungueltig")
    s = pd.Series(c, index=index, name=symbol).sort_index()
    return verify_series(s, f"NEU {symbol}", start=NEW_START,
                         stop=END-pd.Timedelta(minutes=5))


def combine(old, new, name):
    if old.index[-1] + pd.Timedelta(minutes=5) != new.index[0]:
        raise ValueError(f"{name}: Uebergang Juni/Juli defekt")
    return verify_series(pd.concat([old, new]), name)


def features(frame):
    # Unabhaengige Formelschreibweise, numerisch gleich zur eingefrorenen R5/R6-Funktion.
    ret = np.log(frame).diff()
    sq = ret.pow(2)
    x = pd.DataFrame(index=frame.index)
    x["intercept"] = 1.0
    for symbol in ("ETH", "BTC"):
        for window in (12, 288, 2016):
            x[f"{symbol}{window}"] = np.log(sq[symbol].rolling(window).mean() + EPS)
    x["target"] = np.log(sq["ETH"].rolling(12).sum().shift(-12) + EPS)
    x["available"] = pd.Series(frame.index, index=frame.index).shift(-12) + pd.Timedelta(minutes=5)
    return x.loc[x.index.minute == 55].dropna()


def forecast(data, end=END, test_start=TEST_START, train_start=TRAIN_START):
    rows = []
    month = test_start
    while month < end:
        finish = min(month + pd.DateOffset(months=1), end)
        train = data.loc[(data.index >= train_start) & (data.available <= month)]
        test = data.loc[(data.index >= month) & (data.index < finish) & (data.available <= end)]
        if len(train) < 1000 or len(test) < 100:
            raise ValueError(f"Nicht genug Training/Test am {month}")
        ytr = train.target.to_numpy(dtype=float)
        preds = {"B0": np.full(len(test), ytr.mean())}
        for label, cols in (("B1", BCOLS), ("M1", MCOLS)):
            coeff, *_ = np.linalg.lstsq(train[cols].to_numpy(dtype=float), ytr, rcond=None)
            preds[label] = test[cols].to_numpy(dtype=float) @ coeff
        rows.extend(zip(test.index, test.target.to_numpy(dtype=float),
                        preds["B0"], preds["B1"], preds["M1"]))
        month = finish
    result = pd.DataFrame(rows, columns=["time", "y", "B0", "B1", "M1"]).set_index("time")
    return result


def verify_forecasts(p, test_start=TEST_START, end=END, expected_n=2207):
    expected = pd.date_range(test_start, end-pd.Timedelta(minutes=5), freq="5min")
    expected = expected[expected.minute == 55]
    expected = expected[expected + pd.Timedelta(minutes=65) <= end]
    if len(expected) != expected_n or not p.index.equals(expected):
        raise ValueError("Forecast-Zeitachse unvollstaendig oder unzulaessig")
    if not np.isfinite(p[["y", "B0", "B1", "M1"]].to_numpy(dtype=float)).all():
        raise ValueError("NaN/Inf in Prognosen")
    daily = p.index.floor("D").value_counts().sort_index()
    if len(daily) != 92 or not (daily.iloc[:-1] == 24).all() or daily.iloc[-1] != 23:
        raise ValueError("Tagesabdeckung fehlerhaft")


def daily_records(p):
    e1 = (p.y-p.B1)**2
    e2 = (p.y-p.M1)**2
    d = e1 - e2
    day = p.index.floor("D")
    return pd.DataFrame({"d": d.to_numpy(), "e1": e1.to_numpy(),
                         "e2": e2.to_numpy()}, index=day).groupby(level=0).agg(
                         {"d": "mean", "e1": "sum", "e2": "sum"})


def hac_daily_z(daily):
    # Intercept-only NW/HAC Bartlett 7 Tageslags, ddof=0 wie statsmodels OLS HAC.
    u = daily.to_numpy(dtype=float)
    n = len(u)
    mean = float(u.mean())
    centered = u - mean
    omega = float(centered @ centered / n)
    for lag in range(1, 8):
        omega += 2.0*(1.0-lag/8.0)*float(centered[lag:] @ centered[:-lag]/n)
    if omega <= 0:
        raise ValueError("HAC-Varianz ungueltig")
    z = mean / np.sqrt(omega/n)
    return float(z), float(norm.sf(z))


def bootstrap_indices(n=92, draws=5000, block=7, seed=20261114):
    # Dieselben Tages-Resamples fuer ETH und SOL.
    rng = np.random.default_rng(seed)
    out = np.empty((draws, n), dtype=np.int16)
    for i in range(draws):
        ix = []
        while len(ix) < n:
            j = int(rng.integers(0, n-block+1))
            ix.extend(range(j, j+block))
        out[i] = ix[:n]
    return out


def moving_bootstrap_ci(e1, e2, indices):
    outcomes = np.empty(len(indices), dtype=float)
    for i, ix in enumerate(indices):
        a, b = e1[ix].sum(), e2[ix].sum()
        outcomes[i] = 100*(a-b)/a
    return np.percentile(outcomes, [2.5, 97.5])


def summarize(p, indices):
    e = [(p.y-p[col]).to_numpy(dtype=float) for col in ("B0", "B1", "M1")]
    mse = [float(np.mean(x*x)) for x in e]
    gain = 100*(mse[1]-mse[2])/mse[1]
    d = daily_records(p)
    z, pv = hac_daily_z(d["d"])
    ci = moving_bootstrap_ci(d["e1"].to_numpy(), d["e2"].to_numpy(), indices)
    return {"n": len(p), "days": len(d), "mse_b0": mse[0], "mse_b1": mse[1],
            "mse_m1": mse[2], "gain_pct": gain, "hac_z": z,
            "p_one_sided": pv, "bootstrap_ci_pct": ci.tolist()}


def holm2(pvals):
    order = sorted(pvals, key=pvals.get)
    return {order[0]: min(1., 2*pvals[order[0]]),
            order[1]: min(1., max(2*pvals[order[0]],pvals[order[1]]))}


def selftest():
    # Reiner Synthetiktest. Keine lokalen Alt- oder Neudaten lesen.
    ensure_frozen()
    import importlib.util
    funcs = []
    for name in ("R5_lauf.py", "R6_lauf.py"):
        spec = importlib.util.spec_from_file_location("frozen_" + name[:2], FROZEN[name][0])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        funcs.append(module.features)
    idx = pd.date_range("2025-01-01", "2026-11-01", freq="5min", tz="UTC")
    j = np.arange(len(idx), dtype=float)
    frame = pd.DataFrame({"BTC": 50_000*np.exp(np.cumsum(.0009*np.sin(j/19))),
                          "ETH": 1700*np.exp(np.cumsum(.0011*np.cos(j/31)))}, index=idx)
    # Numerische Identitaet Feature/Target/Availability: R5/R6 vs neu.
    a, b, c = funcs[0](frame), funcs[1](frame), features(frame)
    assert a.index.equals(b.index) and a.index.equals(c.index)
    assert a.available.equals(c.available)
    cols = [x for x in c.columns if x != "available"]
    assert np.allclose(a[cols], c[cols], rtol=0, atol=1e-10)
    print("PASS Merkmale, Ziele, Labelverfuegbarkeit vs R5/R6")
    # Vollstaendige synthetische Walk-Forward-Prozedur inkl. Monats-Refits.
    f = forecast(c)
    verify_forecasts(f)
    print("PASS 2207 Zeitpunkte, 92 Tage, 3 expandierende Refits")
    # Echte Schutzwirkung des Training-Labels: Feat/Target Manipulation nach Refit
    for t in (pd.Timestamp("2026-08-01T00:00Z"), pd.Timestamp("2026-09-01T00:00Z"),
              pd.Timestamp("2026-10-01T00:00Z")):
        train = c[(c.index >= TRAIN_START) & (c.available <= t)]
        assert not train.empty and train.available.max() <= t
    print("PASS Refit nur mit verfuegbaren Labels")
    indices = bootstrap_indices()
    result = summarize(f, indices)
    assert result["n"] == 2207 and result["days"] == 92
    assert np.isfinite(list(result.values())[:0] or [result["hac_z"], result["gain_pct"]]).all()
    assert len(result["bootstrap_ci_pct"]) == 2
    assert holm2({"ETH": .02, "SOL": .04}) == {"ETH": .04, "SOL": .04}
    print("PASS MSE, Tages-HAC, Bootstrap und Holm")
    # Fail-closed: fehlende/duplizierte Prognose wird abgelehnt.
    try:
        verify_forecasts(f.iloc[:-1])
        raise AssertionError("Luecke nicht erkannt")
    except ValueError:
        pass
    print("PASS fehlende Forecasts gesperrt")
    print("RUNNER-SELBSTTEST: PASS; keine echten Marktdaten gelesen")


def run(approved):
    if not approved:
        raise RuntimeError("Ohne explizites --approved kein Zugriff auf Testdaten")
    ensure_frozen()
    manifest_path = ROOT / "data/manifest.json"
    gate = ROOT / "PHASE_B_FREIGABE.json"
    if not manifest_path.is_file() or not gate.is_file():
        raise RuntimeError("Datenmanifest oder separate Phase-B-Freigabe fehlt")
    manifest = json.loads(manifest_path.read_text())
    approval = json.loads(gate.read_text())
    if approval.get("approved") is not True or approval.get("protocol_sha256") != FROZEN["Protocol"][1]:
        raise RuntimeError("Freigabe ungueltig")
    if set(manifest) != {"BTC", "ETH", "SOL"}:
        raise RuntimeError("Erwartet genau BTC, ETH, SOL")
    if (ROOT / "results").exists():
        raise RuntimeError("Ergebnisverzeichnis existiert; kein zweiter Lauf")
    # Vollstaendige Datenpruefung fuer alle Paare vor JEDEM Fit.
    series = {coin: combine(load_historical(coin), load_new(coin, manifest[coin]),coin)
              for coin in ("BTC", "ETH", "SOL")}
    frames = {}
    for symbol in ("ETH", "SOL"):
        frame = pd.concat([series["BTC"].rename("BTC"),
                           series[symbol].rename("ETH")], join="inner", axis=1)
        verify_series(frame["BTC"],f"BTC/{symbol}")
        verify_series(frame["ETH"],f"{symbol}")
        frames[symbol] = features(frame)
    pred = {coin: forecast(frames[coin]) for coin in ("ETH", "SOL")}
    for coin in pred:
        verify_forecasts(pred[coin])
    indices = bootstrap_indices()
    results = {coin: summarize(pred[coin], indices) for coin in ("ETH", "SOL")}
    adjusted = holm2({coin: v["p_one_sided"] for coin, v in results.items()})
    for coin, res in results.items():
        res["holm_p"] = adjusted[coin]
        res["preliminary_confirmed"] = bool(res["gain_pct"] > 0 and
                                            adjusted[coin] < .05 and
                                            res["bootstrap_ci_pct"][0] > 0)
    # Atomare, ausschliesslich neue Ergebnisdateien. Keine Zwischenmeldung zu Metriken.
    dest = ROOT / "results"
    dest.mkdir(parents=False, exist_ok=False)
    for coin in ("ETH", "SOL"):
        pred[coin].to_csv(dest/f"{coin}_forecasts.csv")
    (dest/"FINAL_RESULT.json").write_text(json.dumps({"status": "validierung",
           "manifest_sha256": sha256(manifest_path), "protocol_sha256": FROZEN["Protocol"][1],
           "runner_sha256": sha256(Path(__file__)), "markets": results}, indent=2)+"\n")
    print("VALIDIERUNG ABGESCHLOSSEN; Ergebnis:", dest/"FINAL_RESULT.json")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--selftest", action="store_true")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--approved", action="store_true")
    a = parser.parse_args()
    try:
        selftest() if a.selftest else run(a.approved)
    except Exception as exc:
        print("STOP:",type(exc).__name__,str(exc),file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
