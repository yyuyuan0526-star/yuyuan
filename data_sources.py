from __future__ import annotations
import requests
import pandas as pd
import numpy as np

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

NASA_PARAMETERS = [
    "T2M", "T2M_MAX", "T2M_MIN", "RH2M",
    "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "WS2M"
]

SOIL_PROPERTIES = ["phh2o", "soc", "clay", "sand", "silt", "bdod"]
SOIL_DEPTHS = ["0-5cm", "5-15cm", "15-30cm"]


def fetch_nasa_power(lat: float, lon: float, start_date, end_date, timeout=30) -> pd.DataFrame:
    start = pd.Timestamp(start_date).strftime("%Y%m%d")
    end = pd.Timestamp(end_date).strftime("%Y%m%d")
    params = {
        "parameters": ",".join(NASA_PARAMETERS),
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start,
        "end": end,
        "format": "JSON",
    }
    r = requests.get(NASA_POWER_URL, params=params, timeout=timeout)
    r.raise_for_status()
    payload = r.json()
    p = payload["properties"]["parameter"]
    idx = sorted(set().union(*[set(v.keys()) for v in p.values()]))
    df = pd.DataFrame(index=pd.to_datetime(idx, format="%Y%m%d"))
    for name in NASA_PARAMETERS:
        if name in p:
            df[name] = pd.Series(p[name], dtype="float64").reindex(idx).values
    df.index.name = "date"
    return df.replace([-999, -999.0, -9999], np.nan)


def summarize_climate(df: pd.DataFrame) -> dict:
    out = {}
    def mean(col):
        return float(df[col].mean()) if col in df else np.nan
    def total(col):
        return float(df[col].sum()) if col in df else np.nan

    out["avg_temp_c"] = mean("T2M")
    out["max_temp_mean_c"] = mean("T2M_MAX")
    out["min_temp_mean_c"] = mean("T2M_MIN")
    out["rh_pct"] = mean("RH2M")
    out["precip_mm"] = total("PRECTOTCORR")
    out["solar_mj_m2_day"] = mean("ALLSKY_SFC_SW_DWN")
    out["wind_m_s"] = mean("WS2M")
    out["rainy_days"] = int((df.get("PRECTOTCORR", pd.Series(dtype=float)) >= 1.0).sum())
    out["heavy_rain_days"] = int((df.get("PRECTOTCORR", pd.Series(dtype=float)) >= 25.0).sum())
    out["heat_days_35c"] = int((df.get("T2M_MAX", pd.Series(dtype=float)) >= 35.0).sum())
    out["climate_days"] = int(len(df))
    t, rh = out["avg_temp_c"], out["rh_pct"]
    if np.isfinite(t) and np.isfinite(rh):
        es = 0.6108 * np.exp(17.27 * t / (t + 237.3))
        out["vpd_kpa"] = float(es * (1 - rh / 100.0))
    else:
        out["vpd_kpa"] = np.nan
    return out


def _weighted_depth_value(layer):
    d_factor = layer.get("unit_measure", {}).get("d_factor", 1) or 1
    values, weights = [], []
    depth_weights = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}
    for d in layer.get("depths", []):
        label = d.get("label")
        if label not in depth_weights:
            continue
        mean = (d.get("values") or {}).get("mean")
        if mean is None:
            continue
        values.append(float(mean) / float(d_factor))
        weights.append(depth_weights[label])
    return float(np.average(values, weights=weights)) if values else np.nan


def fetch_soilgrids(lat: float, lon: float, timeout=30) -> dict:
    params = [("lon", lon), ("lat", lat), ("value", "mean")]
    for prop in SOIL_PROPERTIES:
        params.append(("property", prop))
    for depth in SOIL_DEPTHS:
        params.append(("depth", depth))
    r = requests.get(SOILGRIDS_URL, params=params, timeout=timeout)
    r.raise_for_status()
    payload = r.json()
    result = {}
    for layer in payload.get("properties", {}).get("layers", []):
        result[layer.get("name")] = _weighted_depth_value(layer)
    return {
        "soil_ph": result.get("phh2o", np.nan),
        "soil_soc_gkg": result.get("soc", np.nan),
        "soil_clay_pct": result.get("clay", np.nan) / 10 if np.isfinite(result.get("clay", np.nan)) else np.nan,
        "soil_sand_pct": result.get("sand", np.nan) / 10 if np.isfinite(result.get("sand", np.nan)) else np.nan,
        "soil_silt_pct": result.get("silt", np.nan) / 10 if np.isfinite(result.get("silt", np.nan)) else np.nan,
        "soil_bulk_density": result.get("bdod", np.nan),
    }
