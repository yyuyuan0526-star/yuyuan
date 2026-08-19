from __future__ import annotations
import streamlit as st


def apply_metric_card_fix():
    """Final CSS override for Streamlit metric cards.

    Keeps values and units inside narrow competition-dashboard cards without
    ellipsis or overflow. Loaded after the general theme so it wins the cascade.
    """
    st.markdown(
        r"""
<style>
/* Final metric-card typography override */
div[data-testid="stMetric"]{
    min-width:0 !important;
    min-height:104px !important;
    padding:12px 13px 13px !important;
    overflow:hidden !important;
}

div[data-testid="stMetricLabel"]{
    min-width:0 !important;
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
}

div[data-testid="stMetricValue"] > div,
div[data-testid="stMetricValue"] p,
div[data-testid="stMetricValue"] span{
    font-size:1.55rem !important;
    line-height:1.08 !important;
    letter-spacing:-0.025em !important;
    font-weight:900 !important;
    white-space:nowrap !important;
    overflow:visible !important;
    text-overflow:clip !important;
    max-width:none !important;
}

/* Typical 4-column laptop / competition projection widths */
@media (max-width: 1450px){
    div[data-testid="stMetricValue"] > div,
    div[data-testid="stMetricValue"] p,
    div[data-testid="stMetricValue"] span{
        font-size:1.42rem !important;
        letter-spacing:-0.035em !important;
    }
}

@media (max-width: 1250px){
    div[data-testid="stMetricValue"] > div,
    div[data-testid="stMetricValue"] p,
    div[data-testid="stMetricValue"] span{
        font-size:1.25rem !important;
        letter-spacing:-0.04em !important;
    }
    div[data-testid="stMetricLabel"] p{
        font-size:.86rem !important;
    }
}

@media (max-width: 980px){
    div[data-testid="stMetric"]{
        min-height:94px !important;
        padding:10px 11px !important;
    }
    div[data-testid="stMetricValue"] > div,
    div[data-testid="stMetricValue"] p,
    div[data-testid="stMetricValue"] span{
        font-size:1.12rem !important;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )
