from __future__ import annotations

from pathlib import Path
import runpy
import streamlit as st
import decision_support as _decision_support
from ui_style import apply_competition_theme, render_hero, render_system_flow
from competition_views import (
    apply_national_extensions,
    render_dual_base_overview,
    render_prescription_sheet,
    render_business_dashboard,
)
from environment_views import (
    apply_environment_extensions,
    translate_climate_chart,
    translate_forecast_table,
    render_soil_ai_panel,
)

# -----------------------------------------------------------------------------
# National-competition UI wrapper.
# core_app.py retains the validated V2 model/business logic.
# This wrapper is intentionally reversible so Streamlit reruns stay stable.
# -----------------------------------------------------------------------------
_original_title = st.title
_original_caption = st.caption
_original_line_chart = st.line_chart
_original_dataframe = st.dataframe
_original_number_input = st.number_input
_original_prescription_execution = getattr(
    _decision_support,
    "_agrigel_original_prescription_execution",
    _decision_support.prescription_execution,
)
_original_economic_scenario = getattr(
    _decision_support,
    "_agrigel_original_economic_scenario",
    _decision_support.economic_scenario,
)
_decision_support._agrigel_original_prescription_execution = _original_prescription_execution
_decision_support._agrigel_original_economic_scenario = _original_economic_scenario
_caption_count = {"n": 0}
_widget_values = {}


def _apply_metric_overflow_fix():
    """Keep KPI values and units fully inside their competition-dashboard cards."""
    st.markdown(
        r"""
<style>
/* Metric cards: compact typography, full value + unit, no overlap. */
div[data-testid="stMetric"]{
  min-width:0 !important;
  min-height:104px !important;
  padding:12px 13px 13px !important;
  overflow:hidden !important;
}

div[data-testid="stMetricLabel"]{
  overflow:visible !important;
  margin-bottom:4px !important;
}
div[data-testid="stMetricLabel"] p{
  font-size:.95rem !important;
  line-height:1.2 !important;
  white-space:nowrap !important;
  overflow:visible !important;
  text-overflow:clip !important;
}

div[data-testid="stMetricValue"]{
  width:100% !important;
  min-width:0 !important;
  max-width:100% !important;
  overflow:hidden !important;
  text-overflow:clip !important;
  white-space:nowrap !important;
}
div[data-testid="stMetricValue"] *{
  max-width:none !important;
  overflow:visible !important;
  text-overflow:clip !important;
  white-space:nowrap !important;
  font-size:1.38rem !important;
  line-height:1.08 !important;
  letter-spacing:-0.035em !important;
  font-weight:900 !important;
}

/* Laptop / projection widths used in competition presentation. */
@media (max-width:1450px){
  div[data-testid="stMetricValue"] *{
    font-size:1.28rem !important;
    letter-spacing:-0.04em !important;
  }
}
@media (max-width:1250px){
  div[data-testid="stMetric"]{padding:11px 11px 12px !important;min-height:98px !important;}
  div[data-testid="stMetricLabel"] p{font-size:.86rem !important;}
  div[data-testid="stMetricValue"] *{font-size:1.16rem !important;}
}
@media (max-width:980px){
  div[data-testid="stMetricValue"] *{font-size:1.05rem !important;}
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _competition_title(*args, **kwargs):
    # core_app calls set_page_config before st.title, so CSS injection is safe here.
    apply_competition_theme()
    apply_national_extensions()
    apply_environment_extensions()
    _apply_metric_overflow_fix()
    st.sidebar.markdown(
        """
<div class="sidebar-brand">
  <div class="sb-en">AGRIGEL DECISION ENGINE</div>
  <div class="sb-title">凝策 · 地块参数台</div>
  <div class="sb-note">国赛 V3｜先定义地块与番茄生育阶段，再由模型生成可执行水凝胶处方、水肥管理与收益情景。</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    render_hero()


def _competition_caption(body, *args, **kwargs):
    _caption_count["n"] += 1
    if _caption_count["n"] == 1:
        render_system_flow()
        render_dual_base_overview()
        return None
    return _original_caption(body, *args, **kwargs)


def _competition_line_chart(data=None, *args, **kwargs):
    # Keep raw NASA field names inside the data/model; localize only the visible chart.
    return _original_line_chart(translate_climate_chart(data), *args, **kwargs)


def _competition_dataframe(data=None, *args, **kwargs):
    # Localize the Open-Meteo forecast table without changing session_state/raw data.
    return _original_dataframe(translate_forecast_table(data), *args, **kwargs)


def _competition_number_input(label, *args, **kwargs):
    value = _original_number_input(label, *args, **kwargs)
    _widget_values[str(label)] = value
    # The last soil-texture input is the natural anchor for the explainability panel.
    # It is rendered inside the right-hand soil column, using otherwise empty space.
    if str(label).strip() == "粉粒 %":
        render_soil_ai_panel(
            values=_widget_values,
            forecast=st.session_state.get("forecast"),
        )
    return value


def _competition_prescription_execution(formula, planting_density_per_mu, growth_stage, soil_clay_pct):
    execution = _original_prescription_execution(
        formula, planting_density_per_mu, growth_stage, soil_clay_pct
    )
    render_prescription_sheet(
        formula=formula,
        execution=execution,
        result=st.session_state.get("result"),
        growth_stage=growth_stage,
        is_demo=bool(st.session_state.get("demo_loaded", False)),
    )
    return execution


def _competition_economic_scenario(*args, **kwargs):
    econ = _original_economic_scenario(*args, **kwargs)
    result = args[0] if len(args) > 0 else kwargs.get("result", st.session_state.get("result", {}))
    baseline_yield = args[2] if len(args) > 2 else kwargs.get("baseline_yield_kg_mu", 0.0)
    render_business_dashboard(econ=econ, result=result or {}, baseline_yield=baseline_yield)
    return econ


# Activate the competition presentation/explainability layer for this rerun only.
st.title = _competition_title
st.caption = _competition_caption
st.line_chart = _competition_line_chart
st.dataframe = _competition_dataframe
st.number_input = _competition_number_input
_decision_support.prescription_execution = _competition_prescription_execution
_decision_support.economic_scenario = _competition_economic_scenario

try:
    # run_path guarantees core_app executes on every Streamlit rerun.
    runpy.run_path(str(Path(__file__).with_name("core_app.py")), run_name="__main__")
finally:
    # Restore global functions to prevent wrapper stacking on future reruns.
    st.title = _original_title
    st.caption = _original_caption
    st.line_chart = _original_line_chart
    st.dataframe = _original_dataframe
    st.number_input = _original_number_input
    _decision_support.prescription_execution = _original_prescription_execution
    _decision_support.economic_scenario = _original_economic_scenario
