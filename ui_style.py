from __future__ import annotations
import streamlit as st


def apply_competition_theme():
    st.markdown(
        r"""
<style>
:root{
  --red-950:#5f0712;
  --red-900:#7c0917;
  --red-800:#98101f;
  --red-700:#b41425;
  --red-600:#c91b2d;
  --red-100:#fde8e8;
  --red-50:#fff5f4;
  --gold:#d8aa43;
  --ink:#25171a;
  --muted:#745f64;
  --line:#f0d7d9;
  --paper:#fffdfc;
}

html, body, [class*="css"]{
  font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC","Segoe UI",sans-serif;
}

.stApp{
  background:
    radial-gradient(circle at 8% 0%, rgba(201,27,45,.07), transparent 28rem),
    linear-gradient(180deg,#fffafa 0%,#fffdfc 32%,#ffffff 100%);
  color:var(--ink);
}

.block-container{
  max-width:1480px;
  padding-top:1.25rem;
  padding-bottom:3rem;
}

#MainMenu, footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}

/* Hero */
.agrigel-hero{
  position:relative;
  overflow:hidden;
  border-radius:28px;
  padding:34px 38px 30px;
  margin:2px 0 18px;
  color:#fff;
  background:
    radial-gradient(circle at 88% 20%, rgba(255,255,255,.16), transparent 14rem),
    linear-gradient(125deg,var(--red-950) 0%,var(--red-800) 45%,#d32334 100%);
  box-shadow:0 18px 46px rgba(122,9,23,.20);
  border:1px solid rgba(255,255,255,.16);
}
.agrigel-hero:after{
  content:"";
  position:absolute;
  right:-80px; bottom:-130px;
  width:360px; height:360px;
  border:42px solid rgba(255,255,255,.055);
  border-radius:50%;
}
.hero-kicker{
  display:inline-flex;
  align-items:center;
  gap:8px;
  font-size:13px;
  font-weight:700;
  letter-spacing:.08em;
  background:rgba(255,255,255,.12);
  border:1px solid rgba(255,255,255,.18);
  padding:7px 12px;
  border-radius:999px;
  margin-bottom:14px;
}
.hero-title{
  font-size:42px;
  line-height:1.08;
  font-weight:900;
  letter-spacing:-.02em;
  margin:0;
}
.hero-title span{
  color:#ffe6a3;
  font-weight:800;
}
.hero-subtitle{
  font-size:20px;
  font-weight:700;
  margin-top:10px;
}
.hero-desc{
  max-width:980px;
  margin-top:10px;
  color:rgba(255,255,255,.88);
  font-size:14px;
  line-height:1.8;
}
.hero-tags{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top:18px;
}
.hero-tag{
  padding:7px 11px;
  border-radius:10px;
  background:rgba(255,255,255,.11);
  border:1px solid rgba(255,255,255,.15);
  color:#fff;
  font-size:12px;
  font-weight:700;
}

/* Five-step competition flow */
.flow-wrap{
  display:grid;
  grid-template-columns:repeat(5,1fr);
  gap:10px;
  margin:4px 0 20px;
}
.flow-item{
  background:rgba(255,255,255,.94);
  border:1px solid var(--line);
  border-radius:17px;
  padding:13px 14px;
  box-shadow:0 8px 24px rgba(122,9,23,.055);
  min-height:74px;
}
.flow-no{
  width:28px;height:28px;border-radius:9px;
  display:inline-flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,var(--red-800),var(--red-600));
  color:white;font-weight:900;font-size:12px;
  box-shadow:0 5px 13px rgba(180,20,37,.18);
}
.flow-title{font-weight:800;color:var(--red-900);font-size:14px;margin-left:7px;}
.flow-desc{color:var(--muted);font-size:11px;margin-top:8px;line-height:1.4;}

/* Sidebar */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#760b19 0%,#98101f 48%,#6a0815 100%);
  border-right:1px solid rgba(255,255,255,.08);
}
section[data-testid="stSidebar"] > div{padding-top:1rem;}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] label p,
section[data-testid="stSidebar"] .stMarkdown p{
  color:#fff !important;
}
section[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.18);}
.sidebar-brand{
  background:rgba(255,255,255,.10);
  border:1px solid rgba(255,255,255,.16);
  border-radius:18px;
  padding:16px 16px 14px;
  margin:0 0 16px;
}
.sidebar-brand .sb-en{font-size:11px;letter-spacing:.13em;color:#ffdca1;font-weight:800;}
.sidebar-brand .sb-title{font-size:21px;color:#fff;font-weight:900;margin-top:3px;}
.sidebar-brand .sb-note{font-size:11px;color:rgba(255,255,255,.72);margin-top:4px;line-height:1.5;}
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] input{
  background:#fff !important;
  color:#2d1b1f !important;
  border-radius:10px !important;
}

/* Tabs */
div[data-baseweb="tab-list"]{
  gap:7px;
  background:#fff;
  padding:7px;
  border:1px solid var(--line);
  border-radius:16px;
  box-shadow:0 7px 18px rgba(122,9,23,.045);
}
button[data-baseweb="tab"]{
  border-radius:11px;
  padding:10px 13px;
  color:#6e565b;
  font-weight:750;
  transition:all .2s ease;
}
button[data-baseweb="tab"][aria-selected="true"]{
  color:#fff !important;
  background:linear-gradient(135deg,var(--red-800),var(--red-600));
  box-shadow:0 7px 15px rgba(180,20,37,.18);
}
button[data-baseweb="tab"][aria-selected="true"] p{color:#fff !important;}

/* Headings */
h1,h2,h3{color:var(--red-900);letter-spacing:-.01em;}
h2,h3{font-weight:850 !important;}
[data-testid="stMarkdownContainer"] h3{
  padding-left:12px;
  border-left:4px solid var(--red-700);
}

/* Buttons */
.stButton > button,
.stDownloadButton > button{
  border-radius:11px !important;
  border:1px solid #d9a5aa !important;
  font-weight:750 !important;
  transition:all .18s ease !important;
}
.stButton > button:hover,
.stDownloadButton > button:hover{
  border-color:var(--red-700) !important;
  color:var(--red-800) !important;
  transform:translateY(-1px);
  box-shadow:0 7px 16px rgba(180,20,37,.12);
}
.stButton > button[kind="primary"]{
  color:white !important;
  border-color:var(--red-700) !important;
  background:linear-gradient(135deg,var(--red-800),var(--red-600)) !important;
  box-shadow:0 8px 18px rgba(180,20,37,.20) !important;
}
.stButton > button[kind="primary"]:hover{color:#fff !important;filter:brightness(1.04);}

/* Metrics */
div[data-testid="stMetric"]{
  background:linear-gradient(180deg,#fff 0%,#fff8f7 100%);
  border:1px solid var(--line);
  border-top:3px solid var(--red-700);
  padding:14px 15px;
  border-radius:16px;
  box-shadow:0 8px 22px rgba(122,9,23,.06);
}
div[data-testid="stMetricLabel"] p{color:#80676d;font-weight:700;}
div[data-testid="stMetricValue"]{color:var(--red-900);font-weight:900;}

/* Inputs */
.stTextInput input,
.stNumberInput input,
.stDateInput input,
[data-baseweb="select"] > div,
.stTextArea textarea{
  border-radius:10px !important;
  border-color:#ead3d5 !important;
}
.stTextInput input:focus,
.stNumberInput input:focus,
.stDateInput input:focus,
.stTextArea textarea:focus{
  border-color:var(--red-600) !important;
  box-shadow:0 0 0 1px rgba(201,27,45,.15) !important;
}

/* Slider */
[data-baseweb="slider"] [role="slider"]{
  background:var(--red-700) !important;
  border-color:var(--red-700) !important;
}

/* Tables / expanders / alerts */
[data-testid="stDataFrame"]{
  border:1px solid var(--line);
  border-radius:14px;
  overflow:hidden;
  box-shadow:0 5px 16px rgba(122,9,23,.04);
}
[data-testid="stExpander"]{
  border:1px solid var(--line) !important;
  border-radius:14px !important;
  background:#fff !important;
}
[data-testid="stAlert"]{border-radius:13px;}

/* File uploader */
[data-testid="stFileUploaderDropzone"]{
  border:1.5px dashed #d99aa2;
  background:#fff7f6;
  border-radius:15px;
}

/* Captions */
.stCaptionContainer, small{color:#8a7478 !important;}

/* Competition footer */
.competition-footer{
  margin-top:24px;
  padding:15px 18px;
  border-radius:15px;
  background:#fff5f4;
  border:1px solid var(--line);
  color:#765e63;
  font-size:12px;
  text-align:center;
}

@media (max-width: 980px){
  .flow-wrap{grid-template-columns:1fr 1fr;}
  .hero-title{font-size:34px;}
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        """
<div class="agrigel-hero">
  <div class="hero-kicker">中国国际大学生创新大赛 · 智慧农业产品化原型</div>
  <div class="hero-title">凝策 <span>AgriGel-Opt</span></div>
  <div class="hero-subtitle">水凝胶番茄栽培智能决策系统</div>
  <div class="hero-desc">以靖安、玉山番茄场景为首证，融合土壤、气象、水肥与生育期信息，完成“环境诊断—智能配胶—灌溉联动—产量收益—风险校验”的闭环决策。</div>
  <div class="hero-tags">
    <div class="hero-tag">GPR + XGBoost</div>
    <div class="hero-tag">Bayesian 配方寻优</div>
    <div class="hero-tag">7日灌溉联动</div>
    <div class="hero-tag">一地一方 · 一作一策</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_system_flow():
    st.markdown(
        """
<div class="flow-wrap">
  <div class="flow-item"><span class="flow-no">01</span><span class="flow-title">环境诊断</span><div class="flow-desc">气候 · 土壤 · 水分 · 光照 · 肥料</div></div>
  <div class="flow-item"><span class="flow-no">02</span><span class="flow-title">AI智能配胶</span><div class="flow-desc">比例 · 功能模块 · 亩用量 · 施用方式</div></div>
  <div class="flow-item"><span class="flow-no">03</span><span class="flow-title">灌溉联动</span><div class="flow-desc">未来7天 · ET₀ · 降雨 · 动态灌水</div></div>
  <div class="flow-item"><span class="flow-no">04</span><span class="flow-title">产量收益</span><div class="flow-desc">稳产 · 提质 · 节本 · ROI情景测算</div></div>
  <div class="flow-item"><span class="flow-no">05</span><span class="flow-title">风险校验</span><div class="flow-desc">干旱 · 涝害 · 盐分 · 过量施用</div></div>
</div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_brand():
    st.markdown(
        """
<div class="sidebar-brand">
  <div class="sb-en">AGRIGEL DECISION ENGINE</div>
  <div class="sb-title">凝策 · 地块参数台</div>
  <div class="sb-note">先定义地块与番茄生育阶段，再由模型生成可执行处方。</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        """
<div class="competition-footer">V2 决策闭环：环境数据输入 → AI配方推荐 → 灌溉施用 → 产量收益 → 风险/可信度 → 田间数据回流。当前为科研与比赛原型，真实生产处方须经田间校准。</div>
        """,
        unsafe_allow_html=True,
    )
