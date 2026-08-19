from __future__ import annotations
import requests
import numpy as np
import pandas as pd

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

STAGE_KC_DEFAULT = {
    "定植期": 0.65,
    "开花坐果期": 0.95,
    "果实膨大期": 1.10,
    "转色成熟期": 0.85,
}

def fetch_open_meteo_forecast(lat: float, lon: float, days: int = 7, timeout: int = 30) -> pd.DataFrame:
    """7-day daily weather forecast from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "forecast_days": int(days),
        "timezone": "auto",
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "et0_fao_evapotranspiration",
            "shortwave_radiation_sum",
            "wind_speed_10m_max",
        ]),
    }
    r = requests.get(OPEN_METEO_URL, params=params, timeout=timeout)
    r.raise_for_status()
    d = r.json().get("daily", {})
    if not d or "time" not in d:
        raise RuntimeError("Open-Meteo未返回可用的日尺度预报。")
    n = len(d["time"])
    return pd.DataFrame({
        "date": pd.to_datetime(d["time"]),
        "tmax_c": d.get("temperature_2m_max", [np.nan]*n),
        "tmin_c": d.get("temperature_2m_min", [np.nan]*n),
        "precip_mm": d.get("precipitation_sum", [np.nan]*n),
        "precip_prob_pct": d.get("precipitation_probability_max", [np.nan]*n),
        "et0_mm": d.get("et0_fao_evapotranspiration", [np.nan]*n),
        "solar_mj_m2": d.get("shortwave_radiation_sum", [np.nan]*n),
        "wind_max_kmh": d.get("wind_speed_10m_max", [np.nan]*n),
    })

def prescription_execution(formula: dict, planting_density_per_mu: float, growth_stage: str, soil_clay_pct: float) -> dict:
    rate_mu = float(formula["application_kg_mu"])
    g_plant = 1000.0 * rate_mu / max(float(planting_density_per_mu), 1.0)
    rate_ha = rate_mu * 15.0
    if growth_stage == "定植期":
        depth = "10–15 cm根区"
        method = "定植穴/根际定点混施"
    elif growth_stage in ("开花坐果期", "果实膨大期"):
        depth = "12–20 cm主根活动层"
        method = "植株两侧条施或滴灌带附近定点施用"
    else:
        depth = "10–15 cm浅根区"
        method = "根际定点补施；避免大面积翻动根系"
    if soil_clay_pct >= 40:
        method += "；黏重土优先降低局部集中施量并加强通气"
    return {"kg_mu": rate_mu, "g_plant": g_plant, "kg_ha": rate_ha, "depth": depth, "method": method}

def strategy_plans(execution: dict) -> pd.DataFrame:
    base = execution["kg_mu"]
    rows = [
        ("保守型", 0.90, "优先控制材料投入，保留较高安全余量", "低"),
        ("平衡型", 1.00, "兼顾水分稳定、产量与成本", "中"),
        ("高效节水型", 1.10, "提高根区缓冲能力，并配合更积极的灌溉减量", "较高"),
    ]
    return pd.DataFrame([{
        "方案": name,
        "推荐量_kg亩": round(base*factor, 2),
        "推荐量_kg_ha": round(base*factor*15, 1),
        "定位": purpose,
        "节水目标": saving,
    } for name, factor, purpose, saving in rows])

def make_irrigation_schedule(forecast: pd.DataFrame, growth_stage: str, current_soil_moisture_pct: float,
                             target_soil_moisture_pct: float, predicted_water_retention_pct: float,
                             kc_override: float | None = None) -> pd.DataFrame:
    """Conceptual root-zone water-balance schedule; requires field calibration."""
    kc = float(kc_override if kc_override is not None else STAGE_KC_DEFAULT.get(growth_stage, 0.9))
    retention_credit = float(np.clip((predicted_water_retention_pct - 45.0) / 100.0, 0.0, 0.28))
    moisture_factor = np.clip((target_soil_moisture_pct-current_soil_moisture_pct)/max(target_soil_moisture_pct,1.0), -0.25, 0.45)
    rolling_moist = float(current_soil_moisture_pct)
    rows=[]
    for _, r in forecast.iterrows():
        et0 = float(r.get("et0_mm", 0.0) if pd.notna(r.get("et0_mm", np.nan)) else 0.0)
        rain = float(r.get("precip_mm", 0.0) if pd.notna(r.get("precip_mm", np.nan)) else 0.0)
        tmax = float(r.get("tmax_c", np.nan))
        crop_et = kc*et0
        effective_rain = min(rain*0.80, crop_et*1.2)
        gel_credit = crop_et*retention_credit
        raw_need = max(0.0, crop_et-effective_rain-gel_credit)
        adjusted_need = max(0.0, raw_need*(1.0+moisture_factor))
        if rain >= 20:
            adjusted_need = 0.0; action = "暂停灌溉"
        elif adjusted_need < 0.8:
            action = "暂缓/观察"
        else:
            action = "建议灌溉"
        if pd.notna(tmax) and tmax >= 35 and rain < 3:
            action += "；高温关注"
        rows.append({
            "日期": pd.Timestamp(r["date"]).date().isoformat(),
            "最高温_℃": round(tmax,1) if pd.notna(tmax) else np.nan,
            "降水_mm": round(rain,1),
            "ET0_mm": round(et0,2),
            "作物需水_ETc_mm": round(crop_et,2),
            "建议灌水_mm": round(adjusted_need,2),
            "建议": action,
        })
        rolling_moist += (effective_rain+adjusted_need-crop_et)*0.35
        rolling_moist = float(np.clip(rolling_moist,5,70))
        moisture_factor = np.clip((target_soil_moisture_pct-rolling_moist)/max(target_soil_moisture_pct,1.0), -0.25, 0.45)
    return pd.DataFrame(rows)

def risk_assessment(forecast: pd.DataFrame, soil_moisture_pct: float, soil_clay_pct: float, soil_ec: float,
                    application_kg_mu: float, app_upper_bound: float, growth_stage: str) -> pd.DataFrame:
    tmax = float(forecast["tmax_c"].max()) if len(forecast) else np.nan
    rain7 = float(forecast["precip_mm"].sum()) if len(forecast) else 0.0
    et07 = float(forecast["et0_mm"].sum()) if len(forecast) else 0.0
    rows=[]
    def add(name, level, basis, advice):
        rows.append({"风险":name,"等级":level,"判断依据":basis,"建议":advice})
    drought_index = et07-0.8*rain7
    if soil_moisture_pct < 20 or drought_index > 18:
        add("干旱/失水","高",f"当前含水率{soil_moisture_pct:.1f}%，7日ET0-有效降水≈{drought_index:.1f} mm","提高监测频率，优先执行节水型处方并分次灌溉")
    elif soil_moisture_pct < 27 or drought_index > 8:
        add("干旱/失水","中",f"当前含水率{soil_moisture_pct:.1f}%，7日水分亏缺指数≈{drought_index:.1f} mm","按日水量平衡调整灌溉")
    else:
        add("干旱/失水","低","当前根区水分与未来7日水量平衡相对稳定","维持监测")
    if rain7 >= 80 or (soil_moisture_pct >= 42 and soil_clay_pct >= 35):
        add("涝害/根系缺氧","高",f"7日降水{rain7:.1f} mm；黏粒{soil_clay_pct:.1f}%","暂停加大水凝胶施量，优先排水与通气")
    elif rain7 >= 45:
        add("涝害/根系缺氧","中",f"7日降水{rain7:.1f} mm","暴雨前减少灌水，检查排水")
    else:
        add("涝害/根系缺氧","低",f"7日降水{rain7:.1f} mm","常规观察")
    if pd.notna(tmax) and tmax >= 37:
        add("高温落花落果","高",f"未来最高温{tmax:.1f}℃","加强遮阴/通风，避免中午灌溉冲击")
    elif pd.notna(tmax) and tmax >= 34:
        add("高温落花落果","中",f"未来最高温{tmax:.1f}℃","关注开花坐果期高温")
    else:
        add("高温落花落果","低",f"未来最高温{tmax:.1f}℃" if pd.notna(tmax) else "无有效预报","常规观察")
    if soil_ec >= 2.5:
        add("盐分累积","高",f"EC={soil_ec:.2f}","降低肥盐集中输入，核查灌溉水EC与淋洗条件")
    elif soil_ec >= 1.5:
        add("盐分累积","中",f"EC={soil_ec:.2f}","控制追肥浓度并持续监测EC")
    else:
        add("盐分累积","低",f"EC={soil_ec:.2f}","维持监测")
    ratio = application_kg_mu/max(app_upper_bound,1e-6)
    if ratio >= 0.92:
        add("水凝胶过量/通气性下降","中",f"推荐量已达搜索上限的{ratio*100:.0f}%","建议设置更严格田间安全上限并进行根区通气验证")
    else:
        add("水凝胶过量/通气性下降","低","当前推荐量未接近设定上限","仍需以根系活力和含氧状态验证安全边界")
    return pd.DataFrame(rows)

def economic_scenario(result: dict, irrigation_schedule: pd.DataFrame, baseline_yield_kg_mu: float,
                      tomato_price_yuan_kg: float, baseline_irrigation_mm_7d: float,
                      irrigation_cost_yuan_mm_mu: float, baseline_fertilizer_cost_yuan_mu: float,
                      other_saved_cost_yuan_mu: float = 0.0) -> dict:
    yield_gain_pct = float(result["predictions"].get("yield_gain_pct",0.0))
    nutrient_ret = float(result["predictions"].get("nutrient_retention_21d_pct",50.0))
    predicted_yield = baseline_yield_kg_mu*(1.0+yield_gain_pct/100.0)
    added_revenue = max(0.0,predicted_yield-baseline_yield_kg_mu)*tomato_price_yuan_kg
    recommended_irrigation = float(irrigation_schedule["建议灌水_mm"].sum()) if len(irrigation_schedule) else baseline_irrigation_mm_7d
    irrigation_saved_mm = max(0.0,baseline_irrigation_mm_7d-recommended_irrigation)
    irrigation_saved_cost = irrigation_saved_mm*irrigation_cost_yuan_mm_mu
    fertilizer_saving_rate = float(np.clip((nutrient_ret-50.0)/250.0,0.0,0.15))
    fertilizer_saved_cost = baseline_fertilizer_cost_yuan_mu*fertilizer_saving_rate
    gel_cost = float(result.get("cost_yuan_mu",0.0))
    gross_benefit = added_revenue+irrigation_saved_cost+fertilizer_saved_cost+other_saved_cost_yuan_mu
    net_gain = gross_benefit-gel_cost
    roi = net_gain/gel_cost if gel_cost>0 else np.nan
    return {
        "predicted_yield_kg_mu":predicted_yield,
        "yield_gain_pct":yield_gain_pct,
        "added_revenue_yuan_mu":added_revenue,
        "irrigation_saved_mm_7d":irrigation_saved_mm,
        "irrigation_saved_cost_yuan_mu":irrigation_saved_cost,
        "fertilizer_saving_rate_pct":fertilizer_saving_rate*100,
        "fertilizer_saved_cost_yuan_mu":fertilizer_saved_cost,
        "gel_cost_yuan_mu":gel_cost,
        "net_gain_yuan_mu":net_gain,
        "roi":roi,
    }
