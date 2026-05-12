"""Stage 1 feasibility assessment helpers."""

from __future__ import annotations

from .models import FeasibilityAssessment, FeasibilityInput


def assess_feasibility(input_data: FeasibilityInput) -> FeasibilityAssessment:
    score = 0
    flags: list[str] = []

    receptor = input_data.sensitive_receptor.lower()
    if any(token in receptor for token in ("resid", "dorm", "bedroom", "quarto")):
        score += 2
        flags.append("Receptor residencial/dormitório aumenta a sensibilidade.")
    elif any(token in receptor for token in ("escrit", "office", "saúde", "hospital")):
        score += 1
        flags.append("Receptor com exigência moderada de controle acústico.")

    activity = input_data.activity_type.lower()
    if any(token in activity for token in ("cross", "lpo", "olímp", "150", "extremo")):
        score += 3
        flags.append("Atividade extrema deve ser evitada ou proibida em muitos edifícios.")
    elif any(token in activity for token in ("peso", "halter", "free", "funcional", "impacto")):
        score += 2
        flags.append("Atividade de impacto pesado requer mitigação robusta.")

    if not input_data.has_dry_concrete_slab:
        score += 1
        flags.append("Base estrutural não confirmada como laje seca de concreto.")

    flanking = input_data.flanking_risk.lower()
    if "alto" in flanking or "high" in flanking:
        score += 2
        flags.append("Risco alto de flanqueamento deve ser investigado em campo.")
    elif "médio" in flanking or "medio" in flanking or "medium" in flanking:
        score += 1
        flags.append("Risco médio de flanqueamento exige ressalva no ADS.")

    if input_data.method1_recommended:
        flags.append("Recomendar ensaio de referência Método 1 antes da decisão final.")
    else:
        score += 1
        flags.append("Sem recomendação de Método 1, a decisão fica menos rastreável.")

    if score <= 2:
        risk_level = "Baixo"
        recommendation = "Prosseguir para predição preliminar com validação posterior."
    elif score <= 5:
        risk_level = "Médio"
        recommendation = "Prosseguir com cautela e prever ensaio de referência antes da especificação final."
    else:
        risk_level = "Alto"
        recommendation = "Tratar como viabilidade condicionada; ensaio de referência e revisão estrutural são necessários."

    return FeasibilityAssessment(
        risk_level=risk_level,
        score=score,
        recommendation=recommendation,
        flags=tuple(flags),
    )
