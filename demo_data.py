from __future__ import annotations
import numpy as np
import pandas as pd

PPT_FORMULAS = pd.DataFrame([
    ["G1", 1.0, 0.5, 0.1, "无", 0.0],
    ["G2", 2.0, 1.0, 0.2, "蒙脱土", 5.0],
    ["G3", 3.0, 1.5, 0.3, "海藻酸寡糖", 1.0],
    ["G4", 3.0, 1.5, 0.3, "海藻酸寡糖", 2.0],
    ["G5", 3.0, 1.5, 0.3, "海藻酸钠", 1.0],
    ["G6", 3.0, 1.5, 0.3, "葡萄糖", 1.0],
], columns=["formula_id", "sa_pct", "cs_pct", "glutaraldehyde_pct", "additive_type", "additive_pct"])


def make_demo_trials(n=120, seed=42) -> pd.DataFrame:
    """Synthetic data ONLY for software demonstration."""
    rng = np.random.default_rng(seed)
    sites = rng.choice(["靖安", "玉山"], size=n)
    stages = rng.choice(["定植期", "开花坐果期", "果实膨大期", "转色成熟期"], size=n)
    modules = rng.choice(["基础保水", "水肥协同", "防病增强"], size=n, p=[0.45, 0.40, 0.15])
    additives = rng.choice(["无", "蒙脱土", "海藻酸寡糖", "海藻酸钠", "葡萄糖"], size=n)

    is_jingan = (sites == "靖安").astype(float)
    avg_temp = rng.normal(25.0 - 0.8 * is_jingan, 2.7, n)
    rh = np.clip(rng.normal(76 + 3 * is_jingan, 7, n), 45, 96)
    precip = np.clip(rng.gamma(2.3, 35, n) * (1.12 + 0.08 * is_jingan), 0, 420)
    solar = np.clip(rng.normal(14.5 - 0.5 * is_jingan, 2.5, n), 6, 23)
    vpd = np.clip(0.6108*np.exp(17.27*avg_temp/(avg_temp+237.3))*(1-rh/100), 0.1, 3.5)

    soil_ph = np.clip(rng.normal(6.25 - 0.10 * is_jingan, 0.35, n), 4.8, 7.5)
    soc = np.clip(rng.normal(22 + 3 * is_jingan, 6, n), 7, 45)
    clay = np.clip(rng.normal(29 + 4 * is_jingan, 7, n), 10, 55)
    sand = np.clip(rng.normal(38 - 3 * is_jingan, 9, n), 12, 70)
    silt = np.clip(100 - clay - sand, 8, 65)
    soil_moist0 = np.clip(rng.normal(27 + 2 * is_jingan, 6, n), 10, 48)

    sa = rng.uniform(1.0, 3.5, n)
    cs = rng.uniform(0.5, 1.8, n)
    ga = rng.uniform(0.08, 0.35, n)
    add_pct = rng.uniform(0, 5.0, n)
    app_rate = rng.uniform(1.0, 4.0, n)
    n_rate = rng.uniform(180, 420, n)
    p_rate = rng.uniform(70, 220, n)
    k_rate = rng.uniform(160, 420, n)

    formula_balance = (-1.5*(sa-2.7)**2 -1.1*(cs-1.25)**2 -18*(ga-0.23)**2 +0.55*add_pct +1.3*app_rate)
    dryness = 1.2*vpd + 0.055*avg_temp + 0.018*solar - 0.004*precip
    soil_hold = 0.07*clay + 0.06*soc + 0.08*soil_moist0

    water = np.clip(35 + 7.5*formula_balance + 2.0*dryness + 1.2*soil_hold + rng.normal(0, 4.0, n), 15, 88)
    nutrient = np.clip(46 + 4.5*formula_balance + 0.04*(n_rate+p_rate) + 0.5*soc - 0.22*precip + rng.normal(0, 5, n), 20, 93)
    module_fert = (modules == "水肥协同").astype(float)
    module_disease = (modules == "防病增强").astype(float)
    disease_red = np.clip(12 + 18*module_disease + 4.0*formula_balance + 0.2*rh + rng.normal(0, 8, n), 0, 88)
    yield_gain = np.clip(1.5 + 0.075*(water-45) + 0.055*(nutrient-50) + 1.4*module_fert + 0.03*disease_red + rng.normal(0, 2.5, n), -5, 24)
    brix_gain = np.clip(0.15 + 0.018*(nutrient-50) + 0.015*(water-45) - 0.03*np.maximum(water-75, 0) + rng.normal(0, 0.35, n), -0.7, 2.6)

    return pd.DataFrame({
        "site": sites, "crop": "番茄", "growth_stage": stages, "function_module": modules,
        "sa_pct": sa, "cs_pct": cs, "glutaraldehyde_pct": ga, "additive_type": additives,
        "additive_pct": add_pct, "application_kg_mu": app_rate, "avg_temp_c": avg_temp,
        "rh_pct": rh, "precip_mm": precip, "solar_mj_m2_day": solar, "vpd_kpa": vpd,
        "soil_ph": soil_ph, "soil_soc_gkg": soc, "soil_clay_pct": clay, "soil_sand_pct": sand,
        "soil_silt_pct": silt, "soil_moisture0_pct": soil_moist0, "n_kg_ha": n_rate,
        "p_kg_ha": p_rate, "k_kg_ha": k_rate, "water_retention_21d_pct": water,
        "nutrient_retention_21d_pct": nutrient, "yield_gain_pct": yield_gain,
        "brix_gain": brix_gain, "disease_reduction_pct": disease_red, "is_demo": 1,
    })
