"""Typed data structures for the ImpactoSEA-ProPG app."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProjectInput:
    impact_mass_kg: float
    drop_height_m: float
    room_width_m: float
    room_length_m: float
    room_height_m: float
    reverberation_time_s: float
    slab_thickness_m: float
    slab_density_kg_m3: float
    young_modulus_pa: float
    poisson_ratio: float
    tc_original_ms: float

    @property
    def room_volume_m3(self) -> float:
        return self.room_width_m * self.room_length_m * self.room_height_m

    @property
    def receiver_floor_area_m2(self) -> float:
        return self.room_width_m * self.room_length_m

    @property
    def total_surface_area_m2(self) -> float:
        w = self.room_width_m
        l = self.room_length_m
        h = self.room_height_m
        return 2 * (w * l + w * h + l * h)

    @property
    def total_edge_length_m(self) -> float:
        return 4 * (self.room_width_m + self.room_length_m + self.room_height_m)

    @property
    def tc_original_s(self) -> float:
        return self.tc_original_ms / 1000.0


@dataclass(frozen=True)
class ContactTimeEstimate:
    tc_calibrated_ms: float
    tc_mechanical_ms: float
    fc_calibrated_hz: float
    fc_mechanical_hz: float
    panel_frequency_hz: float
    source_factor: float
    mechanical_contact_stiffness_n_m: float
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FeasibilityInput:
    intended_use: str
    sensitive_receptor: str
    activity_type: str
    has_dry_concrete_slab: bool
    flanking_risk: str
    method1_recommended: bool
    notes: str = ""


@dataclass(frozen=True)
class FeasibilityAssessment:
    risk_level: str
    score: int
    recommendation: str
    flags: tuple[str, ...]


@dataclass(frozen=True)
class MitigationLayer:
    material: str
    thickness_mm: float
    role: str


@dataclass(frozen=True)
class MitigationSolution:
    id: str
    name: str
    summary: str
    layers: tuple[MitigationLayer, ...]
    tc_mitigated_ms: float
    fn_hz: float
    zeta: float
    cap_db: float
    source: str
    validity: str
    uncertainty: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "MitigationSolution":
        layers = tuple(MitigationLayer(**layer) for layer in data["layers"])
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            summary=str(data["summary"]),
            layers=layers,
            tc_mitigated_ms=float(data["tc_mitigated_ms"]),
            fn_hz=float(data["fn_hz"]),
            zeta=float(data["zeta"]),
            cap_db=float(data["cap_db"]),
            source=str(data["source"]),
            validity=str(data["validity"]),
            uncertainty=tuple(str(item) for item in data.get("uncertainty", [])),
        )

    @property
    def tc_mitigated_s(self) -> float:
        return self.tc_mitigated_ms / 1000.0


@dataclass(frozen=True)
class BandResult:
    frequency_hz: float
    lmax_original_db: float
    lmax_contact_mitigated_db: float
    attenuation_sdof_db: float
    lmax_mitigated_db: float
    target_g_limit_db: float
    target_margin_db: float
    band_g_classification: str
    modal_overlap: float
    contact_correction_db: float
    contact_cutoff_hz: float
    vibration_level_db: float
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioResult:
    target_g: int
    bands: tuple[BandResult, ...]
    overall_g_classification: str
    global_lmax_original_db: float
    global_lmax_mitigated_db: float
    global_reduction_db: float
    lfispl_original_db: float
    lfispl_mitigated_db: float
    lir_original: float
    lir_mitigated: float
    worst_margin_db: float
    worst_margin_frequency_hz: float
    critical_bands_hz: tuple[float, ...]
    uncertainty_notes: tuple[str, ...]


@dataclass(frozen=True)
class ADSReport:
    markdown: str
