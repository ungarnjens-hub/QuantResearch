"""Research only: mutually exclusive long and short ENTRY hours, UTC."""
import pandas as pd
from pandas import DataFrame
from TripleMA_BTC_V1_ATR15_LongShort_NoGate import TripleMA_BTC_V1_ATR15_LongShort_NoGate

class TripleMA_BTC_V1_ATR15_Complementary_Hours(TripleMA_BTC_V1_ATR15_LongShort_NoGate):
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        # Freqtrade 1h candle 'date' is open timestamp; decision at close,
        # entry at next candle open, i.e., +1h in UTC.
        entry_hour = (pd.to_datetime(dataframe['date'],utc=True) + pd.Timedelta(hours=1)).dt.hour
        short_window = entry_hour.between(12,17)
        remove_long = dataframe['enter_long'].fillna(0).eq(1) & short_window
        remove_short = dataframe['enter_short'].fillna(0).eq(1) & ~short_window
        dataframe.loc[remove_long,'enter_long'] = 0
        dataframe.loc[remove_short,'enter_short'] = 0
        dataframe.loc[remove_long | remove_short, 'enter_tag'] = None
        if (dataframe['enter_long'].fillna(0).eq(1) & dataframe['enter_short'].fillna(0).eq(1)).any():
            raise ValueError('Simultaneous long and short signals')
        return dataframe
