"""Ungated short-only mirror: removes long entries entirely."""
from pandas import DataFrame
from TripleMA_BTC_V1_ATR15_LongShort_NoGate import TripleMA_BTC_V1_ATR15_LongShort_NoGate
class TripleMA_BTC_V1_ATR15_ShortOnly_NoGate(TripleMA_BTC_V1_ATR15_LongShort_NoGate):
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        m = dataframe['enter_long'].fillna(0).eq(1)
        dataframe.loc[m,'enter_long'] = 0
        dataframe.loc[m,'enter_tag'] = None
        return dataframe
