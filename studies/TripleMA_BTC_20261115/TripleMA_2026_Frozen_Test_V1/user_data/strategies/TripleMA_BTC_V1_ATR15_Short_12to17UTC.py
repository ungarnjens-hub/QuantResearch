"""Research only: SHORT entry 12:00-17:59 UTC; original exits unchanged."""
from pandas import DataFrame
from TripleMA_BTC_V1_ATR15_Complementary_Hours import TripleMA_BTC_V1_ATR15_Complementary_Hours
class TripleMA_BTC_V1_ATR15_Short_12to17UTC(TripleMA_BTC_V1_ATR15_Complementary_Hours):
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        remove = dataframe['enter_long'].fillna(0).eq(1)
        dataframe.loc[remove,'enter_long'] = 0
        dataframe.loc[remove,'enter_tag'] = None
        return dataframe
