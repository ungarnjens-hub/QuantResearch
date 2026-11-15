"""Isolated research strategy for Freqtrade 2026.9. 1h signals, next candle open fills.

RESEARCH ONLY, no live or dry-run bot use. Parameters are preselected hypotheses.
"""
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class TripleMA_BTC_V1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    startup_candle_count = 600
    process_only_new_candles = True

    minimal_roi = {"0": 100.0}  # Intentionally disables ordinary ROI exits
    stoploss = -0.99           # Research-only placeholder; not a safe live stop
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Preregistered exploratory defaults, not optimized parameters.
    slope_lookback_hours = 24
    min_ma200_rise_24h = 0.001
    oversold_lookback_hours = 48
    min_below_ma200_atr = 3.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        c = dataframe["close"]
        dataframe["ema7"] = c.ewm(span=7, adjust=False).mean()
        dataframe["ema25"] = c.ewm(span=25, adjust=False).mean()
        dataframe["ema200"] = c.ewm(span=200, adjust=False).mean()

        prev_close = c.shift(1)
        true_range = (dataframe["high"] - dataframe["low"]).combine(
            (dataframe["high"] - prev_close).abs(), max
        ).combine((dataframe["low"] - prev_close).abs(), max)
        # Wilder-style ATR(14) (RMA), using current and previous finalized 1h bars.
        dataframe["atr14"] = true_range.ewm(alpha=1 / 14, adjust=False).mean()

        dataframe["ma200_growth_24h"] = (
            dataframe["ema200"] / dataframe["ema200"].shift(self.slope_lookback_hours) - 1
        )
        below_in_atr = (
            (dataframe["ema200"] - c) / dataframe["atr14"].replace(0, float("nan"))
        ).clip(lower=0)
        # The earlier drop is assessed before the cross-candle itself.
        dataframe["prior_oversold_atr"] = (
            below_in_atr.shift(1)
            .rolling(self.oversold_lookback_hours, min_periods=self.oversold_lookback_hours)
            .max()
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        crossed_up = (
            (dataframe["ema7"] > dataframe["ema25"])
            & (dataframe["ema7"].shift(1) <= dataframe["ema25"].shift(1))
        )
        trend = (
            (dataframe["ma200_growth_24h"] >= self.min_ma200_rise_24h)
            & (dataframe["close"] > dataframe["ema200"])
        )
        recovery = dataframe["prior_oversold_atr"] >= self.min_below_ma200_atr
        ready = (dataframe["volume"] > 0) & dataframe["prior_oversold_atr"].notna()

        dataframe.loc[ready & crossed_up & trend, ["enter_long", "enter_tag"]] = (1, "trend")
        dataframe.loc[ready & crossed_up & ~trend & recovery, ["enter_long", "enter_tag"]] = (1, "recovery")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        crossed_down = (
            (dataframe["ema7"] < dataframe["ema25"])
            & (dataframe["ema7"].shift(1) >= dataframe["ema25"].shift(1))
        )
        dataframe.loc[(dataframe["volume"] > 0) & crossed_down, "exit_long"] = 1
        return dataframe
