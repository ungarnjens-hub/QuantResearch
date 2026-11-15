"""Ungated short mirror; identical signal and stop formulas to prior gated mirror."""
import math
from pandas import DataFrame
from freqtrade.strategy import stoploss_from_absolute
from TripleMA_BTC_V1_ATR15_TrendOnly_NoGate import TripleMA_BTC_V1_ATR15_TrendOnly_NoGate
class TripleMA_BTC_V1_ATR15_LongShort_NoGate(TripleMA_BTC_V1_ATR15_TrendOnly_NoGate):
    can_short = True
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        crossed_down = ((dataframe['ema7'] < dataframe['ema25']) &
                        (dataframe['ema7'].shift(1) >= dataframe['ema25'].shift(1)))
        trend_down = ((dataframe['ma200_growth_24h'] <= -self.min_ma200_rise_24h) &
                      (dataframe['close'] < dataframe['ema200']))
        ready = (dataframe['volume'] > 0) & dataframe['prior_oversold_atr'].notna()
        mask = ready & crossed_down & trend_down
        if mask.any():
            vals = dataframe.loc[mask, 'atr14']
            if vals.isna().any() or (vals <= 0).any():
                raise ValueError('Invalid finalized ATR for short signal')
            dataframe.loc[mask, 'enter_short'] = 1
            dataframe.loc[mask, 'enter_tag'] = ('short_trend|atr14=' +
                vals.map(lambda v: format(float(v), '.9f')))
        if (dataframe['enter_long'].fillna(0).eq(1) & dataframe['enter_short'].fillna(0).eq(1)).any():
            raise ValueError('Simultaneous contradictory signals')
        return dataframe
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_exit_trend(dataframe, metadata)
        crossed_up = ((dataframe['ema7'] > dataframe['ema25']) &
                      (dataframe['ema7'].shift(1) <= dataframe['ema25'].shift(1)))
        dataframe.loc[(dataframe['volume'] > 0) & crossed_up, 'exit_short'] = 1
        return dataframe
    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, after_fill, **kwargs):
        tag = str(trade.enter_tag or '')
        if '|atr14=' not in tag:
            raise ValueError('Missing signal-time ATR')
        atr = float(tag.split('|atr14=', 1)[1].split('|',1)[0])
        if not math.isfinite(atr) or atr <= 0:
            raise ValueError('Invalid signal ATR')
        absolute = float(trade.open_rate) + (1.5*atr if trade.is_short else -1.5*atr)
        if absolute <= 0: raise ValueError('Invalid stop price')
        return stoploss_from_absolute(absolute, current_rate=current_rate,
                                      is_short=trade.is_short, leverage=trade.leverage)
