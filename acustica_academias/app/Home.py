from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from impactosea import (  # noqa: E402
    FeasibilityInput,
    ProjectInput,
    assess_feasibility,
    build_ads_markdown,
    calculate_scenario,
    load_solutions,
)
from impactosea.constants import G_CURVES, IMPACT_BANDS_HZ, TARGET_G_OPTIONS  # noqa: E402
from impactosea.engine import scenario_to_records, validate_h3_case  # noqa: E402


st.set_page_config(
    page_title="ImpactoSEA-ProPG ADS",
    layout="wide",
    initial_sidebar_state="expanded",
)

alt.data_transformers.disable_max_rows()

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem;
            max-width: 1500px;
        }
        .small-note {
            color: #475569;
            font-size: 0.9rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def cached_solutions():
    return load_solutions()


@st.cache_data(show_spinner=False)
def cached_h3_validation() -> pd.DataFrame:
    return pd.DataFrame(validate_h3_case())


def _solution_label(solution) -> str:
    return f"{solution.name} ({solution.id})"


def build_g_curve_dataframe() -> pd.DataFrame:
    rows = []
    for g_value, curve in G_CURVES.items():
        for frequency, limit in curve.items():
            rows.append(
                {
                    "Freq_Hz": float(frequency),
                    "Nivel_dB": float(limit),
                    "Serie": f"G{g_value}",
                    "Tipo": "Curva G",
                }
            )
    return pd.DataFrame(rows)


def build_chart(result_df: pd.DataFrame, target_g: int) -> alt.Chart:
    curve_df = build_g_curve_dataframe()
    target_df = curve_df[curve_df["Serie"] == f"G{target_g}"].copy()

    spectra = pd.concat(
        [
            result_df[["Freq_Hz", "Lmax_original_dB"]]
            .rename(columns={"Lmax_original_dB": "Nivel_dB"})
            .assign(Serie="Original", Tipo="Predição"),
            result_df[["Freq_Hz", "Lmax_mitigado_dB"]]
            .rename(columns={"Lmax_mitigado_dB": "Nivel_dB"})
            .assign(Serie="Mitigado", Tipo="Predição"),
        ],
        ignore_index=True,
    )

    gray_curves = (
        alt.Chart(curve_df)
        .mark_line(color="#94A3B8", opacity=0.25, strokeDash=[4, 3])
        .encode(
            x=alt.X("Freq_Hz:Q", scale=alt.Scale(type="log"), title="Frequência [Hz]"),
            y=alt.Y("Nivel_dB:Q", title="Nível por banda [dB]"),
            detail="Serie:N",
        )
    )
    target_line = (
        alt.Chart(target_df)
        .mark_line(color="#2563EB", strokeWidth=2.5)
        .encode(
            x=alt.X("Freq_Hz:Q", scale=alt.Scale(type="log")),
            y="Nivel_dB:Q",
            tooltip=["Serie:N", "Freq_Hz:Q", "Nivel_dB:Q"],
        )
    )
    spectra_lines = (
        alt.Chart(spectra)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("Freq_Hz:Q", scale=alt.Scale(type="log")),
            y="Nivel_dB:Q",
            color=alt.Color(
                "Serie:N",
                scale=alt.Scale(domain=["Original", "Mitigado"], range=["#DC2626", "#16A34A"]),
                legend=alt.Legend(title="Série"),
            ),
            tooltip=[
                alt.Tooltip("Serie:N"),
                alt.Tooltip("Freq_Hz:Q", format=".1f"),
                alt.Tooltip("Nivel_dB:Q", format=".1f"),
            ],
        )
    )
    return (gray_curves + target_line + spectra_lines).properties(height=500)


solutions = cached_solutions()

st.title("ImpactoSEA-ProPG ADS")
st.caption(
    "Dimensionamento preliminar de ruído de impacto pesado em academias com predição SEA, "
    "mitigação SDOF, Curvas-G e Declaração de Design Acústico."
)

with st.sidebar:
    st.header("Critério")
    target_g = st.selectbox("Curva-G alvo", TARGET_G_OPTIONS, index=TARGET_G_OPTIONS.index(25))
    st.caption("Exemplo: G15-G25 para contextos residenciais, dependendo do período e do risco.")

    st.header("Solução")
    solution = st.selectbox(
        "Catálogo de mitigação",
        solutions,
        format_func=_solution_label,
        index=1 if len(solutions) > 1 else 0,
    )
    st.write(solution.summary)

tab_stage1, tab_stage2, tab_results, tab_ads, tab_validation = st.tabs(
    ["Estágio 1", "Estágio 2", "Resultados", "ADS", "Validação"]
)

with tab_stage1:
    st.subheader("Avaliação de Viabilidade")
    col_a, col_b = st.columns(2)
    with col_a:
        intended_use = st.text_input("Uso pretendido", "Academia com área de pesos livres")
        sensitive_receptor = st.text_input("Receptor sensível", "Dormitório residencial abaixo")
        activity_type = st.selectbox(
            "Atividade de referência",
            [
                "Pesos livres / halteres",
                "Treino funcional com impacto",
                "LPO / CrossFit extremo",
                "Impacto moderado",
            ],
        )
    with col_b:
        has_dry_concrete_slab = st.checkbox("Laje seca de concreto confirmada", value=True)
        flanking_risk = st.selectbox("Risco de flanqueamento", ["Baixo", "Médio", "Alto"], index=1)
        method1_recommended = st.checkbox("Recomendar ensaio de referência Método 1", value=True)
    feasibility_notes = st.text_area("Notas de viabilidade", "")

    feasibility = FeasibilityInput(
        intended_use=intended_use,
        sensitive_receptor=sensitive_receptor,
        activity_type=activity_type,
        has_dry_concrete_slab=has_dry_concrete_slab,
        flanking_risk=flanking_risk,
        method1_recommended=method1_recommended,
        notes=feasibility_notes,
    )
    assessment = assess_feasibility(feasibility)

    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("Risco preliminar", assessment.risk_level)
    metric_col2.metric("Score", assessment.score)
    st.info(assessment.recommendation)
    st.write("Fatores registrados:")
    for flag in assessment.flags:
        st.write(f"- {flag}")

with tab_stage2:
    st.subheader("Modelagem e Predição")
    st.markdown("#### Fonte de impacto")
    impact_col1, impact_col2, impact_col3 = st.columns(3)
    with impact_col1:
        impact_mass_kg = st.number_input("Massa [kg]", min_value=1.0, max_value=200.0, value=15.0, step=1.0)
    with impact_col2:
        drop_height_m = st.number_input("Altura de queda [m]", min_value=0.05, max_value=2.0, value=0.5, step=0.05)
    with impact_col3:
        tc_original_ms = st.number_input("Tc original [ms]", min_value=0.5, max_value=30.0, value=3.0, step=0.5)

    st.markdown("#### Sala receptora")
    room_col1, room_col2, room_col3, room_col4 = st.columns(4)
    with room_col1:
        room_width_m = st.number_input("Largura [m]", min_value=1.0, max_value=20.0, value=2.58, step=0.1)
    with room_col2:
        room_length_m = st.number_input("Comprimento [m]", min_value=1.0, max_value=20.0, value=2.62, step=0.1)
    with room_col3:
        room_height_m = st.number_input("Altura [m]", min_value=1.8, max_value=8.0, value=3.24, step=0.1)
    with room_col4:
        reverberation_time_s = st.number_input("T60 [s]", min_value=0.1, max_value=5.0, value=0.5, step=0.1)

    st.markdown("#### Laje seca de concreto")
    slab_col1, slab_col2, slab_col3, slab_col4 = st.columns(4)
    with slab_col1:
        slab_thickness_mm = st.number_input("Espessura [mm]", min_value=80.0, max_value=600.0, value=250.0, step=10.0)
    with slab_col2:
        slab_density_kg_m3 = st.number_input("Densidade [kg/m³]", min_value=1500.0, max_value=3000.0, value=2400.0, step=50.0)
    with slab_col3:
        young_modulus_gpa = st.number_input("Módulo de Young [GPa]", min_value=5.0, max_value=60.0, value=30.0, step=1.0)
    with slab_col4:
        poisson_ratio = st.number_input("Poisson", min_value=0.05, max_value=0.45, value=0.20, step=0.01)

    st.markdown("#### Parâmetros da solução selecionada")
    sol_col1, sol_col2, sol_col3, sol_col4 = st.columns(4)
    sol_col1.metric("Tc mitigado", f"{solution.tc_mitigated_ms:.1f} ms")
    sol_col2.metric("fn", f"{solution.fn_hz:.1f} Hz")
    sol_col3.metric("zeta", f"{solution.zeta:.2f}")
    sol_col4.metric("cap", f"{solution.cap_db:.1f} dB")
    with st.expander("Camadas da solução", expanded=False):
        for layer in solution.layers:
            st.write(f"- {layer.material}: {layer.thickness_mm:g} mm ({layer.role})")

project = ProjectInput(
    impact_mass_kg=impact_mass_kg,
    drop_height_m=drop_height_m,
    room_width_m=room_width_m,
    room_length_m=room_length_m,
    room_height_m=room_height_m,
    reverberation_time_s=reverberation_time_s,
    slab_thickness_m=slab_thickness_mm / 1000.0,
    slab_density_kg_m3=slab_density_kg_m3,
    young_modulus_pa=young_modulus_gpa * 1e9,
    poisson_ratio=poisson_ratio,
    tc_original_ms=tc_original_ms,
)
result = calculate_scenario(project, solution, target_g=target_g, bands_hz=IMPACT_BANDS_HZ)
result_df = pd.DataFrame(scenario_to_records(result))
ads = build_ads_markdown(feasibility, assessment, project, solution, result)

with tab_results:
    st.subheader("Resultados por Curvas-G")
    metric_cols = st.columns(5)
    metric_cols[0].metric("Classificação mitigada", result.overall_g_classification)
    metric_cols[1].metric("Alvo", f"G{result.target_g}")
    metric_cols[2].metric("Pior margem", f"{result.worst_margin_db:.1f} dB")
    metric_cols[3].metric("Redução global", f"{result.global_reduction_db:.1f} dB")
    metric_cols[4].metric("LFISPL mitigado", f"{result.lfispl_mitigated_db:.1f} dB")

    st.altair_chart(build_chart(result_df, target_g), width="stretch")
    st.caption(
        "Bandas acima de 2 kHz são mantidas para apresentação até 4 kHz, com aviso de menor confiança para a predição SEA."
    )

    display_df = result_df.copy()
    rounded_cols = [
        "Lmax_original_dB",
        "Lmax_contato_mitigado_dB",
        "Atenuacao_SDOF_dB",
        "Lmax_mitigado_dB",
        "Limite_G_alvo_dB",
        "Margem_dB",
        "M",
        "Correcao_contato_dB",
        "fc_contato_Hz",
        "Lv_indicativo_dB",
    ]
    display_df[rounded_cols] = display_df[rounded_cols].round(1)
    st.dataframe(display_df, hide_index=True, width="stretch")

    with st.expander("Incertezas consideradas", expanded=True):
        for note in result.uncertainty_notes:
            st.write(f"- {note}")

with tab_ads:
    st.subheader("Relatório / Declaração de Design Acústico")
    st.download_button(
        "Baixar ADS em Markdown",
        data=ads.markdown.encode("utf-8"),
        file_name="ADS_ImpactoSEA_ProPG.md",
        mime="text/markdown",
    )
    st.markdown(ads.markdown)

with tab_validation:
    st.subheader("Validação H.3 ProPG/GAG")
    validation_df = cached_h3_validation()
    st.dataframe(validation_df.round(1), hide_index=True, width="stretch")
    max_error = validation_df["Diferenca_dB"].abs().max()
    if max_error <= 6.0:
        st.success(f"Erro máximo absoluto: {max_error:.1f} dB (dentro de ±6 dB).")
    else:
        st.error(f"Erro máximo absoluto: {max_error:.1f} dB (fora de ±6 dB).")
