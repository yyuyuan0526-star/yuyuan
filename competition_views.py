from __future__ import annotations
from datetime import date
from html import escape
import math
import pandas as pd
import streamlit as st


def apply_national_extensions():
    st.markdown(r"""
<style>
.section-kicker{font-size:12px;font-weight:800;letter-spacing:.12em;color:#b41425;margin-bottom:6px;}
.section-title{font-size:24px;font-weight:900;color:#7c0917;margin:0 0 7px;}
.section-note{font-size:12px;color:#80676d;line-height:1.7;margin-bottom:12px;}

.base-stage{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0 14px;}
.base-card{position:relative;overflow:hidden;background:#fff;border:1px solid #f0d7d9;border-radius:19px;padding:18px 18px 16px;box-shadow:0 8px 24px rgba(122,9,23,.06);}
.base-card:before{content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:linear-gradient(#7c0917,#d32334);}
.base-label{display:inline-block;padding:5px 9px;border-radius:999px;background:#fff0ef;color:#98101f;font-size:11px;font-weight:800;}
.base-name{font-size:21px;color:#5f0712;font-weight:900;margin:8px 0 3px;}
.base-role{font-size:13px;font-weight:800;color:#b41425;}
.base-desc{font-size:12px;color:#745f64;line-height:1.7;margin-top:8px;}
.base-meta{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px;}
.base-meta span{font-size:10px;color:#80676d;background:#fff8f7;border:1px solid #f0d7d9;border-radius:8px;padding:5px 7px;}

.prescription-sheet{background:#fff;border:1px solid #e9c7cb;border-radius:24px;overflow:hidden;box-shadow:0 14px 34px rgba(122,9,23,.10);margin:14px 0 18px;}
.rx-head{display:flex;justify-content:space-between;align-items:flex-start;gap:15px;padding:20px 22px;background:linear-gradient(125deg,#690813,#96101f 55%,#c91b2d);color:#fff;}
.rx-kicker{font-size:11px;letter-spacing:.12em;font-weight:800;color:#ffe0a0;}
.rx-title{font-size:24px;font-weight:900;margin-top:3px;}
.rx-sub{font-size:12px;color:rgba(255,255,255,.78);margin-top:5px;}
.rx-status{font-size:11px;font-weight:800;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.10);padding:7px 10px;border-radius:999px;white-space:nowrap;}
.rx-body{padding:18px 22px 20px;}
.rx-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}
.rx-item{background:#fff9f8;border:1px solid #f2dadd;border-radius:14px;padding:12px 13px;}
.rx-item .k{font-size:10px;color:#8b7479;font-weight:700;}
.rx-item .v{font-size:16px;color:#6c0915;font-weight:900;margin-top:4px;word-break:break-word;}
.rx-wide{grid-column:span 2;}
.rx-operation{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;}
.rx-op{border-left:4px solid #b41425;background:#fff;border-radius:12px;padding:11px 13px;border-top:1px solid #f2dadd;border-right:1px solid #f2dadd;border-bottom:1px solid #f2dadd;}
.rx-op .k{font-size:10px;color:#8b7479;font-weight:700;}.rx-op .v{font-size:13px;color:#3d272c;font-weight:750;margin-top:4px;line-height:1.65;}
.rx-outcomes{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-top:12px;}
.rx-outcome{background:linear-gradient(180deg,#fff,#fff6f5);border:1px solid #f0d7d9;border-radius:13px;padding:10px 12px;text-align:center;}
.rx-outcome .k{font-size:10px;color:#80676d;}.rx-outcome .v{font-size:18px;color:#98101f;font-weight:900;margin-top:2px;}
.rx-foot{font-size:10px;color:#8a7478;border-top:1px dashed #ecd2d5;margin-top:13px;padding-top:10px;line-height:1.6;}

.biz-panel{margin:12px 0 16px;padding:18px;border-radius:22px;background:linear-gradient(135deg,#6c0814,#9f1222 60%,#cb2031);color:white;box-shadow:0 15px 38px rgba(122,9,23,.19);}
.biz-top{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;margin-bottom:14px;}
.biz-kicker{font-size:11px;letter-spacing:.12em;color:#ffe0a0;font-weight:800;}.biz-title{font-size:22px;font-weight:900;margin-top:3px;}.biz-note{font-size:11px;color:rgba(255,255,255,.72);max-width:720px;line-height:1.6;}
.biz-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}
.biz-kpi{background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.14);border-radius:16px;padding:14px;}
.biz-kpi .k{font-size:11px;color:rgba(255,255,255,.72);font-weight:700;}.biz-kpi .v{font-size:27px;font-weight:900;margin-top:5px;}.biz-kpi .s{font-size:10px;color:#ffe0a0;margin-top:5px;}
.value-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-top:11px;}
.value-mini{background:#fff;border:1px solid #efd5d8;border-radius:14px;padding:12px 13px;box-shadow:0 7px 18px rgba(122,9,23,.045);}.value-mini .k{font-size:10px;color:#80676d;}.value-mini .v{font-size:18px;color:#7c0917;font-weight:900;margin-top:4px;}
.compare-wrap{margin-top:12px;background:#fff;border:1px solid #efd5d8;border-radius:16px;padding:14px 15px;}
.compare-title{font-size:12px;font-weight:850;color:#7c0917;margin-bottom:9px;}.bar-row{display:grid;grid-template-columns:92px 1fr 92px;gap:9px;align-items:center;margin:8px 0;}.bar-name{font-size:11px;color:#6d575c;font-weight:700;}.bar-track{height:11px;background:#faecee;border-radius:999px;overflow:hidden;}.bar-fill-base{height:100%;background:#d8c3c6;border-radius:999px;}.bar-fill-ai{height:100%;background:linear-gradient(90deg,#98101f,#d32334);border-radius:999px;}.bar-val{text-align:right;font-size:11px;font-weight:850;color:#7c0917;}

@media(max-width:900px){.base-stage,.rx-operation{grid-template-columns:1fr}.rx-grid,.rx-outcomes,.biz-grid,.value-strip{grid-template-columns:1fr 1fr}.rx-wide{grid-column:span 1}}
</style>
""", unsafe_allow_html=True)


def render_dual_base_overview():
    st.markdown('<div class="section-kicker">DOUBLE-SITE VALIDATION</div><div class="section-title">靖安 × 玉山｜双环境番茄验证场景</div><div class="section-note">先用两个真实区域建立“环境—配方—田间结果”的差异学习，再逐步扩展到更多地区与作物。县域坐标仅用于界面展示，正式模型以试验地GPS为准。</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="base-stage">
  <div class="base-card">
    <span class="base-label">JING'AN · SITE A</span>
    <div class="base-name">江西 · 靖安</div>
    <div class="base-role">番茄首轮田间验证场景</div>
    <div class="base-desc">用于连接配方筛选、根际水分/养分表现与田间反馈，形成“问题反哺—材料再研发”的第一条闭环。</div>
    <div class="base-meta"><span>环境差异输入</span><span>番茄首证</span><span>田间反馈迭代</span></div>
  </div>
  <div class="base-card">
    <span class="base-label">YUSHAN · SITE B</span>
    <div class="base-name">江西 · 玉山</div>
    <div class="base-role">第二环境适配验证场景</div>
    <div class="base-desc">用于检验同一水凝胶技术底座在不同气候、土壤与水分背景下的配方响应差异，为“因地配胶”积累跨区域数据。</div>
    <div class="base-meta"><span>跨区域适配</span><span>环境×配方交互</span><span>模型迁移基础</span></div>
  </div>
</div>
""", unsafe_allow_html=True)
    base_df = pd.DataFrame({"lat":[28.9500,28.67677],"lon":[115.2300,118.24162]})
    try:
        st.map(base_df, latitude="lat", longitude="lon", zoom=7, use_container_width=True, height=280)
    except TypeError:
        st.map(base_df)


def _fmt(x, digits=2, suffix=""):
    try:
        return f"{float(x):.{digits}f}{suffix}"
    except Exception:
        return "—"


def render_prescription_sheet(formula: dict, execution: dict, result: dict | None, growth_stage: str, is_demo: bool=False):
    preds=(result or {}).get("predictions",{})
    site=escape(str(formula.get("site","—")))
    crop=escape(str(formula.get("crop","番茄")))
    module=escape(str(formula.get("function_module","—")))
    additive=escape(str(formula.get("additive_type","—")))
    rxid=f"AG-{site}-{date.today().strftime('%m%d')}"
    status="演示数据 · 不可直接农用" if is_demo else "模型推荐 · 待田间校准"
    water=_fmt(preds.get("water_retention_21d_pct"),1,"%")
    nutrient=_fmt(preds.get("nutrient_retention_21d_pct"),1,"%")
    yld=_fmt(preds.get("yield_gain_pct"),1,"%")
    brix=_fmt(preds.get("brix_gain"),2," °Brix")
    st.markdown(f"""
<div class="prescription-sheet">
  <div class="rx-head">
    <div><div class="rx-kicker">AGRIGEL AGRONOMIC PRESCRIPTION · {escape(rxid)}</div><div class="rx-title">凝策水凝胶农艺处方单</div><div class="rx-sub">一地一方 · 一作一策｜把模型结果直接转化为可执行田间方案</div></div>
    <div class="rx-status">{escape(status)}</div>
  </div>
  <div class="rx-body">
    <div class="rx-grid">
      <div class="rx-item"><div class="k">地块场景</div><div class="v">{site}</div></div>
      <div class="rx-item"><div class="k">作物 / 生育期</div><div class="v">{crop} · {escape(str(growth_stage))}</div></div>
      <div class="rx-item"><div class="k">功能模块</div><div class="v">{module}</div></div>
      <div class="rx-item"><div class="k">推荐亩用量</div><div class="v">{_fmt(execution.get('kg_mu'),2,' kg/亩')}</div></div>
      <div class="rx-item"><div class="k">SA</div><div class="v">{_fmt(formula.get('sa_pct'),2,'%')}</div></div>
      <div class="rx-item"><div class="k">CS</div><div class="v">{_fmt(formula.get('cs_pct'),2,'%')}</div></div>
      <div class="rx-item"><div class="k">交联剂</div><div class="v">{_fmt(formula.get('glutaraldehyde_pct'),3,'%')}</div></div>
      <div class="rx-item"><div class="k">添加剂</div><div class="v">{additive} {_fmt(formula.get('additive_pct'),2,'%')}</div></div>
      <div class="rx-item"><div class="k">折算单株</div><div class="v">{_fmt(execution.get('g_plant'),2,' g/株')}</div></div>
      <div class="rx-item"><div class="k">折算公顷</div><div class="v">{_fmt(execution.get('kg_ha'),1,' kg/ha')}</div></div>
      <div class="rx-item rx-wide"><div class="k">处方定位</div><div class="v">环境驱动 + 多目标平衡</div></div>
    </div>
    <div class="rx-operation">
      <div class="rx-op"><div class="k">推荐施用深度</div><div class="v">{escape(str(execution.get('depth','—')))}</div></div>
      <div class="rx-op"><div class="k">推荐施用方式</div><div class="v">{escape(str(execution.get('method','—')))}</div></div>
    </div>
    <div class="rx-outcomes">
      <div class="rx-outcome"><div class="k">控水预测</div><div class="v">{water}</div></div>
      <div class="rx-outcome"><div class="k">控肥预测</div><div class="v">{nutrient}</div></div>
      <div class="rx-outcome"><div class="k">产量变化</div><div class="v">{yld}</div></div>
      <div class="rx-outcome"><div class="k">糖度变化</div><div class="v">{brix}</div></div>
    </div>
    <div class="rx-foot">科研边界：当前处方由模型计算生成；若训练集仍为合成演示数据，则仅用于软件流程展示。正式生产必须由靖安、玉山及后续田间实测数据持续校准，并设置根区通气、土壤盐分和施用量安全边界。</div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_business_dashboard(econ: dict, result: dict, baseline_yield: float):
    preds=result.get("predictions",{})
    predicted=float(econ.get("predicted_yield_kg_mu",baseline_yield))
    base=max(float(baseline_yield),1.0)
    ai_pct=min(100.0, 100.0*predicted/max(predicted,base))
    base_pct=min(100.0, 100.0*base/max(predicted,base))
    roi=econ.get("roi",float('nan'))
    roi_text="—" if not isinstance(roi,(int,float)) or not math.isfinite(roi) else f"{roi:.2f}"
    net=float(econ.get("net_gain_yuan_mu",0.0))
    gain=float(econ.get("yield_gain_pct",preds.get("yield_gain_pct",0.0)))
    st.markdown(f"""
<div class="biz-panel">
  <div class="biz-top"><div><div class="biz-kicker">COMPETITION VALUE DASHBOARD</div><div class="biz-title">技术价值 → 农户收益｜一亩地经济账</div></div><div class="biz-note">以下为当前参数与模型输出形成的情景测算，不等同于已经实现的田间收益；真实路演数据应由投入、售价、节水、节肥和产量实测共同支撑。</div></div>
  <div class="biz-grid">
    <div class="biz-kpi"><div class="k">预计亩产</div><div class="v">{predicted:,.0f}</div><div class="s">kg/亩 · 预测变化 {gain:+.1f}%</div></div>
    <div class="biz-kpi"><div class="k">7日节水潜力</div><div class="v">{float(econ.get('irrigation_saved_mm_7d',0.0)):.1f}</div><div class="s">mm · 来自灌溉联动情景</div></div>
    <div class="biz-kpi"><div class="k">预计净增益</div><div class="v">{net:,.0f}</div><div class="s">元/亩 · 情景值</div></div>
    <div class="biz-kpi"><div class="k">投入产出 ROI</div><div class="v">{roi_text}</div><div class="s">净增益 / 水凝胶投入</div></div>
  </div>
</div>
<div class="value-strip">
  <div class="value-mini"><div class="k">新增产值</div><div class="v">¥ {float(econ.get('added_revenue_yuan_mu',0.0)):,.0f}</div></div>
  <div class="value-mini"><div class="k">节水成本收益</div><div class="v">¥ {float(econ.get('irrigation_saved_cost_yuan_mu',0.0)):,.0f}</div></div>
  <div class="value-mini"><div class="k">肥料节省情景</div><div class="v">¥ {float(econ.get('fertilizer_saved_cost_yuan_mu',0.0)):,.0f}</div></div>
  <div class="value-mini"><div class="k">水凝胶材料成本</div><div class="v">¥ {float(econ.get('gel_cost_yuan_mu',0.0)):,.0f}</div></div>
</div>
<div class="compare-wrap">
  <div class="compare-title">亩产情景对照｜常规基线 vs AI推荐处方</div>
  <div class="bar-row"><div class="bar-name">常规基线</div><div class="bar-track"><div class="bar-fill-base" style="width:{base_pct:.1f}%"></div></div><div class="bar-val">{base:,.0f} kg</div></div>
  <div class="bar-row"><div class="bar-name">AI推荐</div><div class="bar-track"><div class="bar-fill-ai" style="width:{ai_pct:.1f}%"></div></div><div class="bar-val">{predicted:,.0f} kg</div></div>
</div>
""", unsafe_allow_html=True)
    st.caption("未加入“固定比例水凝胶”第三条对照，是因为当前系统没有独立的固定比例对照预测/实测标签；补齐对应田间对照后再展示三方案比较，避免人为制造数据。")
