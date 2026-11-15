"""Trend-only variant: suppress recovery AFTER exact reference ATR+gate logic."""
from pandas import DataFrame
from TripleMA_BTC_V1_Gate_ATR15 import TripleMA_BTC_V1_Gate_ATR15

class TripleMA_BTC_V1_Gate_ATR15_TrendOnly(TripleMA_BTC_V1_Gate_ATR15):
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        recovery = dataframe['enter_long'].eq(1) & dataframe['enter_tag'].fillna('').astype(str).str.startswith('recovery|')
        dataframe.loc[recovery, 'enter_long'] = 0
        dataframe.loc[recovery, 'enter_tag'] = None
        return dataframe
