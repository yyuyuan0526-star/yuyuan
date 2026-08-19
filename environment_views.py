from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

CLIMATE_DISPLAY = {
    "T2M": "平均气温（℃）",
    "RH2M": "相对湿度（%）",
    "PRECTOTCORR": "降水量（mm）",
}

FORECAST_DISPLAY = {
    "date": "日期",
    "tmax_c": "最高气温（℃）",
    "tmin_c": "最低气温（℃）",
    "precip_mm": "预计降水（mm）",
    "precip_prob_pct": "降水概率（%）",
    "et0_mm": "参考蒸散 ET₀（mm）",
    "solar_mj_m2": "太阳辐射（MJ/m²）",
    "wind_max_kmh": "最大风速（km/h）",
}


def apply_environment_extensions():
    st.markdown(r"""
<style>
.env-explain-card{margin-top:14px;background:#fff;border:1px solid #efd5d8;border-radius:18px;padding:16px 17px;box-shadow:0 8px 22px rgba(122,9,23,.06);}
.env-kicker{font-size:10px;letter-spacing:.12em;color:#b41425;font-weight:850;}
.env-title{font-size:19px;color:#7c0917;font-weight:900;margin:4px 0 10px;}
.env-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;}
.env-cell{background:#fff8f7;border:1px solid #f2dadd;border-radius:12px;padding:10px 11px;}
.env-cell .k{font-size:10px;color:#846e73;font-weight:700;}.env-cell .v{font-size:15px;color:#6e0915;font-weight:900;margin-top:3px;}
.env-pill{display:inline-block;padding:4px 8px;border-radius:999px;background:#fff0ef;color:#98101f;border:1px solid #f0d7d9;font-size:10px;font-weight:800;margin-right:5px;margin-top:6px;}
.ai-box{margin-top:10px;border-left:4px solid #b41425;background:linear-gradient(90deg,#fff7f6,#fff);border-radius:12px;padding:11px 12px;color:#4f373c;font-size:12px;line-height:1.75;}
.risk-row{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center;padding:7px 0;border-bottom:1px dashed #eed7da;font-size:12px;color:#5e484d;}.risk-row:last-child{border-bottom:none}.risk-level{font-weight:850;color:#98101f;}
.var-note{margin-top:10px;padding:10px 11px;border-radius:11px;background:#faf5f5;color:#776166;font-size:10px;line-height:1.75;}
</style>
""", unsafe_allow_html=True)


def translate_climate_chart(data):
    if not isinstance(data, pd.DataFrame):
        return data
    cols=set(map(str,data.columns))
    if {"T2M","RH2M","PRECTOTCORR"}.issubset(cols):
        return data.rename(columns=CLIMATE_DISPLAY)
    return data


def translate_forecast_table(data):
    if not isinstance(data, pd.DataFrame):
        return data
    cols=set(map(str,data.columns))
    if not {"date","tmax_c","tmin_c","precip_mm"}.issubset(cols):
        return data
    out=data.copy()
    if "date" in out.columns:
        try:
            out["date"]=pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
        except Exception:
            pass
    ordered=[c for c in FORECAST_DISPLAY if c in out.columns]
    extra=[c for c in out.columns if c not in ordered]
    return out[ordered+extra].rename(columns=FORECAST_DISPLAY)


def _soil_texture(clay: float, sand: float):
    if clay >= 40:
        return "黏重土", "较强", "较弱", "中等"
    if sand >= 60:
        return "砂质土", "较弱", "较强", "较高"
    if clay >= 30:
        return "黏壤质土", "中高", "中等", "较高"
    return "壤质土", "中等", "中等", "较高"


def _risk_level(value, medium, high):
    if value >= high:
        return "高"
    if value >= medium:
        return "中"
    return "低"


def render_soil_ai_panel(values: dict, forecast=None):
    clay=float(values.get("黏粒 %",30.0) or 30.0)
    sand=float(values.get("砂粒 %",35.0) or 35.0)
    silt=float(values.get("粉粒 %",35.0) or 35.0)
    ph=float(values.get("pH",6.2) or 6.2)
    soc=float(values.get("SOC / 有机碳 g/kg",22.0) or 22.0)
    moisture=float(values.get("当前根际含水率 %",28.0) or 28.0)
    texture,hold,drain,fit=_soil_texture(clay,sand)

    st.markdown(f"""
<div class="env-explain-card">
  <div class="env-kicker">SOIL INTERPRETATION</div>
  <div class="env-title">地块土壤画像</div>
  <div class="env-grid">
    <div class="env-cell"><div class="k">土壤质地判断</div><div class="v">{texture}</div></div>
    <div class="env-cell"><div class="k">水凝胶适配性</div><div class="v">{fit}</div></div>
    <div class="env-cell"><div class="k">天然保水能力</div><div class="v">{hold}</div></div>
    <div class="env-cell"><div class="k">排水通气能力</div><div class="v">{drain}</div></div>
  </div>
  <span class="env-pill">pH {ph:.2f}</span><span class="env-pill">SOC {soc:.1f} g/kg</span><span class="env-pill">根际含水率 {moisture:.1f}%</span>
  <div class="ai-box">模型解释：当前黏粒 {clay:.1f}%、砂粒 {sand:.1f}%、粉粒 {silt:.1f}%。水凝胶施量不能只追求“越多越保水”，还需要同时考虑土壤自身保水能力与根区通气安全边界。</div>
</div>
""", unsafe_allow_html=True)

    if isinstance(forecast,pd.DataFrame) and len(forecast):
        def num(col,how="sum",default=0.0):
            if col not in forecast.columns:
                return default
            s=pd.to_numeric(forecast[col],errors="coerce")
            return float(s.max() if how=="max" else s.sum()) if s.notna().any() else default
        max_t=num("tmax_c","max",np.nan)
        rain=num("precip_mm","sum",0.0)
        et0=num("et0_mm","sum",0.0)
        rain_prob=num("precip_prob_pct","max",0.0)
        deficit=et0-0.8*rain
        heat=_risk_level(max_t if np.isfinite(max_t) else 0,32,35)
        rainrisk=_risk_level(rain,20,40)
        drought="高" if deficit>12 and moisture<23 else ("中" if deficit>6 or moisture<25 else "低")
        oxygen="中" if (rain>=30 and clay>=30) else ("高" if rain>=50 and clay>=40 else "低")

        if rain >= 30:
            advice="未来降雨较集中，建议强降雨前减少或暂停灌溉；当前不建议仅为追求保水而继续提高水凝胶施用量，应优先关注根区排水与通气。"
        elif deficit > 10:
            advice="未来蒸散需求高于有效降水，建议采用小水分次灌溉，并结合模型处方发挥水凝胶的根区缓冲作用。"
        else:
            advice="未来7日水分供需总体较平衡，可维持常规监测，并根据土壤含水率变化动态修正灌溉。"

        st.markdown(f"""
<div class="env-explain-card">
  <div class="env-kicker">7-DAY AI DIAGNOSIS</div>
  <div class="env-title">未来7日环境诊断</div>
  <div class="risk-row"><span>最高气温</span><span class="risk-level">{max_t:.1f} ℃ · {heat}风险</span></div>
  <div class="risk-row"><span>累计预报降水</span><span class="risk-level">{rain:.1f} mm · {rainrisk}风险</span></div>
  <div class="risk-row"><span>最高降水概率</span><span class="risk-level">{rain_prob:.0f}%</span></div>
  <div class="risk-row"><span>水分亏缺指数（ET₀−0.8P）</span><span class="risk-level">{deficit:.1f} mm · 干旱{drought}</span></div>
  <div class="risk-row"><span>根区缺氧风险</span><span class="risk-level">{oxygen}</span></div>
  <div class="ai-box"><b>AI农艺建议：</b>{advice}</div>
  <div class="var-note">指标释义：平均气温 T2M＝2米气温；相对湿度 RH2M＝2米相对湿度；PRECTOTCORR＝校正降水量；ET₀＝参考蒸散量，用于表征大气蒸发需求。界面显示全部使用中文名称，英文缩写仅保留作数据来源追溯。</div>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div class="env-explain-card">
  <div class="env-kicker">7-DAY AI DIAGNOSIS</div>
  <div class="env-title">未来7日环境诊断</div>
  <div class="ai-box">点击左侧“获取未来7天天气”后，这里将自动生成高温、强降雨、水分亏缺与根区缺氧风险，并给出可解释的灌溉/水凝胶管理建议。</div>
  <div class="var-note">变量说明：T2M＝平均气温；RH2M＝相对湿度；PRECTOTCORR＝降水量；ET₀＝参考蒸散量。正式展示中表格与图例均转换为中文。</div>
</div>
""", unsafe_allow_html=True)
