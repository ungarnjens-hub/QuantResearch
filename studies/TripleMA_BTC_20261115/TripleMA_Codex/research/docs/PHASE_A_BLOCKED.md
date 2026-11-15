# Triple-MA BTC V2 — Phase A: blocked

Date: 2026-11-15 (Europe/Berlin)

## Scope and isolation

- Engine: `/home/icom/Freqtrade-Test/.venv/bin/freqtrade`, version 2026.9
  (Python 3.12.16, CCXT 4.5.90).
- Run mode requested: native Freqtrade backtesting only; `dry_run=true`,
  `trading_mode=futures`, `margin_mode=isolated`.
- Requested reproducibility settings: `BTC/USDT:USDT`, 1h primary timeframe,
  5m execution-detail timeframe, 2024-07-01 through 2026-01-01, 100 USDT
  stake, one maximum open trade, and Freqtrade's 0.05% per-side worst-case
  Binance fee.
- The strategy and configuration were copied or newly created only below this
  isolated research directory. The local strategy logic is byte-identical to
  the original V1 source. `research/data` is a read-only symbolic link to the
  original data directory; no source data were modified.

## Attempted Phase-A reproduction

The exact local command was:

```text
/home/icom/Freqtrade-Test/.venv/bin/freqtrade backtesting --config research/config_baseline.json --userdir research/user_data --strategy-path research/user_data/strategies --strategy TripleMA_BTC_V1 --datadir research/data --timeframe 1h --timeframe-detail 5m --timerange 20240701-20260101 --export trades --backtest-directory research/results/baseline --cache none --logfile research/logs/baseline.log --no-color
```

It failed before strategy loading, data loading, indicator construction, or
trade simulation. Freqtrade attempted to load Binance markets and terminated
with:

```text
Could not load markets, therefore cannot start.
Temporary failure in name resolution
api.binance.com/api/v3/exchangeInfo
```

This is the same type of sandbox infrastructure blocker documented in the
Freqtrade integration contract. The existing V1 reference run is therefore
not contradicted, but it cannot be reproduced in the current sandbox state.

## Consequence

No ATR-1.5 variant, parameter search, comparison model, or holdout analysis
was run. No data download, installation, configuration change outside this
directory, Paper-bot interaction, or order occurred. Per the requested
stop-on-substantial-engine-error rule, no offline-market-cache workaround or
other repair attempt was made.
