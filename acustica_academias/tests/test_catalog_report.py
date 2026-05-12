from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from impactosea.catalog import load_solutions
from impactosea.engine import calculate_scenario
from impactosea.feasibility import assess_feasibility
from impactosea.models import FeasibilityInput, ProjectInput
from impactosea.report import build_ads_markdown


class CatalogReportTest(unittest.TestCase):
    def test_catalog_loads_valid_solutions(self) -> None:
        solutions = load_solutions()
        self.assertGreaterEqual(len(solutions), 3)
        for solution in solutions:
            self.assertTrue(solution.id)
            self.assertGreater(solution.tc_mitigated_ms, 0)
            self.assertGreater(solution.fn_hz, 0)
            self.assertGreater(solution.cap_db, 0)
            self.assertTrue(solution.layers)

    def test_ads_contains_required_sections(self) -> None:
        feasibility = FeasibilityInput(
            intended_use="Academia com pesos livres",
            sensitive_receptor="Dormitório residencial abaixo",
            activity_type="Pesos livres / halteres",
            has_dry_concrete_slab=True,
            flanking_risk="Médio",
            method1_recommended=True,
        )
        assessment = assess_feasibility(feasibility)
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
        report = build_ads_markdown(feasibility, assessment, project, solution, result)

        for heading in (
            "Avaliação de Viabilidade",
            "Modelagem e Predição",
            "Especificação da Mitigação",
            "Resultados e Critério-Alvo",
            "Análise de Incerteza",
            "Limitações",
        ):
            self.assertIn(heading, report.markdown)
        self.assertIn("|", report.markdown)
        self.assertIn("G25", report.markdown)


if __name__ == "__main__":
    unittest.main()
