"""Fixed initial absolute ATR stop, anchored to signal-time ATR in enter_tag.

The ATR value is encoded at 1h SIGNAL calculation, so delayed fills never
accidentally use a later bar. The 1h bar is finalized before Freqtrade entry.
"""
import math
from pandas import DataFrame
from freqtrade.strategy import stoploss_from_absolute
from TripleMA_BTC_V1 import TripleMA_BTC_V1

class TripleMA_BTC_V1_ATR15(TripleMA_BTC_V1):
    use_custom_stoploss = True
    stoploss = -0.99  # Freqtrade mandatory fallback; must set initial ATR on fill
    atr_multiple = 1.5

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        mask = dataframe['enter_long'].eq(1)
        if mask.any():
            if dataframe.loc[mask, 'atr14'].isna().any():
                raise ValueError('Missing ATR14 at valid signal')
            dataframe.loc[mask, 'enter_tag'] = (
                dataframe.loc[mask, 'enter_tag'].astype(str) + '|atr14=' +
                dataframe.loc[mask, 'atr14'].map(lambda v: format(float(v), '.9f'))
            )
        return dataframe

    def custom_stoploss(self, pair, trade, current_time, current_rate,
                        current_profit, after_fill, **kwargs):
        tag = str(trade.enter_tag or '')
        if '|atr14=' not in tag:
            raise ValueError('Missing signal-time ATR in entry tag')
        atr = float(tag.split('|atr14=',1)[1].split('|',1)[0])
        if not math.isfinite(atr) or atr <= 0:
            raise ValueError('Invalid signal-time ATR')
        stop_price = float(trade.open_rate) - self.atr_multiple * atr
        if stop_price <= 0:
            raise ValueError('ATR stop invalid (nonpositive price)')
        return stoploss_from_absolute(stop_price, current_rate=current_rate,
                                      is_short=trade.is_short, leverage=trade.leverage)
