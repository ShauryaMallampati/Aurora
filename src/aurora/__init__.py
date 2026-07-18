"""AURORA: reproducible multi-agent wildfire-response simulation tools."""

from .coordination import (
    EpisodeResult,
    EpisodeTrace,
    run_episode,
    run_episode_with_trace,
    run_strategy_episode,
    verify_trace,
)
from .simulator import BURNED, BURNING, SUPPRESSED, UNBURNED, FireSim, WeatherState
from .strategy import HeuristicStrategist, Strategist, StrategyPlan, Zone
from .types import Scenario

__all__ = [
    "UNBURNED",
    "BURNING",
    "BURNED",
    "SUPPRESSED",
    "FireSim",
    "WeatherState",
    "Scenario",
    "Strategist",
    "HeuristicStrategist",
    "StrategyPlan",
    "Zone",
    "EpisodeResult",
    "EpisodeTrace",
    "run_episode",
    "run_episode_with_trace",
    "run_strategy_episode",
    "verify_trace",
]

__version__ = "0.4.0"
