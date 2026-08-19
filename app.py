from __future__ import annotations

import streamlit as st
from ui_style import apply_competition_theme, render_hero, render_system_flow

# UI wrapper: all validated V2 model/business logic stays in core_app.py.
_original_caption = st.caption
_caption_count = {"n": 0}


def _competition_title(*args, **kwargs):
    # core_app calls set_page_config before title, so CSS injection is safe here.
    apply_competition_theme()
    st.sidebar.markdown(
        """
<div class="sidebar-brand">
  <div class="sb-en">AGRIGEL DECISION ENGINE</div>
  <div class="sb-title">凝策 · 地块参数台</div>
  <div class="sb-note">先定义地块与番茄生育阶段，再由模型生成可执行的水凝胶处方与水肥管理方案。</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    render_hero()


def _competition_caption(body, *args, **kwargs):
    _caption_count["n"] += 1
    # Replace only the original top caption with the five-step competition workflow.
    if _caption_count["n"] == 1:
        render_system_flow()
        return None
    return _original_caption(body, *args, **kwargs)


st.title = _competition_title
st.caption = _competition_caption

# Execute the validated V2 application logic.
import core_app  # noqa: E402,F401
