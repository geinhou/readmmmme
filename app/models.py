from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class WatchItem:
    ticker: str
    company_name: str
    earnings_date: Optional[str]
    market_session: str  # pre-market / post-market / unknown
    ir_url: Optional[str] = None
    last_pdf_path: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict) -> "WatchItem":
        return cls(**value)

    def set_updated_now(self) -> None:
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
