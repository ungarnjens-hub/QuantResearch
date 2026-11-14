#!/usr/bin/env python3
"""Vortest der eingefrorenen R5/R6-Zeitlogik, nur künstliche Kurse.

Keine echten Kursdaten, keine Prognosemodelle auf historischen Marktdaten,
keine Änderungen an vorhandenen Forschungsberichten oder produktiven Systemen.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HOME = Path.home()
REPO = HOME / "QuantResearch-Git"
FILES = {
    "R5-Code": (REPO / "studies/R5_BTC_ETH_Volatilitaet/R5_lauf.py", "fca8ef5d64ddb98d9cf470b67698ffb982dccedb68bd3dd56e6c03ea88ebaee0"),
    "R6-Code": (REPO / "studies/R6_BTC_SOL_Volatilitaet/R6_lauf.py", "905843db94f5d1730c62380d1a4303e84b860f0858bfe3f50686d71006a3c647"),
    "Protokoll": (REPO / "validation/R5_R6_Validierungsprotokoll_PhaseB_2026-11-14.md", "ba46b172bb9cf4e51dea4241804423a052c69abcd42cd6fc1b033bbea2fd5df8"),
    "Methodenaudit": (REPO / "validation/R5_R6_Methodenaudit_2026-11-14.md", "000c4c30d40a28bedaf9795be11c25c51daf12e6a97f83a75ee10a3ceaf4f04e"),
}
START = pd.Timestamp("2026-08-01T00:00:00Z")
END = pd.Timestamp("2026-11-01T00:00:00Z")


def check(condition, description):
    if not bool(condition):
        raise AssertionError(description)
    print("PASS", description)


def imported_features(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.features


def run():
    for label, (path, expected) in FILES.items():
        check(path.is_file(), f"Vorhanden: {label}")
        check(hashlib.sha256(path.read_bytes()).hexdigest() == expected,
              f"Unveraenderte SHA256: {label}")

    r5 = imported_features(FILES["R5-Code"][0], "gate_r5")
    r6 = imported_features(FILES["R6-Code"][0], "gate_r6")

    # 5min-Synthetik mit ausreichend HAR-Warm-up und Testdaten bis zum Labelende.
    idx = pd.date_range("2026-07-15T00:00Z", "2026-11-02T00:00Z", freq="5min")
    j = np.arange(len(idx), dtype=float)
    data = pd.DataFrame({
        "BTC": 50_000. * np.exp(np.cumsum(0.0012*np.sin(j/23.0))),
        "ETH": 2_000. * np.exp(np.cumsum(0.0018*np.cos(j/29.0))),
    }, index=idx)

    a = r5(data)
    b = r6(data)
    check(a.index.equals(b.index), "Gleiche R5/R6-Prognosezeitachse")
    check(np.allclose(a.drop(columns="available"), b.drop(columns="available")),
          "Gleiche R5/R6-Merkmale und Ziele")
    check(a.available.equals(b.available), "Gleiche R5/R6-Labelverfuegbarkeit")

    eligible = a[(a.index >= START) & (a.index < END) & (a.available <= END)]
    check(len(eligible) == 2207, "Exakt 2207 zulaessige Forecasts")
    check((eligible.index.minute == 55).all(), "Nur Forecasts zur Minute 55")
    check((eligible.available - pd.Series(eligible.index, index=eligible.index)
           == pd.Timedelta(minutes=65)).all(),
          "Label fruehestens t + 65 Minuten")
    day_counts = eligible.groupby(eligible.index.floor("D")).size()
    check(len(day_counts) == 92, "Genau 92 UTC-Kalendertage")
    check((day_counts.iloc[:-1] == 24).all() and day_counts.iloc[-1] == 23,
          "Erste 91 Tage je 24, letzter Tag 23 Prognosen")
    check(eligible.index[0] == pd.Timestamp("2026-08-01T00:55:00Z"),
          "Erster Forecast am 1. August 00:55 UTC")
    check(eligible.index[-1] == pd.Timestamp("2026-10-31T22:55:00Z"),
          "Letzter Forecast am 31. Oktober 22:55 UTC")

    for refit in pd.to_datetime(["2026-08-01", "2026-09-01", "2026-10-01"], utc=True):
        train = a[(a.index >= pd.Timestamp("2026-07-15T00:00Z")) &
                  (a.available <= refit)]
        check(not train.empty and (train.available <= refit).all(),
              f"Keine Zukunftslabels beim Refit {refit.date()}")

    t = eligible.index[0]
    earlier = a.loc[t, ["BTC12", "BTC288", "BTC2016", "ETH12", "ETH288", "ETH2016"]].to_numpy(dtype=float)
    tampered = data.copy()
    tampered.loc[tampered.index > t, "BTC"] *= 1.5
    tampered.loc[tampered.index > t, "ETH"] *= 1.2
    changed = r5(tampered).loc[t, ["BTC12", "BTC288", "BTC2016", "ETH12", "ETH288", "ETH2016"]].to_numpy(dtype=float)
    check(np.allclose(earlier, changed, rtol=0., atol=1e-12),
          "Merkmale invariant gegen Kursaenderungen nach Forecast-Kerze")
    check(not np.isclose(a.loc[t, "target"], r5(tampered).loc[t, "target"], rtol=0., atol=1e-9),
          "Zukunftsaenderung betrifft das Ziel, nicht die Merkmale")

    print("\nSYNTHETISCHES GATE: PASS")
    print("Noch KEINE Freigabe zur echten Ergebnismessung.")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(f"\nSYNTHETISCHES GATE: FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
