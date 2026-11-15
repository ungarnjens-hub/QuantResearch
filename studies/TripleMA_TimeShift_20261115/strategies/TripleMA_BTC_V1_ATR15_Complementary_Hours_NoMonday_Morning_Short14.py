from datetime import timezone
from TripleMA_BTC_V1_ATR15_Complementary_Hours import TripleMA_BTC_V1_ATR15_Complementary_Hours

class TripleMA_BTC_V1_ATR15_Complementary_Hours_NoMonday_Morning_Short14(TripleMA_BTC_V1_ATR15_Complementary_Hours):
    # Explorative neue Regel: Montag vollständig; LONG 05:00-07:59; SHORT 14:00-14:59 UTC
    def confirm_trade_entry(self, pair, order_type, amount, rate,
                            time_in_force, current_time, entry_tag, side, **kwargs):
        if current_time.tzinfo is None or current_time.utcoffset() is None:
            raise ValueError("Entry confirmation requires timezone-aware UTC timestamp")
        utc = current_time.astimezone(timezone.utc)
        if (utc.weekday() == 0 or
            (side == "long" and utc.hour in (5, 6, 7)) or
            (side == "short" and utc.hour == 14)):
            return False
        return super().confirm_trade_entry(
            pair, order_type, amount, rate, time_in_force,
            current_time, entry_tag, side, **kwargs)
