"""
Portfolio Configuration Dataclass

Defines the typed configuration schema for portfolio analysis and monitoring.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Position:
    """Single stock position."""
    ticker: str = ""
    shares: int = 0
    buy_price_eur: float = 0.0
    current_price_eur: float = 0.0
    target_low_eur: float = 0.0
    target_high_eur: float = 0.0
    currency: str = "EUR"  # EUR or USD
    is_open: bool = True
    sell_price_eur: Optional[float] = None  # Set when position is closed
    notes: str = ""


@dataclass
class Settings:
    """Portfolio settings."""
    usd_to_eur: float = 0.85
    base_currency: str = "EUR"
    analysis_year: int = {{ cookiecutter.analysis_year }}


@dataclass
class Monitoring:
    """Monthly monitoring settings."""
    last_update: str = ""  # YYYY-MM-DD
    save_history: bool = True
    history_file: str = "portfolio_history.csv"


@dataclass
class Output:
    """Output settings."""
    save_plots: bool = True
    output_dir: str = "results"
    verbose: bool = True


@dataclass
class {{ cookiecutter.config_name }}:
    """Root configuration for portfolio analysis."""
    settings: Settings = field(default_factory=Settings)
    monitoring: Monitoring = field(default_factory=Monitoring)
    output: Output = field(default_factory=Output)
    positions: List[Position] = field(default_factory=list)
