from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta

from data_sources import fetch_nasa_power, summarize_climate, fetch_soilgrids
from demo_data import make_demo_trials, PPT_FORMULAS
from modeling import fit_models, bayesian_recommend

st.set_page_config(page_title="凝策 AgriGel-Opt", layout="wide")
SITE_DEFAULTS={"靖安":{"lat":28.9500,"lon":115.2300},"玉山":{"lat":28.67677,"lon":118.24162}}
STAGES=["定植期","开花坐果期","果实膨大期","转色成熟期"]
MODULES=["基础保水","水肥协同","防病增强"]
ADDITIVES=["无","蒙脱土","海藻酸寡糖","海藻酸钠","葡萄糖"]

st.title("凝策 AgriGel-Opt")
st.caption("多源环境驱动的农业水凝胶精准配方与施用决策模型｜输入一块地，输出一张水凝胶处方")

with st.sidebar:
    st.header("场景")
    site=st.selectbox("地区",["靖安","玉山","自定义"])
    if site=="自定义":
        lat=st.number_input("纬度",value=28.80,format="%.6f"); lon=st.number_input("经度",value=116.50,format="%.6f"); site_name=st.text_input("地区名称","自定义地块")
    else:
        lat=st.number_input("纬度",value=float(SITE_DEFAULTS[site]["lat"]),format="%.6f"); lon=st.number_input("经度",value=float(SITE_DEFAULTS[site]["lon"]),format="%.6f"); site_name=site
    crop=st.text_input("作物","番茄"); growth_stage=st.selectbox("生育期",STAGES)
    end_date=st.date_input("环境窗口结束",value=date.today()); start_date=st.date_input("环境窗口开始",value=date.today()-timedelta(days=30))
    st.divider(); st.header("施肥 / 基线")
    n_kg_ha=st.number_input("N施用量 kg/ha",min_value=0.0,value=280.0)
    p_kg_ha=st.number_input("P施用量 kg/ha",min_value=0.0,value=130.0)
    k_kg_ha=st.number_input("K施用量 kg/ha",min_value=0.0,value=260.0)
    soil_moisture0=st.number_input("当前根际含水率 %",min_value=1.0,max_value=80.0,value=28.0)

tabs=st.tabs(["① 环境数据","② 训练数据","③ 模型训练","④ 配方寻优"])

with tabs[0]:
    st.subheader("环境参数：气候 + 土壤 + 水肥")
    st.info("县域坐标仅作演示；正式科研请替换为试验小区精确GPS。SoilGrids只作背景先验，最终以实测土样为准。")
    c1,c2=st.columns(2)
    with c1:
        if st.button("抓取 NASA POWER 气候数据",type="primary"):
            try:
                df=fetch_nasa_power(lat,lon,start_date,end_date); st.session_state["climate_df"]=df; st.session_state["climate"]=summarize_climate(df); st.success("气候数据抓取成功")
            except Exception as e: st.error(f"NASA POWER 获取失败：{e}")
        climate=st.session_state.get("climate",{})
        if climate:
            st.json(climate); st.line_chart(st.session_state["climate_df"][["T2M","RH2M","PRECTOTCORR"]])
    with c2:
        if st.button("抓取 SoilGrids 土壤背景"):
            try: st.session_state["soil"]=fetch_soilgrids(lat,lon); st.success("SoilGrids 获取成功")
            except Exception as e: st.warning(f"SoilGrids 获取失败，可人工填写：{e}")
        soil=st.session_state.get("soil",{})
        def sv(key,default):
            v=soil.get(key,np.nan); return float(v) if pd.notna(v) else default
        soil_ph=st.number_input("pH",value=sv("soil_ph",6.2)); soil_soc=st.number_input("SOC / 有机碳 g/kg",value=sv("soil_soc_gkg",22.0))
        soil_clay=st.number_input("黏粒 %",value=sv("soil_clay_pct",30.0)); soil_sand=st.number_input("砂粒 %",value=sv("soil_sand_pct",35.0)); soil_silt=st.number_input("粉粒 %",value=sv("soil_silt_pct",35.0))
    if climate:
        st.session_state["base_env"]={"site":site_name,"crop":crop,"growth_stage":growth_stage,"avg_temp_c":climate.get("avg_temp_c",25.0),"rh_pct":climate.get("rh_pct",75.0),"precip_mm":climate.get("precip_mm",100.0),"solar_mj_m2_day":climate.get("solar_mj_m2_day",14.0),"vpd_kpa":climate.get("vpd_kpa",0.7),"soil_ph":soil_ph,"soil_soc_gkg":soil_soc,"soil_clay_pct":soil_clay,"soil_sand_pct":soil_sand,"soil_silt_pct":soil_silt,"soil_moisture0_pct":soil_moisture0,"n_kg_ha":n_kg_ha,"p_kg_ha":p_kg_ha,"k_kg_ha":k_kg_ha}
        st.success("当前场景已形成模型输入向量")

with tabs[1]:
    st.subheader("配方参数与田间结果数据")
    st.write("### PPT已有配方种子"); st.dataframe(PPT_FORMULAS,use_container_width=True)
    uploaded=st.file_uploader("上传真实 field_trials.csv",type=["csv"]); use_demo=st.toggle("没有完整数据时，使用合成演示数据跑通软件",value=True)
    if uploaded:
        st.session_state["trials"]=pd.read_csv(uploaded); st.session_state["demo_loaded"]=False; st.success(f"已载入 {len(st.session_state['trials'])} 条真实记录")
    elif use_demo:
        if "trials" not in st.session_state or not st.session_state.get("demo_loaded",False): st.session_state["trials"]=make_demo_trials(); st.session_state["demo_loaded"]=True
        st.warning("当前为合成演示数据，仅用于验证软件流程，不能作为比赛或论文结果。")
    if "trials" in st.session_state:
        st.dataframe(st.session_state["trials"].head(30),use_container_width=True)
        st.download_button("下载当前训练数据CSV",st.session_state["trials"].to_csv(index=False).encode("utf-8-sig"),"agrigel_trials.csv","text/csv")

with tabs[2]:
    st.subheader("GPR + XGBoost 集成性能预测")
    if st.button("训练模型",type="primary"):
        try:
            models,metrics=fit_models(st.session_state["trials"]); st.session_state["models"]=models; st.session_state["metrics"]=metrics; st.success("模型训练完成")
        except Exception as e: st.error(str(e))
    if "metrics" in st.session_state: st.dataframe(st.session_state["metrics"],use_container_width=True)

with tabs[3]:
    st.subheader("Bayesian 配方寻优")
    if "models" not in st.session_state: st.info("请先训练模型")
    elif "base_env" not in st.session_state: st.info("请先获取/填写当前环境")
    else:
        c1,c2,c3=st.columns(3)
        with c1: w_water=st.slider("控水",0.0,1.0,0.25,0.05); w_nutrient=st.slider("控肥",0.0,1.0,0.20,0.05)
        with c2: w_yield=st.slider("增产",0.0,1.0,0.25,0.05); w_brix=st.slider("提质",0.0,1.0,0.15,0.05)
        with c3: w_disease=st.slider("防病",0.0,1.0,0.10,0.05); w_cost=st.slider("成本惩罚",0.0,0.5,0.10,0.05)
        risk=st.slider("不确定性惩罚",0.0,0.5,0.15,0.05); price=st.number_input("水凝胶材料价格 元/kg",min_value=0.0,value=800.0,step=50.0)
        sa=st.slider("SA %",0.5,5.0,(1.0,3.5),0.1); cs=st.slider("CS %",0.2,3.0,(0.5,1.8),0.1); ga=st.slider("交联剂 %",0.02,0.6,(0.08,0.35),0.01)
        add=st.slider("添加剂 %",0.0,8.0,(0.0,5.0),0.1); app=st.slider("施用量 kg/亩",0.5,6.0,(1.0,4.0),0.1)
        adds=st.multiselect("允许的添加剂",ADDITIVES,default=ADDITIVES); mods=st.multiselect("允许的功能模块",MODULES,default=MODULES)
        weights={"water_retention_21d_pct":w_water,"nutrient_retention_21d_pct":w_nutrient,"yield_gain_pct":w_yield,"brix_gain":w_brix,"disease_reduction_pct":w_disease,"cost":w_cost}
        bounds={"sa_pct":sa,"cs_pct":cs,"glutaraldehyde_pct":ga,"additive_pct":add,"application_kg_mu":app}
        if st.button("开始 Bayesian 配方寻优",type="primary"):
            if not adds or not mods: st.error("至少选择一种添加剂和一个功能模块")
            else:
                with st.spinner("正在进行GPR贝叶斯寻优……"):
                    st.session_state["result"]=bayesian_recommend(st.session_state["models"],st.session_state["base_env"],weights,bounds,adds,mods,price,risk)
        if "result" in st.session_state:
            r=st.session_state["result"]; f=r["formula"]; st.success("推荐完成")
            a,b,c,d=st.columns(4); a.metric("SA",f'{f["sa_pct"]:.2f}%'); b.metric("CS",f'{f["cs_pct"]:.2f}%'); c.metric("交联剂",f'{f["glutaraldehyde_pct"]:.3f}%'); d.metric("亩施用量",f'{f["application_kg_mu"]:.2f} kg/亩')
            st.write({"地区":f["site"],"作物":f["crop"],"生育期":f["growth_stage"],"添加剂":f["additive_type"],"添加剂比例":round(f["additive_pct"],3),"功能模块":f["function_module"],"预计材料成本_元亩":round(r["cost_yuan_mu"],2),"综合效用分":round(r["best_score"],4)})
            st.dataframe(pd.DataFrame([{"指标":k,"预测值":v,"不确定性":r["uncertainty"][k]} for k,v in r["predictions"].items()]),use_container_width=True)
            st.line_chart(r["history"].set_index("iteration")["utility"])
            if st.session_state.get("demo_loaded",False): st.error("当前结果来自合成演示数据，只能证明软件流程能跑通，不能作为真实配方建议。")

st.divider(); st.caption("科研底线：公开数据用于背景先验；正式模型必须以精确GPS、实测土壤、水肥记录和真实产量/品质结果为主。")
