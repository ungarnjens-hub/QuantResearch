#!/usr/bin/env python3
"""Read-only Freqtrade ZIP audit / pre-registered weekly moving-block bootstrap.
No strategies, candles, profiles or source files are modified.
Usage: python triplema_montecarlo.py --audit [--dev ZIP --test ZIP]
       python triplema_montecarlo.py --run [--dev ZIP --test ZIP] [--out DIRECTORY]
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np

STRATEGY = "TripleMA_BTC_V1_ATR15_Complementary_Hours"
SEED = 20261115
N_SIM = 10000
BLOCK_WEEKS = (1, 2, 4)
EXPECTED = {"development": (115, 23.00436, 1.40533), "validation_2026": (31, 8.17416365, 1.6212)}
HOME = Path.home()
DEFAULT_DEV = HOME / "QuantResearch/TripleMA_Complementary_Hours_AB_V1/user_data/backtest_results/backtest-result-2026-11-15_16-16-55.zip"
DEFAULT_TEST = HOME / "QuantResearch/TripleMA_2026_Frozen_Test_V1/user_data/backtest_results/backtest-result-2026-11-15_16-24-25.zip"


def fail(msg):
    raise ValueError(msg)


def iso_date(raw):
    if isinstance(raw, (float, int)):
        return datetime.fromtimestamp(raw / (1000 if raw > 1e11 else 1), tz=timezone.utc)
    if not isinstance(raw, str) or not raw:
        fail("Missing trade datetime")
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)  # Freqtrade export timestamps denote UTC
    return dt.astimezone(timezone.utc)


def as_float(obj, key):
    val = obj.get(key)
    try:
        out = float(val)
    except (TypeError, ValueError):
        fail(f"Non-numeric {key}: {val!r}")
    if not math.isfinite(out):
        fail(f"Non-finite {key}")
    return out


def extract_zip(path, label):
    if not path.is_file():
        fail(f"Missing ZIP: {path}")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as z:
        choices = [n for n in z.namelist() if n.endswith(".json") and not n.endswith("_config.json") and not n.endswith(".meta.json") and "/" not in n]
        if len(choices) != 1:
            fail(f"Expected one root result json in {path}, got {choices}")
        payload = json.loads(z.read(choices[0]))
    strat = payload.get("strategy", {})
    if STRATEGY not in strat:
        fail(f"{label}: strategy {STRATEGY} missing; found {list(strat)}")
    result = strat[STRATEGY]
    trades = result.get("trades")
    if not isinstance(trades, list):
        fail(f"{label}: no trades list")
    parsed = []
    for t in trades:
        op = iso_date(t.get("open_date") or t.get("open_date_utc") or t.get("open_timestamp"))
        cl = iso_date(t.get("close_date") or t.get("close_date_utc") or t.get("close_timestamp"))
        if cl < op:
            fail(f"{label}: invalid trade duration {op} {cl}")
        profit = as_float(t, "profit_abs")
        lev = t.get("leverage", 1) or 1
        stake = t.get("stake_amount")
        notional = None
        if stake is not None:
            notional = float(stake) * float(lev)
            if not math.isfinite(notional) or notional <= 0:
                fail(f"{label}: invalid stake/leverage")
        parsed.append({"open": op, "close": cl, "pnl": profit, "notional": notional, "pair": t.get("pair"), "is_short": t.get("is_short")})
    parsed.sort(key=lambda t: (t["close"], t["open"]))
    count, reference, reference_pf = EXPECTED[label]
    pnl = sum(t["pnl"] for t in parsed)
    if len(parsed) != count or abs(pnl - reference) > .05:
        fail(f"{label}: archive differs from frozen reference: count={len(parsed)} net={pnl:.6f}, expected={count} / {reference}")
    if label == "development" and any(t["open"] >= datetime(2026,1,1,tzinfo=timezone.utc) for t in parsed):
        fail("Development has 2026 trades: potential period leakage")
    if label == "validation_2026" and any(not(datetime(2026,1,1,tzinfo=timezone.utc) <= t["open"] < datetime(2026,7,1,tzinfo=timezone.utc)) for t in parsed):
        fail("Validation has trades outside frozen 2026 window")
    if len(set((t["open"], t["close"], round(t["pnl"], 8)) for t in parsed)) != len(parsed):
        fail(f"{label}: duplicate-like trade records")
    gross_pos = sum(max(t["pnl"],0) for t in parsed)
    gross_neg = -sum(min(t["pnl"],0) for t in parsed)
    pf = gross_pos/gross_neg if gross_neg > 0 else None
    if pf is None or abs(pf - reference_pf) > .015:
        fail(f"{label}: PF {pf} differs from archived reported {reference_pf}")
    print(f"[{label}] ZIP SHA256 {sha}")
    print(f"  trades={len(parsed)} net={pnl:.6f} PF={pf:.4f}" if pf else f"  trades={len(parsed)} net={pnl:.6f} PF=undefined")
    print(f"  first_open={min(t['open'] for t in parsed)} last_close={max(t['close'] for t in parsed)}")
    print(f"  pair(s)={sorted(set(str(t['pair']) for t in parsed))} notional_complete={all(t['notional'] is not None for t in parsed)}")
    return {"zip": str(path.resolve()), "sha256": sha, "trades": parsed, "reported_pf": pf, "reported_net": pnl, "freqtrade_max_dd_abs": result.get("max_drawdown_abs")}


def calendar_weeks(trades, start, end):
    first = start - timedelta(days=start.weekday())
    last = (end - timedelta(microseconds=1))
    last = last - timedelta(days=last.weekday())
    weeks = []
    lookup = {}
    day = first
    while day <= last:
        lookup[day.date()] = len(weeks)
        weeks.append([])
        day += timedelta(days=7)
    for t in trades:
        monday = (t["close"] - timedelta(days=t["close"].weekday())).date()
        if monday not in lookup:
            fail(f"Trade close outside target period: {t['close']}")
        weeks[lookup[monday]].append(t)
    return weeks


def closed_equity_dd(values):
    running = 0.0
    peak = 0.0
    dd = 0.0
    for v in values:
        running += v
        peak = max(peak, running)
        dd = max(dd, peak-running)
    return dd


def pf(values):
    p = sum(max(v, 0) for v in values)
    n = -sum(min(v, 0) for v in values)
    return p/n if n > 0 else None


def stationary_week_indices(rng, n, block):
    """Circular moving block bootstrap with fixed blocks of L calendar weeks."""
    indices = []
    while len(indices) < n:
        s = int(rng.integers(0, n))
        indices.extend(((s + j) % n for j in range(block)))
    return indices[:n]


def summarize(values):
    a = np.asarray(values, dtype=float)
    good = a[np.isfinite(a)]
    if not len(good):
        return {"status": "undefined"}
    return {"q01": float(np.quantile(good, .01)), "q05": float(np.quantile(good, .05)), "median": float(np.median(good)), "q95": float(np.quantile(good, .95)), "q99": float(np.quantile(good, .99))}


def simulate(weeks, L, seed, stress_bps):
    rng = np.random.default_rng(seed)
    nets, pfs, dds, negatives = [], [], [], 0
    for _ in range(N_SIM):
        seq = []
        for i in stationary_week_indices(rng, len(weeks), L):
            seq.extend(weeks[i])
        if stress_bps:
            pnl = [t["pnl"] - t["notional"] * stress_bps / 10000 for t in seq]
        else:
            pnl = [t["pnl"] for t in seq]
        total = sum(pnl)
        nets.append(total)
        pfs.append(pf(pnl) or float("nan"))
        dds.append(closed_equity_dd(pnl))
        negatives += (total < 0)
    return {"simulations": N_SIM, "block_weeks": L, "extra_roundtrip_bps": stress_bps, "net_usdt": summarize(nets), "pf": summarize(pfs), "pf_undefined_fraction": sum(not math.isfinite(x) for x in pfs)/N_SIM, "closed_trade_max_dd_usdt": summarize(dds), "fraction_negative_net": negatives/N_SIM}


def extra_analysis(trades):
    pnl = [t["pnl"] for t in trades]
    winners = sorted((x for x in pnl if x > 0), reverse=True)
    return {"top1_win_usdt": winners[0] if winners else None, "top3_win_usdt": sum(winners[:3]), "top3_over_net": sum(winners[:3])/sum(pnl) if sum(pnl) else None, "without_top1_net": sum(pnl) - sum(winners[:1]), "without_top3_net": sum(pnl)-sum(winners[:3]), "closed_trade_max_dd_usdt": closed_equity_dd(pnl), "winning_count": len(winners), "losing_count": sum(x < 0 for x in pnl), "net_usdt": sum(pnl), "pf": pf(pnl)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    act = ap.add_mutually_exclusive_group(required=True)
    act.add_argument("--audit", action="store_true", help="read-only audit, no Monte Carlo")
    act.add_argument("--run", action="store_true", help="run pre-registered analysis")
    ap.add_argument("--dev", type=Path, default=DEFAULT_DEV)
    ap.add_argument("--test", type=Path, default=DEFAULT_TEST)
    ap.add_argument("--out", type=Path, default=HOME / "QuantResearch/TripleMA_MonteCarlo_Audit_V1")
    args = ap.parse_args()
    print("AUDIT: immutable Freqtrade archives; frozen strategy", STRATEGY)
    dev = extract_zip(args.dev, "development")
    val = extract_zip(args.test, "validation_2026")
    if any(x["close"] >= datetime(2026,1,1,tzinfo=timezone.utc) for x in dev["trades"]):
        fail("Development closed after 2025 (overlaps validation)")
    if not (all(t["notional"] is not None for t in dev["trades"]) and all(t["notional"] is not None for t in val["trades"])):
        fail("Missing stake/leverage: cannot conduct pre-registered cost stress")
    print("AUDIT PASS (trade-level only). Verify Freqtrade stop/execution/cost semantics separately.")
    if args.audit:
        return
    if args.out.exists() and any(args.out.iterdir()):
        fail(f"Output directory already populated; refusing overwrite: {args.out}")
    results = {"method": "calendar-week circular moving block bootstrap of closed-trade records", "non_claims": ["No newly independent OOS confirmation", "Closed-trade DD excludes intratrade equity drawdown", "Fixed-length historical resampling does not model novel regimes or execution failures"], "seed":SEED, "simulation_count":N_SIM, "blocks_in_weeks":list(BLOCK_WEEKS), "extra_roundtrip_bps":[0,2,5,10], "datasets":{}}
    for label,obj,start,end in (("development",dev,datetime(2024,7,1,tzinfo=timezone.utc),datetime(2026,1,1,tzinfo=timezone.utc)),("validation_2026",val,datetime(2026,1,1,tzinfo=timezone.utc),datetime(2026,7,1,tzinfo=timezone.utc))):
        weeks = calendar_weeks(obj["trades"],start,end)
        cases = []
        for L in BLOCK_WEEKS:
            for bps in (0,2,5,10):
                cases.append(simulate(weeks,L,SEED+L*1000+bps, bps))
        results["datasets"][label] = {"archive":obj["zip"], "sha256":obj["sha256"], "calendar_weeks":len(weeks), "active_weeks":sum(bool(w) for w in weeks), "observed":extra_analysis(obj["trades"]), "cases":cases}
    args.out.mkdir(parents=True,exist_ok=True)
    path = args.out / "report.json"
    path.write_text(json.dumps(results,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print("MONTE CARLO DONE (historical resampling, NOT new independent validation)")
    print("REPORT", path)
    for name,group in results["datasets"].items():
        base = next(c for c in group["cases"] if c["block_weeks"]==2 and c["extra_roundtrip_bps"]==0)
        print(f"{name}: P(net<0)={base['fraction_negative_net']:.3f}, net q05={base['net_usdt']['q05']:.3f} USDT; closed-trade-DD q95={base['closed_trade_max_dd_usdt']['q95']:.3f} USDT")

if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, zipfile.BadZipFile, json.JSONDecodeError) as e:
        print("BLOCKED:",e,file=sys.stderr)
        sys.exit(2)
