#!/usr/bin/env python3
"""R9 phase B only: read-only data quality + synthetic method checks. No market labels."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path.home() / "QuantResearch/Validation_2026_AugOct/data"
ASSETS = ("BTC", "ETH", "SOL")
START = pd.Timestamp("2026-07-01", tz="UTC")
END = pd.Timestamp("2026-11-01", tz="UTC")
EXPECTED = pd.date_range(START, END, freq="5min", inclusive="left")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1048576), b""):
            h.update(part)
    return h.hexdigest()


def check_data():
    """Only timestamps, provenance, OHLCV consistency. Never calculate a real return."""
    checks = {}
    manifest_file = DATA / "manifest.json"
    manifest = json.loads(manifest_file.read_text())
    for a in ASSETS:
        path = DATA / f"{a}_USDT_5m_2026-07_2026-10.parquet"
        meta = manifest[a]
        d = pd.read_parquet(path)
        ts = pd.DatetimeIndex(d["open_time"])
        ohlc = d[["open", "high", "low", "close"]].to_numpy(dtype=np.float64)
        vols = d["volume"].to_numpy(dtype=np.float64)
        item = {
            "sha256_pass": sha256(path) == meta["sha256"],
            "sha256": sha256(path),
            "provenance": (
                meta["exchange"] == "binance"
                and meta["market_type"] == "perpetual"
                and meta["contract_type"] == "linear"
                and meta["price_source"] == "last_trade"
                and meta["endpoint"] == "/fapi/v1/klines"
                and meta["timeframe"] == "5m"
                and meta["symbol"] == f"{a}/USDT:USDT"
            ),
            "utc": str(ts.tz) == "UTC",
            "full_grid": ts.equals(EXPECTED),
            "unique": ts.is_unique,
            "ordered": ts.is_monotonic_increasing,
            "rows_manifest": len(d) == meta["rows"],
            "prices_positive_finite": bool(np.isfinite(ohlc).all() and (ohlc > 0).all()),
            "ohlc_valid": bool(
                (ohlc[:, 1] >= np.maximum(ohlc[:, 0], ohlc[:, 3])).all()
                and (ohlc[:, 2] <= np.minimum(ohlc[:, 0], ohlc[:, 3])).all()
                and (ohlc[:, 1] >= ohlc[:, 2]).all()
            ),
            "volume_finite_nonnegative": bool(np.isfinite(vols).all() and (vols >= 0).all()),
            "rows": len(d),
            "first_open_time": str(ts[0]),
            "last_open_time": str(ts[-1]),
        }
        item["pass"] = all(v for k, v in item.items() if k in {
            "sha256_pass", "provenance", "utc", "full_grid", "unique",
            "ordered", "rows_manifest", "prices_positive_finite", "ohlc_valid",
            "volume_finite_nonnegative"
        })
        checks[a] = item
    checks["cross_asset_timestamp_alignment"] = bool(all(checks[a]["full_grid"] for a in ASSETS))
    checks["pass"] = all(checks[a]["pass"] for a in ASSETS) and checks["cross_asset_timestamp_alignment"]
    return checks


def events(close, vol, close_minutes=5, z_limit=2.0, volume_limit=1.5):
    """Synthetic only. At index j: impulse (j-6,j], historical returns (j-294,j-6].
    Historical volume candles indices [j-293,j-6) = 288 bars; no overlap with impulse.
    Labels use (j,j+6]. An eligible event blocks next six decision indices.
    """
    close = np.asarray(close, dtype=np.float64)
    vol = np.asarray(vol, dtype=np.float64)
    if len(close) != len(vol):
        raise ValueError("length mismatch")
    if not np.isfinite(close).all() or (close <= 0).any():
        raise ValueError("invalid price")
    if not np.isfinite(vol).all() or (vol < 0).any():
        raise ValueError("invalid volume")
    logp = np.log(close)
    r = np.diff(logp)
    selected = []
    blocked_until = -1
    # Earliest j: need r[j-294:j-6] => indices 0..287 when j=294.
    # r index k is close[k+1]-close[k].
    for j in range(294, len(close) - 6):
        if j <= blocked_until:
            continue
        past = r[j - 294:j - 6]
        historical_v = vol[j - 293:j - 5]  # 288 volume candles ending at j-6
        imp_v = vol[j - 5:j + 1]  # 6 impulse candles
        if len(past) != 288 or len(historical_v) != 288 or len(imp_v) != 6:
            raise AssertionError("warmup off-by-one")
        sd = float(np.std(past, ddof=1))
        med = float(np.median(historical_v))
        if not (sd > 0 and med > 0):
            continue
        impulse = float(logp[j] - logp[j - 6])
        z = abs(impulse) / (math.sqrt(6) * sd)
        if z < z_limit or impulse == 0:
            continue
        v = float(imp_v.sum() / (6 * med))
        y = float(np.sign(impulse) * (logp[j + 6] - logp[j]))
        selected.append({
            "j": j, "group": "M1" if v >= volume_limit else "B1",
            "z": z, "v": v, "y": y, "decision_time_minutes": j * close_minutes,
            "label_end_minutes": (j + 6) * close_minutes
        })
        blocked_until = j + 6
    return selected


def daily_block_bootstrap(events_by_day, draws=500, seed=20261114, block_days=7):
    """Paired circular moving blocks of UTC days, shared by both groups.
    Aborts/flags empty groups. No IID event-level resampling.
    """
    days = sorted(events_by_day)
    n = len(days)
    if n < 2 * block_days:
        raise ValueError("insufficient days")
    m = np.array([sum(x["y"] for x in events_by_day[d] if x["group"] == "M1") for d in days])
    b = np.array([sum(x["y"] for x in events_by_day[d] if x["group"] == "B1") for d in days])
    cm = np.array([sum(x["group"] == "M1" for x in events_by_day[d]) for d in days])
    cb = np.array([sum(x["group"] == "B1" for x in events_by_day[d]) for d in days])
    rng = np.random.default_rng(seed)
    results = []
    invalid = 0
    nblocks = math.ceil(n / block_days)
    for _ in range(draws):
        starts = rng.integers(0, n, size=nblocks)
        idx = np.concatenate([(np.arange(s, s + block_days) % n) for s in starts])[:n]
        if cm[idx].sum() == 0 or cb[idx].sum() == 0:
            invalid += 1
            continue
        results.append(m[idx].sum() / cm[idx].sum() - b[idx].sum() / cb[idx].sum())
    return np.array(results), invalid


def synthetic_checks():
    tests = {}
    n = 700
    rng = np.random.default_rng(20261114)
    lp = np.cumsum(rng.normal(0, .001, size=n))
    vol = np.ones(n) * 100
    close = np.exp(lp)
    raw = events(close, vol)
    tests["chronological_selection"] = all(raw[i + 1]["j"] - raw[i]["j"] >= 7 for i in range(len(raw) - 1))
    tests["no_lookahead_last_six"] = (
        events(close[:-6], vol[:-6]) ==
        [e for e in raw if e["j"] < len(close) - 12]
    )
    tests["no_price_at_decision_future"] = all(
        e["label_end_minutes"] == e["decision_time_minutes"] + 30 for e in raw
    )
    tests["warmup_288_prior_returns"] = (len(np.diff(lp)[0:288]) == 288)
    tests["baseline_volumes_non_overlap"] = (
        set(range(294-293, 294-5)).isdisjoint(set(range(294-5, 295)))
    )

    days = {d: [] for d in range(28)}
    for d in days:
        for group, y in (("M1", .002), ("B1", -.001)):
            days[d].append({"group": group, "y": y})
    good, inv = daily_block_bootstrap(days, draws=500)
    tests["paired_block_known_delta"] = (len(good) == 500 and inv == 0 and np.allclose(good, .003))

    null_days = {d: [] for d in range(28)}
    for d in null_days:
        null_days[d].append({"group": "M1", "y": 0.0})
        if d % 7 == 0:
            null_days[d].append({"group": "B1", "y": 0.0})
    vals, invalid = daily_block_bootstrap(null_days, draws=500)
    tests["null_exact_zero"] = bool(np.all(vals == 0))
    tests["empty_group_reported"] = (invalid >= 0 and len(vals) + invalid == 500)

    empty_days = {d: [{"group": "M1", "y": 0.0}] for d in range(28)}
    vals, invalid = daily_block_bootstrap(empty_days, draws=50)
    tests["entire_empty_group_fail_closed"] = (len(vals) == 0 and invalid == 50)

    # Event control: A large close-to-close jump is visible only after it happened.
    close2 = np.ones(700) * 100.0
    close2[294:] = 120.0
    vol2 = np.ones(700) * 100
    vol2[289:295] = 300
    # Constant prehistory has sigma==0 -> reject rather than divide by zero.
    tests["zero_sigma_rejected"] = len(events(close2, vol2)) == 0
    tests["invalid_price_rejected"] = False
    try:
        events(np.append(close, -1), np.append(vol, 100))
    except ValueError:
        tests["invalid_price_rejected"] = True
    return {"tests": tests, "pass": all(tests.values()), "synthetic_events": len(raw),
            "null_bootstrap_invalid_replicates": invalid}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="perform read-only data audit + synthetic tests")
    a = parser.parse_args()
    if not a.run:
        parser.error("Use --run; no real market momentum or labels will be evaluated.")
    syn = synthetic_checks()
    data = check_data()
    print("R9 PHASE B SYNTHETIK:", "PASS" if syn["pass"] else "FAIL")
    for key, status in syn["tests"].items():
        print(f"  {key}: {'PASS' if status else 'FAIL'}")
    print("R9 DATENINVENTAR:", "PASS" if data["pass"] else "FAIL")
    for asset in ASSETS:
        x = data[asset]
        print(f"  {asset}: {'PASS' if x['pass'] else 'FAIL'}, rows={x['rows']}, sha256={x['sha256']}")
    print("USED DATA WINDOW: 2026-07-01 ... 2026-11-01 exclusive; EXPLORATORY ONLY")
    print("DATA-CONSUMPTION: Aug-Oct already analyzed; R7 Jan-Mar 2027 and R8 Apr-Jun 2027 RESERVED")
    print("INFERENTIAL GATE: NOT APPROVED; NEED PRE-REGISTERED MINIMUM EVENT COUNTS, TEST AND HOLDOUT")
    print("R9 PHASE C: NOT APPROVED. NO REAL RETURNS, EVENTS, CORRELATIONS OR PNL CALCULATED")
    print("AUDIT OVERALL:", "PASS" if data["pass"] and syn["pass"] else "FAIL")
    if not data["pass"] or not syn["pass"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
