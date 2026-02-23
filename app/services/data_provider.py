from __future__ import annotations

from datetime import datetime
from typing import Tuple

import yfinance as yf
from dateutil.parser import parse


class EarningsDataProvider:
    """通过 yfinance 获取财报日期与时段信息。"""

    @staticmethod
    def fetch_earnings_info(ticker: str) -> Tuple[str, str, str, str]:
        stock = yf.Ticker(ticker)
        info = stock.info
        company_name = info.get("shortName") or info.get("longName") or ticker.upper()

        earnings_date = None
        session = "unknown"

        calendar = stock.calendar
        if calendar is not None and not getattr(calendar, "empty", True):
            if "Earnings Date" in calendar.index:
                raw = calendar.loc["Earnings Date"].values[0]
                if raw is not None:
                    parsed = parse(str(raw))
                    earnings_date = parsed.strftime("%Y-%m-%d")
            if "Earnings Call Time" in calendar.index:
                session_raw = str(calendar.loc["Earnings Call Time"].values[0]).lower()
                if "am" in session_raw or "before" in session_raw:
                    session = "pre-market"
                elif "pm" in session_raw or "after" in session_raw:
                    session = "post-market"

        if not earnings_date:
            # 降级策略：尝试从 info 读取 next earnings timestamp
            ts = info.get("earningsTimestamp") or info.get("earningsTimestampStart")
            if ts:
                earnings_date = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")

        if not earnings_date:
            earnings_date = "N/A"

        return ticker.upper(), company_name, earnings_date, session
