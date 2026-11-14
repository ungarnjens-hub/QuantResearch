#!/usr/bin/env python3
"""R9 Phase B ONLY. Read-only inspection of BTC/ETH futures OHLCV; no returns, events or PnL."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE = Path.home() / "Dokumente/TradingLab/data/canonical/binance/perpetual/klines"
OUT = Path.home() / "QuantResearch/R9_2024_2025_Audit"
START = pd.Timestamp("2024-09-01T00:00:00Z")
END = pd.Timestamp("2026-01-01T00:00:00Z")
MONTHS = pd.period_range("2024-09", "2025-12", freq="M")
EXPECTED = pd.date_range(START, END, freq="5min", inclusive="left")


def digest(file):
    h = hashlib.sha256()
    with file.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def audit_coin(symbol):
    folder = SOURCE / f"{symbol}_USDT/5m"
    files = [folder / f"{symbol}_USDT_5m_{m}_v1.0.parquet" for m in MONTHS]
    outputs = []
    arrays = []
    for m, p in zip(MONTHS, files):
        if not p.is_file():
            raise ValueError(f"{symbol}: missing month {m}: {p}")
        d = pd.read_parquet(p)
        needed = {"open_time", "open", "high", "low", "close", "volume"}
        if not needed.issubset(d.columns):
            raise ValueError(f"{symbol} {m}: columns missing: {needed - set(d.columns)}")
        ts = pd.DatetimeIndex(d["open_time"])
        if str(ts.tz) != "UTC":
            raise ValueError(f"{symbol} {m}: timezone {ts.tz}, expected UTC")
        a = m.to_timestamp(how="start").tz_localize("UTC")
        b = (m + 1).to_timestamp(how="start").tz_localize("UTC")
        ex = pd.date_range(a, b, freq="5min", inclusive="left")
        if not ts.equals(ex):
            raise ValueError(f"{symbol} {m}: missing/extra/disordered time (actual {len(ts)} expected {len(ex)})")
        q = d[["open", "high", "low", "close"]].to_numpy(dtype=float)
        v = d["volume"].to_numpy(dtype=float)
        checks = {
            "positive_finite_ohlc": bool(np.isfinite(q).all() and (q > 0).all()),
            "high_ge_ohlc": bool((q[:, 1] >= q[:, [0, 2, 3]].max(axis=1)).all()),
            "low_le_ohlc": bool((q[:, 2] <= q[:, [0, 1, 3]].min(axis=1)).all()),
            "finite_nonnegative_volume": bool(np.isfinite(v).all() and (v >= 0).all()),
        }
        if not all(checks.values()):
            raise ValueError(f"{symbol} {m}: invalid OHLCV {checks}")
        arrays.append(ts)
        outputs.append({"month": str(m), "file": str(p), "sha256": digest(p),
                        "rows": len(d), "checks": checks})
    full = arrays[0].append(arrays[1:])
    if not full.equals(EXPECTED):
        raise ValueError(f"{symbol}: time alignment failed")
    return {"symbol": symbol, "n_months": len(files), "rows": len(full),
            "first_open_time": str(full[0]), "last_open_time": str(full[-1]),
            "complete_5m_grid": True, "files": outputs}


def main():
    if sys.argv[1:] != ["--preflight"]:
        raise SystemExit("Usage: python R9_phase_b_daten_audit_2024_2025.py --preflight")
    out = {"schema": "r9_data_quality_v1", "phase": "B", "phase_c_approved": False,
           "status": "NOT_A_MARKET_MEASUREMENT", "expected_period":
           "2024-09-01 through 2025-01-01 through 2026-01-01 UTC excl",
           "expected_5m_rows_per_asset": len(EXPECTED), "assets": {}}
    errors = []
    for s in ("BTC", "ETH"):
        try:
            result = audit_coin(s)
            out["assets"][s] = result
            print(f"{s}: PASS, {result['n_months']} months, {result['rows']} candles")
        except Exception as exc:
            errors.append(str(exc))
            print(f"{s}: FAIL: {exc}")
    out["pass"] = not errors
    out["errors"] = errors
    out["data_provenance_status"] = "EXCHANGE_ENDPOINT_NOT_INDEPENDENTLY_VERIFIED"
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "R9_2024_2025_DATA_AUDIT.json"
    if path.exists():
        raise SystemExit(f"STOP: will not overwrite existing audit {path}")
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("AUDIT FILE:", path)
    print("PROVENANCE: Binance folder path known; independent endpoint evidence still required")
    print("PHASE C: NOT APPROVED; NO RETURNS, EVENTS, BOOTSTRAP OR PNL MEASURED")
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
