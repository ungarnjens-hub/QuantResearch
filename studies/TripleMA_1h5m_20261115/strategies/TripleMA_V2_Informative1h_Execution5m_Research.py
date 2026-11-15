"""Research-only 1h-signal / 5m-execution candidate for TripleMA V2.

Candles on the informative 1h dataframe are processed by the exact frozen V2
parent methods. The 1h signal is exposed on 5m only after the hour closes.
The signal is emitted once, on the first 5m candle of that hour; Freqtrade's
backtest next-candle rule therefore fills at +5m, not at the 1h close.
This difference from historical 1h+5m detail simulation is intentional.
"""
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import informative
from TripleMA_BTC_V1_ATR15_Complementary_Hours import TripleMA_BTC_V1_ATR15_Complementary_Hours
from TripleMA_BTC_V1_ATR15_Complementary_Hours_NoMonday_Morning_Short14 import (
    TripleMA_BTC_V1_ATR15_Complementary_Hours_NoMonday_Morning_Short14,
)


class TripleMA_V2_Informative1h_Execution5m_Research(
    TripleMA_BTC_V1_ATR15_Complementary_Hours_NoMonday_Morning_Short14
):
    timeframe = '5m'
    startup_candle_count = 600
    process_only_new_candles = True

    @informative('1h', ffill=True)
    def informative_1h_signals(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Explicitly call the frozen 1h chain, never the 5m overrides.
        df = TripleMA_BTC_V1_ATR15_Complementary_Hours.populate_indicators(
            self, dataframe, metadata
        )
        df = TripleMA_BTC_V1_ATR15_Complementary_Hours.populate_entry_trend(
            self, df, metadata
        )
        return TripleMA_BTC_V1_ATR15_Complementary_Hours.populate_exit_trend(
            self, df, metadata
        )

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Informative columns are added by Freqtrade's @informative machinery.
        return dataframe

    @staticmethod
    def _first_5m_after_1h_close(df: DataFrame):
        # date_1h is informative candle OPEN time, never its close.
        # Freqtrade merges higher timeframes only after they close.
        close = pd.to_datetime(df['date_1h'], utc=True) + pd.Timedelta(hours=1)
        base = pd.to_datetime(df['date'], utc=True)
        return base.eq(close) & df['volume'].gt(0)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        df = dataframe.copy()
        first = self._first_5m_after_1h_close(df)
        for direction in ('long', 'short'):
            src = f'enter_{direction}_1h'
            dest = f'enter_{direction}'
            df[dest] = (first & df[src].fillna(0).eq(1)).astype('int8')
        df['enter_tag'] = None
        selected = df['enter_long'].eq(1) | df['enter_short'].eq(1)
        df.loc[selected, 'enter_tag'] = df.loc[selected, 'enter_tag_1h']
        if (df['enter_long'].eq(1) & df['enter_short'].eq(1)).any():
            raise ValueError('Contradictory 1h signals')
        return df

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        df = dataframe.copy()
        first = self._first_5m_after_1h_close(df)
        for direction in ('long', 'short'):
            src = f'exit_{direction}_1h'
            df[f'exit_{direction}'] = (first & df[src].fillna(0).eq(1)).astype('int8')
        return df
