from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta

from data_sources import fetch_nasa_power, summarize_climate, fetch_soilgrids
from demo_data import make_demo_trials, PPT_FORMULAS
from modeling import fit_models, bayesian_recommend
from evaluation import evaluate_cv
from decision_support import (
    fetch_open_meteo_forecast,
    prescription_execution,
    strategy_plans,
    make_irrigation_schedule,
    risk_assessment,
    economic_scenario,
    STAGE_KC_DEFAULT,
)

st.set_page_config(page_title="凝策 AgriGel-Opt", layout="wide", page_icon="🌱")

SITE_DEFAULTS={"靖安":{"lat":28.9500,"lon":115.2300},"玉山":{"lat":28.67677,"lon":118.24162}}
STAGES=["定植期","开花坐果期","果实膨大期","转色成熟期"]
MODULES=["基础保水","水肥协同","防病增强"]
ADDITIVES=["无","蒙脱土","海藻酸寡糖","海藻酸钠","葡萄糖"]
TARGET_LABELS={
    "water_retention_21d_pct":"21天保水表现(%)",
    "nutrient_retention_21d_pct":"21天养分保持(%)",
    "yield_gain_pct":"产量变化(%)",
    "brix_gain":"糖度变化(°Brix)",
    "disease_reduction_pct":"病害下降(%)",
}

st.title("凝策 AgriGel-Opt")
st.caption("水凝胶番茄栽培决策系统｜环境诊断 → 配方推荐 → 灌溉联动 → 产量收益 → 风险与可信度")
st.markdown("> **系统定位：** AI根据土壤—气象—作物生育期动态优化水凝胶和水肥管理，实现番茄节水、稳产、提质、增收。当前为科研原型，正式处方必须由靖安、玉山田间数据持续校准。")

with st.sidebar:
    st.header("地块与作物")
    site=st.selectbox("地区",["靖安","玉山","自定义"])
    if site=="自定义":
        lat=st.number_input("纬度",value=28.80,format="%.6f")
        lon=st.number_input("经度",value=116.50,format="%.6f")
        site_name=st.text_input("地区名称","自定义地块")
    else:
        lat=st.number_input("纬度",value=float(SITE_DEFAULTS[site]["lat"]),format="%.6f")
        lon=st.number_input("经度",value=float(SITE_DEFAULTS[site]["lon"]),format="%.6f")
        site_name=site
    crop=st.text_input("作物","番茄")
    growth_stage=st.selectbox("生育期",STAGES)
    planting_density=st.number_input("种植密度 株/亩",min_value=100.0,value=2000.0,step=100.0)
    baseline_yield=st.number_input("基准亩产 kg/亩",min_value=100.0,value=5000.0,step=100.0)
    tomato_price=st.number_input("番茄售价 元/kg",min_value=0.1,value=4.0,step=0.1)
    st.divider()
    st.header("根区与水肥")
    soil_moisture0=st.number_input("当前根际含水率 %",min_value=1.0,max_value=80.0,value=28.0)
    soil_ec=st.number_input("土壤EC（风险输入）",min_value=0.0,value=1.0,step=0.1)
    n_kg_ha=st.number_input("N施用量 kg/ha",min_value=0.0,value=280.0)
    p_kg_ha=st.number_input("P施用量 kg/ha",min_value=0.0,value=130.0)
    k_kg_ha=st.number_input("K施用量 kg/ha",min_value=0.0,value=260.0)

T1,T2,T3,T4,T5,T6,T7=st.tabs([
    "① 环境诊断","② 试验数据","③ 模型可信度","④ 水凝胶处方","⑤ 灌溉联动","⑥ 产量与收益","⑦ 风险预警"
])

with T1:
    st.subheader("环境诊断：历史背景 + 未来7天")
    st.info("NASA POWER用于环境窗口；Open-Meteo用于7日预报；SoilGrids只作背景先验，正式模型以实测土样和传感器为准。")
    c1,c2=st.columns(2)
    with c1:
        end_date=st.date_input("历史窗口结束",value=date.today())
        start_date=st.date_input("历史窗口开始",value=date.today()-timedelta(days=30))
        if st.button("抓取 NASA POWER 环境数据",type="primary"):
            try:
                df=fetch_nasa_power(lat,lon,start_date,end_date)
                st.session_state["climate_df"]=df
                st.session_state["climate"]=summarize_climate(df)
                st.success("NASA POWER数据获取成功")
            except Exception as e:
                st.error(f"NASA POWER 获取失败：{e}")
        climate=st.session_state.get("climate",{})
        if climate:
            a,b,c,d=st.columns(4)
            a.metric("平均温度",f'{climate.get("avg_temp_c",np.nan):.1f}℃')
            b.metric("相对湿度",f'{climate.get("rh_pct",np.nan):.1f}%')
            c.metric("累计降水",f'{climate.get("precip_mm",np.nan):.1f} mm')
            d.metric("平均辐射",f'{climate.get("solar_mj_m2_day",np.nan):.1f} MJ/m²/d')
            st.line_chart(st.session_state["climate_df"][["T2M","RH2M","PRECTOTCORR"]])
        if st.button("获取未来7天天气"):
            try:
                st.session_state["forecast"]=fetch_open_meteo_forecast(lat,lon,7)
                st.success("7天天气预报获取成功")
            except Exception as e:
                st.error(f"未来天气获取失败：{e}")
        if "forecast" in st.session_state:
            st.dataframe(st.session_state["forecast"],use_container_width=True,hide_index=True)
    with c2:
        if st.button("抓取 SoilGrids 土壤背景"):
            try:
                st.session_state["soil"]=fetch_soilgrids(lat,lon)
                st.success("SoilGrids背景获取成功")
            except Exception as e:
                st.warning(f"SoilGrids 获取失败，可人工填写：{e}")
        soil=st.session_state.get("soil",{})
        def sv(key,default):
            v=soil.get(key,np.nan)
            return float(v) if pd.notna(v) else default
        soil_ph=st.number_input("pH",value=sv("soil_ph",6.2))
        soil_soc=st.number_input("SOC / 有机碳 g/kg",value=sv("soil_soc_gkg",22.0))
        soil_clay=st.number_input("黏粒 %",value=sv("soil_clay_pct",30.0))
        soil_sand=st.number_input("砂粒 %",value=sv("soil_sand_pct",35.0))
        soil_silt=st.number_input("粉粒 %",value=sv("soil_silt_pct",35.0))
    if climate:
        st.session_state["base_env"]={
            "site":site_name,"crop":crop,"growth_stage":growth_stage,
            "avg_temp_c":climate.get("avg_temp_c",25.0),"rh_pct":climate.get("rh_pct",75.0),
            "precip_mm":climate.get("precip_mm",100.0),"solar_mj_m2_day":climate.get("solar_mj_m2_day",14.0),
            "vpd_kpa":climate.get("vpd_kpa",0.7),"soil_ph":soil_ph,"soil_soc_gkg":soil_soc,
            "soil_clay_pct":soil_clay,"soil_sand_pct":soil_sand,"soil_silt_pct":soil_silt,
            "soil_moisture0_pct":soil_moisture0,"n_kg_ha":n_kg_ha,"p_kg_ha":p_kg_ha,"k_kg_ha":k_kg_ha
        }
        st.success("当前地块已形成“环境—土壤—水肥—生育期”输入向量")

with T2:
    st.subheader("田间试验数据库")
    st.write("### PPT已有配方种子")
    st.dataframe(PPT_FORMULAS,use_container_width=True,hide_index=True)
    st.caption("G1–G6作为配方种子；正式训练时一行应对应一个独立小区/重复。")
    uploaded=st.file_uploader("上传真实 field_trials.csv",type=["csv"])
    use_demo=st.toggle("没有完整数据时使用合成演示数据跑通软件",value=True)
    if uploaded:
        st.session_state["trials"]=pd.read_csv(uploaded)
        st.session_state["demo_loaded"]=False
        st.success(f"已载入 {len(st.session_state['trials'])} 条真实试验记录")
    elif use_demo:
        if "trials" not in st.session_state or not st.session_state.get("demo_loaded",False):
            st.session_state["trials"]=make_demo_trials()
            st.session_state["demo_loaded"]=True
        st.warning("当前为合成演示数据，仅用于验证系统流程；不得作为比赛/论文真实效果。")
    if "trials" in st.session_state:
        st.dataframe(st.session_state["trials"].head(40),use_container_width=True)
        st.download_button("下载当前训练数据CSV",st.session_state["trials"].to_csv(index=False).encode("utf-8-sig"),"agrigel_trials.csv","text/csv")

with T3:
    st.subheader("GPR + XGBoost 模型可信度")
    st.write("公开模型误差、拟合度、置信范围与数据来源，而不是只给一个推荐答案。")
    if st.button("训练并评估模型",type="primary"):
        if "trials" not in st.session_state:
            st.error("请先加载训练数据。")
        else:
            try:
                with st.spinner("正在训练与交叉验证……"):
                    models,_=fit_models(st.session_state["trials"])
                    metrics,cvpred=evaluate_cv(st.session_state["trials"])
                    st.session_state["models"]=models
                    st.session_state["metrics_v2"]=metrics
                    st.session_state["cvpred"]=cvpred
                st.success("训练完成")
            except Exception as e:
                st.error(str(e))
    if "metrics_v2" in st.session_state:
        m=st.session_state["metrics_v2"].copy()
        m["指标"]=m["target"].map(TARGET_LABELS)
        st.dataframe(m[["指标","RMSE","R2","MAPE_%","GPR_weight","XGB_weight"]],use_container_width=True,hide_index=True)
        target=st.selectbox("查看预测值 vs 实测值",list(TARGET_LABELS),format_func=lambda x:TARGET_LABELS[x])
        p=st.session_state["cvpred"]
        p=p[p["target"]==target][["actual","predicted"]].rename(columns={"actual":"实测值","predicted":"交叉验证预测值"})
        st.scatter_chart(p,x="实测值",y="交叉验证预测值")
        st.caption("R²越接近1越好，RMSE越低越好；MAPE在真实值接近0时可能失真。")
        if st.session_state.get("demo_loaded",False):
            st.error("当前可信度指标来自合成演示数据，只能检验代码，不代表真实模型精度。")

with T4:
    st.subheader("水凝胶精准处方")
    st.caption("核心输出：什么配方、用多少、怎么施。")
    if "models" not in st.session_state:
        st.info("请先在“③ 模型可信度”训练模型。")
    elif "base_env" not in st.session_state:
        st.info("请先在“① 环境诊断”形成当前地块输入。")
    else:
        c1,c2,c3=st.columns(3)
        with c1:
            w_water=st.slider("控水权重",0.0,1.0,0.25,0.05)
            w_nutrient=st.slider("控肥权重",0.0,1.0,0.20,0.05)
        with c2:
            w_yield=st.slider("增产权重",0.0,1.0,0.25,0.05)
            w_brix=st.slider("提质权重",0.0,1.0,0.15,0.05)
        with c3:
            w_disease=st.slider("防病权重",0.0,1.0,0.10,0.05)
            w_cost=st.slider("成本惩罚",0.0,0.5,0.10,0.05)
        risk=st.slider("不确定性惩罚",0.0,0.5,0.15,0.05)
        price=st.number_input("水凝胶材料价格 元/kg",min_value=0.0,value=800.0,step=50.0)
        with st.expander("配方搜索边界"):
            sa=st.slider("SA %",0.5,5.0,(1.0,3.5),0.1)
            cs=st.slider("CS %",0.2,3.0,(0.5,1.8),0.1)
            ga=st.slider("交联剂 %",0.02,0.6,(0.08,0.35),0.01)
            add=st.slider("添加剂 %",0.0,8.0,(0.0,5.0),0.1)
            app=st.slider("施用量 kg/亩",0.5,6.0,(1.0,4.0),0.1)
            adds=st.multiselect("允许的添加剂",ADDITIVES,default=ADDITIVES)
            mods=st.multiselect("允许的功能模块",MODULES,default=MODULES)
        weights={"water_retention_21d_pct":w_water,"nutrient_retention_21d_pct":w_nutrient,"yield_gain_pct":w_yield,"brix_gain":w_brix,"disease_reduction_pct":w_disease,"cost":w_cost}
        bounds={"sa_pct":sa,"cs_pct":cs,"glutaraldehyde_pct":ga,"additive_pct":add,"application_kg_mu":app}
        st.session_state["last_bounds"]=bounds
        if st.button("生成水凝胶处方",type="primary"):
            if not adds or not mods:
                st.error("至少选择一种添加剂和一个功能模块")
            else:
                with st.spinner("GPR/XGBoost性能预测 + Bayesian配方寻优中……"):
                    st.session_state["result"]=bayesian_recommend(st.session_state["models"],st.session_state["base_env"],weights,bounds,adds,mods,price,risk)
        if "result" in st.session_state:
            r=st.session_state["result"]; f=r["formula"]
            exe=prescription_execution(f,planting_density,growth_stage,soil_clay)
            st.session_state["execution"]=exe
            a,b,c,d=st.columns(4)
            a.metric("SA",f'{f["sa_pct"]:.2f}%'); b.metric("CS",f'{f["cs_pct"]:.2f}%'); c.metric("交联剂",f'{f["glutaraldehyde_pct"]:.3f}%'); d.metric("添加剂",f'{f["additive_type"]} {f["additive_pct"]:.2f}%')
            a,b,c=st.columns(3)
            a.metric("推荐量",f'{exe["kg_mu"]:.2f} kg/亩'); b.metric("折算单株",f'{exe["g_plant"]:.2f} g/株'); c.metric("折算公顷",f'{exe["kg_ha"]:.1f} kg/ha')
            st.write(f'**施用深度：** {exe["depth"]}')
            st.write(f'**施用方式：** {exe["method"]}')
            st.write(f'**功能模块：** {f["function_module"]}')
            pred=pd.DataFrame([{"指标":TARGET_LABELS[k],"预测值":round(v,3),"模型不确定性":round(r["uncertainty"][k],3),"近似95%不确定范围":f'{v-1.96*r["uncertainty"][k]:.2f} ～ {v+1.96*r["uncertainty"][k]:.2f}'} for k,v in r["predictions"].items()])
            st.dataframe(pred,use_container_width=True,hide_index=True)
            st.caption("该95%范围为模型不确定性近似区间，不等同于经过田间校准的统计置信区间。")
            st.write("### 三种执行方案")
            st.dataframe(strategy_plans(exe),use_container_width=True,hide_index=True)
            if st.session_state.get("demo_loaded",False):
                st.error("当前处方来自合成演示训练集，不能直接用于田间生产。")

with T5:
    st.subheader("未来7天灌溉联动")
    if "result" not in st.session_state:
        st.info("请先生成水凝胶处方。")
    else:
        if "forecast" not in st.session_state:
            if st.button("自动获取7天天气并生成灌溉建议",type="primary"):
                try:
                    st.session_state["forecast"]=fetch_open_meteo_forecast(lat,lon,7)
                except Exception as e:
                    st.error(f"天气获取失败：{e}")
        if "forecast" in st.session_state:
            kc=st.slider("作物需水系数Kc（原型，可校准）",0.3,1.4,float(STAGE_KC_DEFAULT.get(growth_stage,0.9)),0.05)
            target_moist=st.slider("目标根际含水率 %",15.0,50.0,30.0,1.0)
            sched=make_irrigation_schedule(st.session_state["forecast"],growth_stage,soil_moisture0,target_moist,st.session_state["result"]["predictions"]["water_retention_21d_pct"],kc)
            st.session_state["irrigation_schedule"]=sched
            a,b,c=st.columns(3)
            a.metric("7日建议灌水",f'{sched["建议灌水_mm"].sum():.1f} mm'); b.metric("7日预报降水",f'{st.session_state["forecast"]["precip_mm"].sum():.1f} mm'); c.metric("7日ET0",f'{st.session_state["forecast"]["et0_mm"].sum():.1f} mm')
            st.dataframe(sched,use_container_width=True,hide_index=True)
            st.bar_chart(sched.set_index("日期")[["建议灌水_mm","降水_mm"]])
            st.warning("该灌溉表是概念决策规则，正式农用前必须用传感器与灌溉试验校准。")

with T6:
    st.subheader("产量、品质与投入产出")
    if "result" not in st.session_state:
        st.info("请先生成水凝胶处方。")
    else:
        r=st.session_state["result"]; p=r["predictions"]
        pred_yield=baseline_yield*(1+p["yield_gain_pct"]/100.0)
        baseline_brix=st.number_input("基准糖度 °Brix",min_value=0.0,value=5.0,step=0.1)
        a,b,c=st.columns(3)
        a.metric("预计亩产",f"{pred_yield:.0f} kg/亩",f'{p["yield_gain_pct"]:.1f}%'); b.metric("预计糖度",f'{baseline_brix+p["brix_gain"]:.2f} °Brix',f'{p["brix_gain"]:+.2f}'); c.metric("病害下降潜力",f'{p["disease_reduction_pct"]:.1f}%')
        st.write("### 成本收益场景测算")
        c1,c2,c3=st.columns(3)
        with c1:
            baseline_irrigation=st.number_input("常规7日灌溉量 mm",min_value=0.0,value=30.0)
            irrigation_cost=st.number_input("灌溉综合成本 元/(mm·亩)",min_value=0.0,value=2.0)
        with c2:
            fertilizer_cost=st.number_input("常规肥料成本 元/亩",min_value=0.0,value=1200.0,step=50.0)
            other_savings=st.number_input("人工/农药等其他可核实节省 元/亩",min_value=0.0,value=0.0,step=50.0)
        with c3:
            st.write("材料成本采用水凝胶价格×推荐用量；节水收益采用联动灌溉结果与常规灌溉量比较。")
        if "irrigation_schedule" in st.session_state:
            econ=economic_scenario(r,st.session_state["irrigation_schedule"],baseline_yield,tomato_price,baseline_irrigation,irrigation_cost,fertilizer_cost,other_savings)
            a,b,c,d=st.columns(4)
            a.metric("新增产值",f'{econ["added_revenue_yuan_mu"]:.0f} 元/亩'); b.metric("7日节水",f'{econ["irrigation_saved_mm_7d"]:.1f} mm'); c.metric("预计净增益",f'{econ["net_gain_yuan_mu"]:.0f} 元/亩'); d.metric("ROI","—" if not np.isfinite(econ["roi"]) else f'{econ["roi"]:.2f}')
            st.warning("收益为情景估算，不是已实现收益；只有真实投入、产量、售价、节水节肥均有记录后，才可作为实证经济数据。")
        else:
            st.info("请先在“⑤ 灌溉联动”生成7日灌溉建议。")

with T7:
    st.subheader("根区与天气风险预警")
    if "result" not in st.session_state:
        st.info("请先生成水凝胶处方。")
    elif "forecast" not in st.session_state:
        st.info("请先获取未来7天天气。")
    else:
        upper=st.session_state.get("last_bounds",{}).get("application_kg_mu",(1.0,4.0))[1]
        risks=risk_assessment(st.session_state["forecast"],soil_moisture0,soil_clay,soil_ec,st.session_state["result"]["formula"]["application_kg_mu"],upper,growth_stage)
        st.dataframe(risks,use_container_width=True,hide_index=True)
        a,b,c=st.columns(3)
        a.metric("高风险项",int((risks["等级"]=="高").sum())); b.metric("中风险项",int((risks["等级"]=="中").sum())); c.metric("安全边界检查","已执行")
        st.write("**系统原则：水凝胶不是越多越好。** 高降雨、黏重土、高含水或推荐量接近搜索上限时，系统主动提示降低集中施量并优先排水/通气。")

st.divider()
st.caption("V2闭环：环境数据输入 → AI配方推荐 → 灌溉施用方案 → 产量收益评估 → 风险/可信度 → 田间数据回流。下一阶段再接入传感器、地块档案、图像诊断与区域适配地图。")
