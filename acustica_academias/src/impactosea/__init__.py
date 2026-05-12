"""ImpactoSEA-ProPG acoustic design tools."""

from .catalog import load_solutions
from .constants import (
    CONCRETE_SLAB_DENSITY_KG_M3,
    CONCRETE_SLAB_POISSON_RATIO,
    CONCRETE_SLAB_YOUNG_MODULUS_PA,
    G_CURVES,
    IMPACT_BANDS_HZ,
)
from .engine import calculate_scenario, estimate_original_contact_time
from .feasibility import assess_feasibility
from .models import (
    ADSReport,
    BandResult,
    ContactTimeEstimate,
    FeasibilityInput,
    MitigationSolution,
    ProjectInput,
    ScenarioResult,
)
from .report import build_ads_markdown

__all__ = [
    "ADSReport",
    "BandResult",
    "CONCRETE_SLAB_DENSITY_KG_M3",
    "CONCRETE_SLAB_POISSON_RATIO",
    "CONCRETE_SLAB_YOUNG_MODULUS_PA",
    "ContactTimeEstimate",
    "FeasibilityInput",
    "G_CURVES",
    "IMPACT_BANDS_HZ",
    "MitigationSolution",
    "ProjectInput",
    "ScenarioResult",
    "assess_feasibility",
    "build_ads_markdown",
    "calculate_scenario",
    "estimate_original_contact_time",
    "load_solutions",
]
