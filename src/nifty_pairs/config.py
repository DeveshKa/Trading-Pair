from dataclasses import asdict, dataclass, fields
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class Config:
    strategy: str = "cointegration"
    formation_sessions: int = 252
    top_pairs: int = 5
    family_alpha: float = 0.05
    entry_z: float = 2.0
    exit_z: float = 0.5
    stop_z: float = 4.0
    max_holding_sessions: int = 60
    min_half_life: float = 5.0
    max_half_life: float = 60.0
    initial_capital: float = 1_000_000.0
    pair_gross_fraction: float = 0.15
    max_gross_fraction: float = 1.0
    max_underlying_fraction: float = 0.15
    max_sector_fraction: float = 0.35
    max_net_fraction: float = 0.10
    pair_loss_fraction: float = 0.0025
    portfolio_drawdown_pause: float = 0.08
    fee_bps: float = 5.0
    slippage_bps: float = 10.0
    short_borrow_annual: float = 0.05
    risk_free_annual: float = 0.0
    same_sector: bool = True
    require_membership: bool = True

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if field.type is bool and type(value) is not bool:
                raise ValueError(f"{field.name} must be boolean")
            if field.type is float and (type(value) not in (int, float)):
                raise ValueError(f"{field.name} must be numeric")
            if field.type is int and type(value) is not int:
                raise ValueError(f"{field.name} must be an integer")
        if self.strategy not in {"cointegration", "distance"}:
            raise ValueError("strategy must be cointegration or distance")
        for name, value in asdict(self).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if not math.isfinite(value) or value < 0:
                    raise ValueError(f"{name} must be finite and nonnegative")
        if self.formation_sessions < 40 or self.top_pairs < 1:
            raise ValueError("Need at least 40 formation sessions and one pair")
        if not 0 <= self.exit_z < self.entry_z < self.stop_z:
            raise ValueError("Require exit_z < entry_z < stop_z")
        if not 0 < self.family_alpha < 1 or self.initial_capital <= 0:
            raise ValueError("Invalid alpha or capital")
        if self.min_half_life > self.max_half_life:
            raise ValueError("Invalid half-life bounds")
        if self.fee_bps >= 10000 or self.slippage_bps >= 10000:
            raise ValueError("Basis point cost must be below 10000")
        for field in ("formation_sessions", "top_pairs", "max_holding_sessions"):
            if not isinstance(getattr(self, field), int) or getattr(self, field) < 1:
                raise ValueError(f"{field} must be a positive integer")
        for field in ("pair_gross_fraction", "max_gross_fraction", "max_underlying_fraction",
                      "max_sector_fraction", "max_net_fraction", "pair_loss_fraction",
                      "portfolio_drawdown_pause"):
            if not 0 < getattr(self, field) <= 1:
                raise ValueError(f"{field} must be in (0, 1]")

    @classmethod
    def load(cls, path):
        return cls(**json.loads(Path(path).read_text())) if path else cls()

    def to_dict(self):
        return asdict(self)
