from pandas import DataFrame
import pandas as pd
from TripleMA_BTC_V1 import TripleMA_BTC_V1

class TripleMA_BTC_V1_No12to17UTC(TripleMA_BTC_V1):
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        entry_hour = (pd.to_datetime(dataframe['date'], utc=True) + pd.Timedelta(hours=1)).dt.hour
        blocked = entry_hour.between(12,17)
        dataframe.loc[blocked, 'enter_long'] = 0
        dataframe.loc[blocked, 'enter_tag'] = None
        return dataframe
