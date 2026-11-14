#!/usr/bin/env python3
"""R5/R6 validation data acquisition. Pure market data, NO research metrics.

Usage: --selftest (offline) or --download (read-only public Binance USD-M API).
Never writes to TradingLab or the Git repository. Writes only into
~/QuantResearch/Validation_2026_AugOct/data, once, without overwriting.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

ROOT = Path.home() / "QuantResearch/Validation_2026_AugOct/data"
URL = "https://fapi.binance.com/fapi/v1/klines"
START = pd.Timestamp("2026-07-01T00:00:00Z")
END = pd.Timestamp("2026-11-01T00:00:00Z")
STEP = 300000
LIMIT = 1500
COINS = ("BTC", "ETH", "SOL")
N = int((END - START).total_seconds() * 1000 // STEP)
FIRST = int(START.timestamp() * 1000)
LAST = int(END.timestamp() * 1000) - STEP


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_rows(rows, symbol):
    if len(rows) != N:
        raise ValueError(f"{symbol}: erwartet {N} 5m-Bars, erhalten {len(rows)}")
    t = np.array([int(x[0]) for x in rows], dtype=np.int64)
    if t[0] != FIRST or t[-1] != LAST or not np.all(np.diff(t) == STEP):
        raise ValueError(f"{symbol}: Luecke, Duplikat oder falsche Zeitgrenze")
    if any(int(x[6]) != int(x[0]) + STEP - 1 for x in rows):
        raise ValueError(f"{symbol}: Kline-Close-Timestamp unerwartet")
    v = np.asarray([[float(x[k]) for k in (1, 2, 3, 4, 5)] for x in rows])
    o, hi, lo, cl, vol = v.T
    if (not np.isfinite(v).all() or np.any(lo <= 0) or np.any(vol < 0)
            or np.any(hi < np.maximum(o, cl)) or np.any(lo > np.minimum(o, cl))):
        raise ValueError(f"{symbol}: OHLC/Volume invalid")
    return pd.DataFrame({
        "open_time": pd.to_datetime(t, unit="ms", utc=True),
        "open": o, "high": hi, "low": lo, "close": cl, "volume": vol,
    })


def get_page(symbol, cursor):
    params = urlencode({"symbol": symbol + "USDT", "interval": "5m",
                        "startTime": cursor, "endTime": int(END.timestamp() * 1000)-1,
                        "limit": LIMIT})
    req = Request(URL + "?" + params,
                  headers={"User-Agent": "QuantResearch-validation-data/1.0", "Accept": "application/json"})
    for attempt in range(5):
        try:
            with urlopen(req, timeout=30) as res:
                return json.load(res)
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"Binance HTTP {exc.code} bei {symbol}") from exc
            if exc.code == 429 and attempt == 4:
                raise RuntimeError("Rate-Limit; nicht weiter anfragen") from exc
            delay = min(60, max(2 ** attempt, int(exc.headers.get("Retry-After", "1"))))
            time.sleep(delay)
        except (URLError, TimeoutError) as exc:
            if attempt == 4:
                raise RuntimeError(f"Netzwerkfehler {symbol}: {exc}") from exc
            time.sleep(2 ** attempt)
    raise RuntimeError("Unbekannter Downloadfehler")


def download_symbol(symbol):
    rows = []
    cursor = FIRST
    while cursor <= LAST:
        page = get_page(symbol, cursor)
        if not isinstance(page, list) or not page:
            raise RuntimeError(f"{symbol}: Leere/ungueltige API-Antwort bei {cursor}")
        if int(page[0][0]) != cursor:
            raise RuntimeError(f"{symbol}: API startet nicht am angeforderten Timestamp")
        if any(int(x[0]) != cursor + STEP * i for i, x in enumerate(page)):
            raise RuntimeError(f"{symbol}: Fehler innerhalb einer API-Seite")
        rows.extend(x for x in page if int(x[0]) <= LAST)
        cursor = int(page[-1][0]) + STEP
        if cursor <= LAST:
            time.sleep(0.20)
    return validate_rows(rows, symbol)


def selftest():
    assert N == 35424, N
    assert pd.to_datetime(FIRST, unit="ms", utc=True) == START
    assert pd.to_datetime(LAST, unit="ms", utc=True) == END-pd.Timedelta(minutes=5)
    synthetic = [[FIRST+i*STEP, "1", "2", "0.5", "1.5", "3",
                  FIRST+i*STEP+STEP-1] for i in range(N)]
    df = validate_rows(synthetic, "TEST")
    assert len(df) == N and (df.columns == ["open_time", "open", "high", "low", "close", "volume"]).all()
    synthetic[100][0] += STEP
    try:
        validate_rows(synthetic, "TEST")
    except ValueError:
        pass
    else:
        raise AssertionError("Lueckenschutz unwirksam")
    print(f"DATENABRUF-SELBSTTEST: PASS; {N} Kerzen pro Markt, keine Netzwerkanfrage")


def acquire():
    # All-or-nothing file policy: do not download if any target already exists.
    targets = {c: ROOT / f"{c}_USDT_5m_2026-07_2026-10.parquet" for c in COINS}
    manifest = ROOT / "manifest.json"
    if any(p.exists() for p in [*targets.values(), manifest]):
        raise RuntimeError("STOP: Daten/Manifest existieren bereits; kein Ueberschreiben")
    if ROOT.is_symlink():
        raise RuntimeError("STOP: Datenverzeichnis ist ein Symlink")
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("STOP: Datenverzeichnis nicht leer")
    collected = {}
    stamps = {}
    for coin in COINS:
        print(f"Rufe {coin}USDT 5m Futures vom oeffentlichen Binance-Endpunkt ab ...", flush=True)
        collected[coin] = download_symbol(coin)
        stamps[coin] = datetime.now(timezone.utc).isoformat()
        print(f"{coin}: {len(collected[coin])} lueckenlose Kerzen geprueft", flush=True)
    ROOT.mkdir(parents=True, exist_ok=True)
    record = {}
    for coin, df in collected.items():
        path = targets[coin]
        # exclusive creation: never overwrite preexisting artifacts
        with path.open("xb") as f:
            df.to_parquet(f, index=False)
        record[coin] = {
            "path": str(path.resolve()), "sha256": digest(path),
            "symbol": f"{coin}/USDT:USDT", "exchange": "binance",
            "market_type": "perpetual", "contract_type": "linear",
            "price_source": "last_trade", "timeframe": "5m",
            "endpoint": "/fapi/v1/klines", "downloaded_at_utc": stamps[coin],
            "from_inclusive": START.isoformat(), "to_exclusive": END.isoformat(),
            "rows": len(df),
        }
    with manifest.open("x", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
        f.write("\n")
    print("DATENGATE: PASS. Drei Rohdatendateien und Manifest erstellt.")
    print("Ort:", ROOT)
    print("Keine Prognosen, keine Ergebnisse, kein Zugriff auf TradingLab-Dateien.")


def main():
    p = argparse.ArgumentParser()
    x = p.add_mutually_exclusive_group(required=True)
    x.add_argument("--selftest", action="store_true")
    x.add_argument("--download", action="store_true")
    args = p.parse_args()
    try:
        selftest() if args.selftest else acquire()
    except Exception as exc:
        print("STOP:", type(exc).__name__, str(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
