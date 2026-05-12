from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from impactosea.catalog import load_solutions
from impactosea.constants import (
    CONCRETE_SLAB_DENSITY_KG_M3,
    CONCRETE_SLAB_POISSON_RATIO,
    CONCRETE_SLAB_YOUNG_MODULUS_PA,
    G_CURVES,
    IMPACT_BANDS_HZ,
)
from impactosea.engine import (
    calculate_scenario,
    classify_band_g,
    contact_cutoff_hz,
    equivalent_cubic_room_project,
    estimate_original_contact_time,
    validate_h3_case,
)
from impactosea.models import ProjectInput


class EngineTest(unittest.TestCase):
    def test_h3_validation_is_within_six_db(self) -> None:
        validation = validate_h3_case()
        max_error = max(abs(row["Diferenca_dB"]) for row in validation)
        self.assertLessEqual(max_error, 6.0)

    def test_g_curves_cover_31_5_to_4k(self) -> None:
        for g_value, curve in G_CURVES.items():
            self.assertIn(31.5, curve, msg=f"G{g_value}")
            self.assertIn(4000.0, curve, msg=f"G{g_value}")
            self.assertEqual(set(curve), set(IMPACT_BANDS_HZ))
        self.assertEqual(G_CURVES[10][31.5], 57)
        self.assertEqual(G_CURVES[50][4000.0], 40)

    def test_classifies_band_against_first_g_curve_not_exceeded(self) -> None:
        self.assertEqual(classify_band_g(100.0, 34.0), "G20")
        self.assertEqual(classify_band_g(100.0, 62.0), "> G50")

    def test_scenario_contains_expected_alerts(self) -> None:
        project = ProjectInput(
            impact_mass_kg=15.0,
            drop_height_m=0.5,
            room_width_m=2.58,
            room_length_m=2.62,
            room_height_m=3.24,
            reverberation_time_s=0.5,
            slab_thickness_m=0.25,
            slab_density_kg_m3=2400.0,
            young_modulus_pa=30e9,
            poisson_ratio=0.2,
            tc_original_ms=3.0,
        )
        solution = load_solutions()[1]
        result = calculate_scenario(project, solution, target_g=25)
        all_warnings = " ".join(" ".join(band.warnings) for band in result.bands)
        self.assertIn("M<1", all_warnings)
        self.assertIn("cutoff", all_warnings)
        self.assertIn("cap SDOF ativo", all_warnings)
        self.assertIn("acima de 2 kHz", all_warnings)

    def test_contact_cutoff(self) -> None:
        self.assertEqual(contact_cutoff_hz(0.003), 500.0)

    def test_equivalent_room_h3_defaults(self) -> None:
        project = equivalent_cubic_room_project()
        self.assertAlmostEqual(project.room_volume_m3, 15.0)

    def test_estimated_contact_time_feeds_project_and_keeps_diagnostic_separate(self) -> None:
        estimate = estimate_original_contact_time(
            impact_mass_kg=15.0,
            drop_height_m=0.5,
            room_width_m=2.58,
            room_length_m=2.62,
            slab_thickness_m=0.25,
        )
        project = ProjectInput(
            impact_mass_kg=15.0,
            drop_height_m=0.5,
            room_width_m=2.58,
            room_length_m=2.62,
            room_height_m=3.24,
            reverberation_time_s=0.5,
            slab_thickness_m=0.25,
            slab_density_kg_m3=CONCRETE_SLAB_DENSITY_KG_M3,
            young_modulus_pa=CONCRETE_SLAB_YOUNG_MODULUS_PA,
            poisson_ratio=CONCRETE_SLAB_POISSON_RATIO,
            tc_original_ms=estimate.tc_calibrated_ms,
        )
        solution = load_solutions()[1]
        result = calculate_scenario(project, solution, target_g=25)

        self.assertGreaterEqual(estimate.tc_calibrated_ms, 2.0)
        self.assertLessEqual(estimate.tc_calibrated_ms, 7.0)
        self.assertAlmostEqual(project.tc_original_ms, estimate.tc_calibrated_ms)
        self.assertNotAlmostEqual(estimate.tc_mechanical_ms, project.tc_original_ms)
        self.assertGreater(result.global_lmax_original_db, result.global_lmax_mitigated_db)

    def test_thicker_concrete_slab_increases_panel_frequency(self) -> None:
        thin = estimate_original_contact_time(
            impact_mass_kg=15.0,
            drop_height_m=0.5,
            room_width_m=2.58,
            room_length_m=2.62,
            slab_thickness_m=0.20,
        )
        thick = estimate_original_contact_time(
            impact_mass_kg=15.0,
            drop_height_m=0.5,
            room_width_m=2.58,
            room_length_m=2.62,
            slab_thickness_m=0.30,
        )

        self.assertGreater(thick.panel_frequency_hz, thin.panel_frequency_hz)
        self.assertLess(thick.tc_calibrated_ms, thin.tc_calibrated_ms)

    def test_concrete_slab_constants_are_fixed_defaults(self) -> None:
        self.assertEqual(CONCRETE_SLAB_DENSITY_KG_M3, 2400.0)
        self.assertEqual(CONCRETE_SLAB_YOUNG_MODULUS_PA, 30e9)
        self.assertEqual(CONCRETE_SLAB_POISSON_RATIO, 0.20)


if __name__ == "__main__":
    unittest.main()
