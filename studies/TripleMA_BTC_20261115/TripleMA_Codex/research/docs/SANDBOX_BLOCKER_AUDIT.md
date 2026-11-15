# Triple-MA BTC V2 — Sandbox-blocker audit

Date: 2026-11-15 (Europe/Berlin)

## Scope

This is a read-only source and local-artifact audit of the installed
`freqtrade 2026.9` environment. No installed package, original data,
TradingLab file, Paper-bot state, or production configuration was changed.
No backtest was run in this audit.

## Verified causal path

The installed Freqtrade source shows that the normal CLI backtesting path
cannot suppress exchange construction:

1. `freqtrade/commands/optimize_commands.py:45-61` constructs
   `Backtesting(config)`.
2. `freqtrade/optimize/backtesting.py:167-173` calls
   `ExchangeResolver.load_exchange(self.config, load_leverage_tiers=True)`
   when no test exchange is injected.
3. `freqtrade/exchange/exchange.py:309-312` performs
   `reload_markets(True, load_leverage_tiers=False)` when the exchange is
   validated.
4. `freqtrade/exchange/exchange.py:732-734` calls
   `await self._api_async.load_markets(reload=reload, params={})`.

The Phase-A command therefore failed before strategy loading, local candle
loading, or trade simulation when this mandatory native initialization reached
Binance DNS/HTTPS. The observed error was
`Temporary failure in name resolution` for
`api.binance.com/api/v3/exchangeInfo`.

The installed CCXT 4.5.90 source confirms that Binance `fetch_markets()` uses
live public exchange-information endpoints. Its default market types are
`spot`, `linear`, and `inverse`; their endpoint families are respectively
`api.binance.com`, `fapi.binance.com`, and `dapi.binance.com`. This behavior is
not an OHLCV download and does not use credentials or order endpoints, but it
does require public network access.

## Offline feasibility

No supported offline path is available in the installed Freqtrade 2026.9
distribution:

- The installed Freqtrade configuration and Python source contain no
  configuration key for a market-metadata file, a serialized CCXT market
  catalogue, or an offline exchange backend.
- `set_markets_from_exchange()` exists only in Freqtrade's internal result
  path after the asynchronous CCXT exchange has loaded markets. It is not a
  CLI/configuration mechanism for injecting a file.
- The local file
  `freqtrade/exchange/binance_leverage_tiers.json` contains 907 leverage-tier
  lists, not CCXT market definitions (it lacks the full precision, limits,
  contract, type, and exchange-info catalogue required by a futures pair).
- The inspected Freqtrade cache, demo directory, and local JSON candidates
  contain configuration, test selections, package caches, or database files;
  none is a serialized CCXT market catalogue for `BTC/USDT:USDT`.

Creating a market dictionary, injecting it through private APIs, or modifying
the installed library would bypass the required native market-validation path
and is out of scope.

## Required approval to unblock the minimal reproduction

Grant the sandbox process running
`/home/icom/Freqtrade-Test/.venv/bin/freqtrade` outbound DNS resolution and
read-only HTTPS access on port 443 only to the public Binance exchange-info
hosts required by the installed CCXT call:

- `api.binance.com`
- `fapi.binance.com`
- `dapi.binance.com`

No credentials, account endpoints, download command, trade command, or order
endpoint are required. With that authorization, the only next action should
be the already-defined isolated V1 reproduction backtest. Until then, no
technically correct Freqtrade-2026.9 offline execution is available here.
