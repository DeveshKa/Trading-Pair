"""Future authenticated feeds integrate here; no Kite credentials are requested in v0.1."""
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol


@dataclass(frozen=True)
class Quote:
    instrument_id: str
    event_at: datetime
    received_at: datetime
    bid: float
    ask: float
    source: str
    sequence: str

    def __post_init__(self):
        import math
        if self.event_at.tzinfo is None or self.received_at.tzinfo is None:
            raise ValueError("Quote timestamps must be timezone aware")
        if not math.isfinite(self.bid) or not math.isfinite(self.ask) or not 0 < self.bid <= self.ask:
            raise ValueError("Invalid quote")


class QuoteProvider(Protocol):
    def subscribe(self, instrument_ids: list[str]) -> Iterable[Quote]: ...


# Historical adapters implement data.HistoricalProvider and output the same validated
# snapshot contract. A future Kite bridge maps instrument tokens to durable IDs here,
# converts timestamps, handles disconnects and authenticates outside the research engine.
