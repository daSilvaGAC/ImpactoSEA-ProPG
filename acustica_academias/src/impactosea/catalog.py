"""Mitigation solution catalog loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import MitigationSolution


REQUIRED_SOLUTION_FIELDS = {
    "id",
    "name",
    "summary",
    "layers",
    "tc_mitigated_ms",
    "fn_hz",
    "zeta",
    "cap_db",
    "source",
    "validity",
}


def _load_catalog_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except Exception:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Catalog root must be a mapping.")
    return data


def validate_catalog_mapping(data: dict[str, Any]) -> None:
    if "solutions" not in data or not isinstance(data["solutions"], list):
        raise ValueError("Catalog must contain a 'solutions' list.")
    if not data["solutions"]:
        raise ValueError("Catalog must contain at least one solution.")

    seen_ids: set[str] = set()
    for index, solution in enumerate(data["solutions"]):
        if not isinstance(solution, dict):
            raise ValueError(f"Solution at index {index} must be a mapping.")
        missing = REQUIRED_SOLUTION_FIELDS - set(solution)
        if missing:
            raise ValueError(f"Solution {index} is missing fields: {sorted(missing)}")
        if solution["id"] in seen_ids:
            raise ValueError(f"Duplicate solution id: {solution['id']}")
        seen_ids.add(str(solution["id"]))

        if not isinstance(solution["layers"], list) or not solution["layers"]:
            raise ValueError(f"Solution {solution['id']} must contain layers.")
        for layer in solution["layers"]:
            if not {"material", "thickness_mm", "role"} <= set(layer):
                raise ValueError(f"Layer in {solution['id']} has missing fields.")
            if float(layer["thickness_mm"]) < 0:
                raise ValueError(f"Layer in {solution['id']} has negative thickness.")

        for numeric_field in ("tc_mitigated_ms", "fn_hz", "zeta", "cap_db"):
            if float(solution[numeric_field]) <= 0:
                raise ValueError(
                    f"Solution {solution['id']} field {numeric_field} must be positive."
                )


def load_solutions(path: str | Path | None = None) -> list[MitigationSolution]:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "data" / "solutions.yaml"
    path = Path(path)
    data = _load_catalog_mapping(path)
    validate_catalog_mapping(data)
    return [MitigationSolution.from_mapping(item) for item in data["solutions"]]
