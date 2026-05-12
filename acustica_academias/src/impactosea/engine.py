"""SEA prediction and mitigation calculations."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from .constants import G_CURVES, H3_VALIDATION_BANDS_HZ, IMPACT_BANDS_HZ
from .models import BandResult, MitigationSolution, ProjectInput, ScenarioResult

FLOAT_TINY = 2.2250738585072014e-308


def contact_cutoff_hz(tc_s: float) -> float:
    if tc_s <= 0:
        raise ValueError("tc_s must be greater than zero.")
    return 1.5 / tc_s


def contact_spectrum_correction_db(
    frequency_hz: float,
    tc_s: float,
    rolloff_db_per_octave: float = 12.0,
) -> float:
    fc = contact_cutoff_hz(tc_s)
    if frequency_hz <= fc:
        return 0.0
    return -rolloff_db_per_octave * math.log2(frequency_hz / fc)


def a_weighting_db(frequency_hz: float) -> float:
    f = float(frequency_hz)
    f2 = f**2
    ra = (12194.0**2 * f2**2) / (
        (f2 + 20.6**2)
        * math.sqrt((f2 + 107.7**2) * (f2 + 737.9**2))
        * (f2 + 12194.0**2)
    )
    return 20 * math.log10(ra) + 2.0


def log_sum_db(levels_db: Iterable[float]) -> float:
    levels = list(levels_db)
    if not levels:
        return float("nan")
    return 10 * math.log10(sum(10 ** (level / 10) for level in levels))


def broadband_lamax_db(
    frequencies_hz: Iterable[float],
    levels_db: Iterable[float],
    apply_a_weighting: bool = True,
) -> float:
    freqs = list(frequencies_hz)
    levels = list(levels_db)
    if apply_a_weighting:
        levels = [
            level + a_weighting_db(frequency)
            for frequency, level in zip(freqs, levels)
        ]
    return log_sum_db(levels)


def calculate_lfispl(
    frequencies_hz: Sequence[float],
    levels_db: Sequence[float],
    low_frequency_bands: tuple[float, ...] = (50.0, 63.0, 80.0),
) -> float:
    by_band = {float(freq): level for freq, level in zip(frequencies_hz, levels_db)}
    missing = [band for band in low_frequency_bands if band not in by_band]
    if missing:
        raise ValueError(f"Missing low-frequency bands: {missing}")
    return log_sum_db(by_band[band] for band in low_frequency_bands)


def calculate_lir(lfispl_db: float) -> float:
    return 190.0 - 2.0 * lfispl_db


def _validate_positive(values: dict[str, float]) -> None:
    for name, value in values.items():
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")


def sea_engine_lmax(
    frequency_hz: float,
    project: ProjectInput,
    tc_s: float,
    *,
    c0: float = 343.0,
    rho0: float = 1.21,
    sigma: float = 1.0,
    apply_contact_filter: bool = True,
) -> dict[str, float | str]:
    _validate_positive(
        {
            "frequency_hz": frequency_hz,
            "impact_mass_kg": project.impact_mass_kg,
            "drop_height_m": project.drop_height_m,
            "room_volume_m3": project.room_volume_m3,
            "total_surface_area_m2": project.total_surface_area_m2,
            "total_edge_length_m": project.total_edge_length_m,
            "reverberation_time_s": project.reverberation_time_s,
            "slab_thickness_m": project.slab_thickness_m,
            "slab_density_kg_m3": project.slab_density_kg_m3,
            "young_modulus_pa": project.young_modulus_pa,
            "tc_s": tc_s,
        }
    )
    if not -0.45 < project.poisson_ratio < 0.5:
        raise ValueError("poisson_ratio must be between -0.45 and 0.5.")

    f = float(frequency_hz)
    volume = project.room_volume_m3
    surface_area = project.total_surface_area_m2
    edge_length = project.total_edge_length_m
    t60 = project.reverberation_time_s
    slab_thickness = project.slab_thickness_m
    density = project.slab_density_kg_m3
    young = project.young_modulus_pa
    poisson = project.poisson_ratio

    n_f = (
        (4 * math.pi * f**2 * volume) / c0**3
        + (math.pi * f * surface_area) / (2 * c0**2)
        + edge_length / (8 * c0)
    )
    bandwidth_hz = 0.23 * f
    eta_2 = 2.2 / (f * t60)
    modal_overlap = f * eta_2 * n_f

    impact_velocity = math.sqrt(2 * 9.81 * project.drop_height_m)
    force_rms_sq = 2 * (project.impact_mass_kg * impact_velocity) ** 2 * bandwidth_hz
    omega = 2 * math.pi * f

    bending_stiffness = (young * slab_thickness**3) / (12 * (1 - poisson**2))
    plate_impedance = 8 * math.sqrt(bending_stiffness * density * slab_thickness)
    power_in_w = force_rms_sq * (
        plate_impedance / (plate_impedance**2 + (omega * project.impact_mass_kg) ** 2)
    )

    surface_density = density * slab_thickness
    eta_1 = 0.01 + 1 / math.sqrt(f)
    eta_12 = (rho0 * c0 * sigma) / (omega * surface_density)

    receiver_energy = (eta_12 / (eta_1 * eta_2)) * (power_in_w / omega)
    receiver_energy = max(receiver_energy, FLOAT_TINY)
    lp_continuous_db = 10 * math.log10(receiver_energy / 1e-12) - 10 * math.log10(volume) + 25.4

    lmax_100ms_db = lp_continuous_db + 10 * math.log10(tc_s / 0.1)

    fc = contact_cutoff_hz(tc_s)
    contact_correction = (
        contact_spectrum_correction_db(f, tc_s) if apply_contact_filter else 0.0
    )
    lmax_db = lmax_100ms_db + contact_correction

    equivalent_slab_mass = density * slab_thickness * project.receiver_floor_area_m2
    source_energy = power_in_w / (omega * eta_1)
    v_rms = math.sqrt(max(source_energy / equivalent_slab_mass, FLOAT_TINY))
    vibration_level_db = 20 * math.log10(v_rms / 1e-9)

    warnings: list[str] = []
    if modal_overlap < 1:
        warnings.append("M<1: SEA pouco robusto nesta banda")
    if f > fc:
        warnings.append("banda acima do cutoff de contato")
    if f > 2000:
        warnings.append("banda acima de 2 kHz: predição SEA com menor confiança")

    return {
        "frequency_hz": f,
        "n_f": n_f,
        "bandwidth_hz": bandwidth_hz,
        "eta_1": eta_1,
        "eta_2": eta_2,
        "modal_overlap": modal_overlap,
        "power_in_w": power_in_w,
        "lp_continuous_db": lp_continuous_db,
        "lmax_100ms_db": lmax_100ms_db,
        "contact_cutoff_hz": fc,
        "contact_correction_db": contact_correction,
        "lmax_db": lmax_db,
        "vibration_level_db": vibration_level_db,
        "warnings": "; ".join(warnings),
    }


def sdof_attenuation(
    frequency_hz: float,
    fn_hz: float,
    *,
    zeta: float = 0.08,
    cap_db: float = 24.0,
) -> dict[str, float | bool]:
    _validate_positive({"frequency_hz": frequency_hz, "fn_hz": fn_hz, "zeta": zeta})
    if cap_db < 0:
        raise ValueError("cap_db must be non-negative.")

    r = frequency_hz / fn_hz
    transmissibility = math.sqrt(1 + (2 * zeta * r) ** 2) / math.sqrt(
        (1 - r**2) ** 2 + (2 * zeta * r) ** 2
    )
    raw_attenuation = max(0.0, -20 * math.log10(transmissibility))
    attenuation = min(raw_attenuation, cap_db)

    return {
        "attenuation_db": attenuation,
        "raw_attenuation_db": raw_attenuation,
        "cap_active": raw_attenuation > cap_db,
        "frequency_ratio": r,
        "near_resonance": 0.7 <= r <= 1.4,
    }


def g_curve_limit(frequency_hz: float, g_value: int) -> float:
    if g_value not in G_CURVES:
        raise ValueError(f"Unknown G curve: {g_value}")
    try:
        return float(G_CURVES[g_value][float(frequency_hz)])
    except KeyError as exc:
        raise ValueError(f"Frequency {frequency_hz} Hz is not in the G-Curve table.") from exc


def classify_band_g(frequency_hz: float, level_db: float) -> str:
    for g_value in sorted(G_CURVES):
        if level_db <= g_curve_limit(frequency_hz, g_value):
            return f"G{g_value}"
    return "> G50"


def classify_spectrum_g(bands: Sequence[BandResult]) -> str:
    required_g_values: list[int] = []
    for band in bands:
        band_class = band.band_g_classification
        if band_class == "> G50":
            return "> G50"
        required_g_values.append(int(band_class.removeprefix("G")))
    if not required_g_values:
        return "sem dados"
    return f"G{max(required_g_values)}"


def calculate_scenario(
    project: ProjectInput,
    solution: MitigationSolution,
    *,
    target_g: int = 25,
    bands_hz: Sequence[float] = IMPACT_BANDS_HZ,
) -> ScenarioResult:
    if target_g not in G_CURVES:
        raise ValueError(f"Unknown target G curve: {target_g}")

    band_results: list[BandResult] = []
    for frequency in bands_hz:
        original = sea_engine_lmax(frequency, project, project.tc_original_s)
        contact = sea_engine_lmax(frequency, project, solution.tc_mitigated_s)
        sdof = sdof_attenuation(
            frequency,
            solution.fn_hz,
            zeta=solution.zeta,
            cap_db=solution.cap_db,
        )
        mitigated = float(contact["lmax_db"]) - float(sdof["attenuation_db"])
        target_limit = g_curve_limit(frequency, target_g)

        warnings: list[str] = []
        for prefix, details in (("original", original), ("mitigado", contact)):
            if details["warnings"]:
                warnings.append(f"{prefix}: {details['warnings']}")
        if sdof["cap_active"]:
            warnings.append("cap SDOF ativo")
        if sdof["near_resonance"]:
            warnings.append("próximo da ressonância SDOF")
        if frequency > 2000:
            warnings.append("usar bandas altas como apoio gráfico, não como validação isolada")

        band_results.append(
            BandResult(
                frequency_hz=float(frequency),
                lmax_original_db=float(original["lmax_db"]),
                lmax_contact_mitigated_db=float(contact["lmax_db"]),
                attenuation_sdof_db=float(sdof["attenuation_db"]),
                lmax_mitigated_db=mitigated,
                target_g_limit_db=target_limit,
                target_margin_db=target_limit - mitigated,
                band_g_classification=classify_band_g(frequency, mitigated),
                modal_overlap=float(contact["modal_overlap"]),
                contact_correction_db=float(contact["contact_correction_db"]),
                contact_cutoff_hz=float(contact["contact_cutoff_hz"]),
                vibration_level_db=float(contact["vibration_level_db"]),
                warnings=tuple(dict.fromkeys(warnings)),
            )
        )

    freqs = [band.frequency_hz for band in band_results]
    original_levels = [band.lmax_original_db for band in band_results]
    mitigated_levels = [band.lmax_mitigated_db for band in band_results]
    lfispl_original = calculate_lfispl(freqs, original_levels)
    lfispl_mitigated = calculate_lfispl(freqs, mitigated_levels)
    worst_band = min(band_results, key=lambda item: item.target_margin_db)
    critical_bands = tuple(
        band.frequency_hz for band in band_results if band.target_margin_db < 0
    )

    uncertainty_notes = [
        "Predição SEA simplificada; bandas com M<1 devem ser tratadas como baixa robustez modal.",
        "Caminhos de flanqueamento, pilares, fachadas, dutos e elementos leves não estão modelados.",
        "Tc e parâmetros SDOF devem ser substituídos por ensaio do conjunto real quando disponíveis.",
        "Bandas acima de 2 kHz são apresentadas para compatibilidade gráfica com Curvas-G até 4 kHz.",
        "Medição até 20 Hz é recomendável para diagnóstico de picos sub-31,5 Hz, fora da classificação G.",
    ]
    uncertainty_notes.extend(solution.uncertainty)

    global_original = log_sum_db(original_levels)
    global_mitigated = log_sum_db(mitigated_levels)

    return ScenarioResult(
        target_g=target_g,
        bands=tuple(band_results),
        overall_g_classification=classify_spectrum_g(band_results),
        global_lmax_original_db=global_original,
        global_lmax_mitigated_db=global_mitigated,
        global_reduction_db=global_original - global_mitigated,
        lfispl_original_db=lfispl_original,
        lfispl_mitigated_db=lfispl_mitigated,
        lir_original=calculate_lir(lfispl_original),
        lir_mitigated=calculate_lir(lfispl_mitigated),
        worst_margin_db=worst_band.target_margin_db,
        worst_margin_frequency_hz=worst_band.frequency_hz,
        critical_bands_hz=critical_bands,
        uncertainty_notes=tuple(dict.fromkeys(uncertainty_notes)),
    )


def scenario_to_records(result: ScenarioResult) -> list[dict[str, float | str]]:
    return [
        {
            "Freq_Hz": band.frequency_hz,
            "Lmax_original_dB": band.lmax_original_db,
            "Lmax_contato_mitigado_dB": band.lmax_contact_mitigated_db,
            "Atenuacao_SDOF_dB": band.attenuation_sdof_db,
            "Lmax_mitigado_dB": band.lmax_mitigated_db,
            "Limite_G_alvo_dB": band.target_g_limit_db,
            "Margem_dB": band.target_margin_db,
            "Curva_G": band.band_g_classification,
            "M": band.modal_overlap,
            "Correcao_contato_dB": band.contact_correction_db,
            "fc_contato_Hz": band.contact_cutoff_hz,
            "Lv_indicativo_dB": band.vibration_level_db,
            "Avisos": "; ".join(band.warnings),
        }
        for band in result.bands
    ]


def equivalent_cubic_room_project(
    *,
    impact_mass_kg: float = 35.0,
    drop_height_m: float = 1.0,
    volume_m3: float = 15.0,
    reverberation_time_s: float = 0.6,
    slab_thickness_m: float = 0.25,
    slab_density_kg_m3: float = 2300.0,
    young_modulus_pa: float = 30e9,
    poisson_ratio: float = 0.2,
    tc_original_ms: float = 3.0,
) -> ProjectInput:
    side = volume_m3 ** (1 / 3)
    return ProjectInput(
        impact_mass_kg=impact_mass_kg,
        drop_height_m=drop_height_m,
        room_width_m=side,
        room_length_m=side,
        room_height_m=side,
        reverberation_time_s=reverberation_time_s,
        slab_thickness_m=slab_thickness_m,
        slab_density_kg_m3=slab_density_kg_m3,
        young_modulus_pa=young_modulus_pa,
        poisson_ratio=poisson_ratio,
        tc_original_ms=tc_original_ms,
    )


def validate_h3_case() -> list[dict[str, float]]:
    targets = [
        {"tc_ms": 2.0, "fc_hz": 750.0, "expected_lamax_db": 90.0},
        {"tc_ms": 3.0, "fc_hz": 500.0, "expected_lamax_db": 90.0},
        {"tc_ms": 4.0, "fc_hz": 375.0, "expected_lamax_db": 87.0},
        {"tc_ms": 5.0, "fc_hz": 300.0, "expected_lamax_db": 86.0},
        {"tc_ms": 7.0, "fc_hz": 215.0, "expected_lamax_db": 84.0},
    ]
    rows = []
    for target in targets:
        project = equivalent_cubic_room_project(tc_original_ms=target["tc_ms"])
        spectrum = [
            sea_engine_lmax(freq, project, target["tc_ms"] / 1000.0)
            for freq in H3_VALIDATION_BANDS_HZ
        ]
        levels = [float(item["lmax_db"]) for item in spectrum]
        calculated = broadband_lamax_db(H3_VALIDATION_BANDS_HZ, levels, apply_a_weighting=True)
        rows.append(
            {
                "Tc_ms": target["tc_ms"],
                "fc_calculado_Hz": contact_cutoff_hz(target["tc_ms"] / 1000.0),
                "fc_esperado_Hz": target["fc_hz"],
                "LAmaxF_calculado_dB": calculated,
                "LAmaxF_esperado_dB": target["expected_lamax_db"],
                "Diferenca_dB": calculated - target["expected_lamax_db"],
            }
        )
    return rows
