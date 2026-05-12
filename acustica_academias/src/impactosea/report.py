"""ADS report generation."""

from __future__ import annotations

from datetime import date

from .models import (
    ADSReport,
    FeasibilityAssessment,
    FeasibilityInput,
    MitigationSolution,
    ProjectInput,
    ScenarioResult,
)


def _fmt(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header_row = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_row, separator, *body])


def build_ads_markdown(
    feasibility: FeasibilityInput,
    assessment: FeasibilityAssessment,
    project: ProjectInput,
    solution: MitigationSolution,
    result: ScenarioResult,
) -> ADSReport:
    table_md = _markdown_table(
        [
            "Freq_Hz",
            "Lmax_original_dB",
            "Atenuacao_SDOF_dB",
            "Lmax_mitigado_dB",
            "Limite_G_alvo_dB",
            "Margem_dB",
            "Curva_G",
            "Avisos",
        ],
        [
            [
                _fmt(band.frequency_hz, 1),
                _fmt(band.lmax_original_db, 1),
                _fmt(band.attenuation_sdof_db, 1),
                _fmt(band.lmax_mitigated_db, 1),
                _fmt(band.target_g_limit_db, 1),
                _fmt(band.target_margin_db, 1),
                band.band_g_classification,
                "; ".join(band.warnings) if band.warnings else "-",
            ]
            for band in result.bands
        ],
    )

    layers = "\n".join(
        f"- {layer.material}: {layer.thickness_mm:g} mm ({layer.role})"
        for layer in solution.layers
    )
    flags = "\n".join(f"- {flag}" for flag in assessment.flags)
    uncertainties = "\n".join(f"- {note}" for note in result.uncertainty_notes)
    critical = (
        ", ".join(f"{freq:g} Hz" for freq in result.critical_bands_hz)
        if result.critical_bands_hz
        else "Nenhuma banda acima do alvo selecionado."
    )

    markdown = f"""# Declaração de Design Acústico (ADS) - ImpactoSEA-ProPG

Data: {date.today().isoformat()}

## 1. Avaliação de Viabilidade - Estágio 1

- Uso pretendido: {feasibility.intended_use}
- Receptor sensível: {feasibility.sensitive_receptor}
- Atividade avaliada: {feasibility.activity_type}
- Laje seca de concreto confirmada: {"sim" if feasibility.has_dry_concrete_slab else "não"}
- Risco de flanqueamento: {feasibility.flanking_risk}
- Método 1 recomendado: {"sim" if feasibility.method1_recommended else "não"}
- Classificação preliminar: {assessment.risk_level} (score {assessment.score})
- Recomendação: {assessment.recommendation}

{flags}

## 2. Modelagem e Predição - Estágio 2

- Massa de impacto: {_fmt(project.impact_mass_kg)} kg
- Altura de queda: {_fmt(project.drop_height_m, 2)} m
- Sala receptora: {_fmt(project.room_width_m, 2)} x {_fmt(project.room_length_m, 2)} x {_fmt(project.room_height_m, 2)} m
- Volume receptor: {_fmt(project.room_volume_m3, 2)} m³
- T60 adotado: {_fmt(project.reverberation_time_s, 2)} s
- Laje seca de concreto: {_fmt(project.slab_thickness_m * 1000, 0)} mm
- Densidade da laje: {_fmt(project.slab_density_kg_m3, 0)} kg/m³
- Módulo de Young: {_fmt(project.young_modulus_pa / 1e9, 1)} GPa
- Poisson: {_fmt(project.poisson_ratio, 2)}
- Tc original: {_fmt(project.tc_original_ms, 2)} ms

## 3. Especificação da Mitigação

Solução selecionada: {solution.name}

{solution.summary}

{layers}

- Tc mitigado adotado: {_fmt(solution.tc_mitigated_ms, 2)} ms
- Frequência natural SDOF: {_fmt(solution.fn_hz, 1)} Hz
- Amortecimento: {_fmt(solution.zeta, 2)}
- Cap de atenuação: {_fmt(solution.cap_db, 1)} dB
- Fonte/premissa: {solution.source}
- Validade: {solution.validity}

## 4. Resultados e Critério-Alvo

- Critério-alvo: G{result.target_g}
- Classificação G prevista do espectro mitigado: {result.overall_g_classification}
- Pior margem contra G{result.target_g}: {_fmt(result.worst_margin_db)} dB em {_fmt(result.worst_margin_frequency_hz, 1)} Hz
- Bandas críticas: {critical}
- Soma log Lmax original: {_fmt(result.global_lmax_original_db)} dB
- Soma log Lmax mitigado: {_fmt(result.global_lmax_mitigated_db)} dB
- Redução global estimada: {_fmt(result.global_reduction_db)} dB
- LFISPL 50+63+80 Hz original: {_fmt(result.lfispl_original_db)} dB
- LFISPL 50+63+80 Hz mitigado: {_fmt(result.lfispl_mitigated_db)} dB
- LIR original: {_fmt(result.lir_original)}
- LIR mitigado: {_fmt(result.lir_mitigated)}

{table_md}

## 5. Análise de Incerteza

{uncertainties}

## 6. Limitações

- Este ADS é uma ferramenta de projeto preliminar e não substitui ensaio de campo nem laudo final.
- A V1 calcula apenas impacto pesado; ruído aéreo/música deve ser avaliado em módulo próprio até 8 kHz quando aplicável.
- A classificação G usa 31,5 Hz a 4 kHz. Medição até 20 Hz é recomendada para diagnóstico de baixa frequência fora da classificação G.
"""
    return ADSReport(markdown=markdown)
