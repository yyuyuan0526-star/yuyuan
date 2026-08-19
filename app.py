from __future__ import annotations

import streamlit as st
import decision_support as _decision_support
from ui_style import apply_competition_theme, render_hero, render_system_flow
from competition_views import (
    apply_national_extensions,
    render_dual_base_overview,
    render_prescription_sheet,
    render_business_dashboard,
)

# -----------------------------------------------------------------------------
# National-competition UI wrapper.
# core_app.py retains the validated V2 model/business logic.
# -----------------------------------------------------------------------------
_original_caption = st.caption
_caption_count = {"n": 0}


def _competition_title(*args, **kwargs):
    # core_app calls set_page_config before st.title, so CSS injection is safe here.
    apply_competition_theme()
    apply_national_extensions()
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
    # Replace only the original top caption with the competition narrative layer.
    if _caption_count["n"] == 1:
        render_system_flow()
        render_dual_base_overview()
        return None
    return _original_caption(body, *args, **kwargs)


# -----------------------------------------------------------------------------
# Inject presentation views at the exact point where the validated business
# functions are called. This avoids changing the model/decision algorithms.
# -----------------------------------------------------------------------------
_original_prescription_execution = _decision_support.prescription_execution
_original_economic_scenario = _decision_support.economic_scenario


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


# Streamlit surface overrides.
st.title = _competition_title
st.caption = _competition_caption
_decision_support.prescription_execution = _competition_prescription_execution
_decision_support.economic_scenario = _competition_economic_scenario

# Execute the validated V2 application logic under the V3 competition UI layer.
import core_app  # noqa: E402,F401
