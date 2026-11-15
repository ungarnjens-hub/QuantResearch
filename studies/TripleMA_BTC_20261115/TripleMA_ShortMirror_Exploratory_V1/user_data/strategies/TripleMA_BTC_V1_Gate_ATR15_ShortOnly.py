"""Short-only version of same mirrored model, no long entries."""
from pandas import DataFrame
from TripleMA_BTC_V1_Gate_ATR15_LongShort import TripleMA_BTC_V1_Gate_ATR15_LongShort

class TripleMA_BTC_V1_Gate_ATR15_ShortOnly(TripleMA_BTC_V1_Gate_ATR15_LongShort):
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        long_mask = dataframe['enter_long'].fillna(0).eq(1)
        dataframe.loc[long_mask, 'enter_long'] = 0
        dataframe.loc[long_mask, 'enter_tag'] = None
        return dataframe
