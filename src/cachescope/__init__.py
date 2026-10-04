"""CacheScope public API."""

from .models import Access, AccessResult, CacheConfig, SimulationStats
from .experiments import ExperimentResult, run_experiments
from .simulator import CacheSimulator

__all__ = [
    "Access",
    "AccessResult",
    "CacheConfig",
    "CacheSimulator",
    "ExperimentResult",
    "SimulationStats",
    "run_experiments",
]

__version__ = "0.1.0"
