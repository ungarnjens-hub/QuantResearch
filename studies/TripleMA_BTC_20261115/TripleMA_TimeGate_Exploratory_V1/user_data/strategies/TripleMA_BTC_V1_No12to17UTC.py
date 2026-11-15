"""Exploratory next-hour UTC entry gate; no changes to underlying indicators/exits."""
import pandas as pd
from pandas import DataFrame
from TripleMA_BTC_V1 import TripleMA_BTC_V1

class TripleMA_BTC_V1_No12to17UTC(TripleMA_BTC_V1):
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        # In Freqtrade the 1h signal is known at the candle close; the normal
        # next opening is one hour after the signal candle's OPEN timestamp.
        expected_entry = pd.to_datetime(dataframe['date'], utc=True) + pd.Timedelta(hours=1)
        blocked = expected_entry.dt.hour.between(12, 17)
        dataframe.loc[blocked, 'enter_long'] = 0
        dataframe.loc[blocked, 'enter_tag'] = None
        return dataframe
