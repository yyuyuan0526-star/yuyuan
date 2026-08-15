from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error
from xgboost import XGBRegressor

NUMERIC_FEATURES = [
    "sa_pct","cs_pct","glutaraldehyde_pct","additive_pct","application_kg_mu",
    "avg_temp_c","rh_pct","precip_mm","solar_mj_m2_day","vpd_kpa",
    "soil_ph","soil_soc_gkg","soil_clay_pct","soil_sand_pct","soil_silt_pct",
    "soil_moisture0_pct","n_kg_ha","p_kg_ha","k_kg_ha"
]
CATEGORICAL_FEATURES = ["site","crop","growth_stage","function_module","additive_type"]
TARGETS = ["water_retention_21d_pct","nutrient_retention_21d_pct","yield_gain_pct","brix_gain","disease_reduction_pct"]


def _preprocessor():
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
    ])

@dataclass
class TargetModel:
    target: str
    pre: ColumnTransformer
    gpr: GaussianProcessRegressor
    xgb: XGBRegressor
    wg: float
    wx: float
    y_min: float
    y_max: float
    def predict(self, X):
        Z = self.pre.transform(X)
        gm, gs = self.gpr.predict(Z, return_std=True)
        xm = self.xgb.predict(Z)
        mu = self.wg*gm + self.wx*xm
        sd = np.sqrt((self.wg*gs)**2 + (0.5*np.abs(gm-xm))**2)
        return mu, sd


def _cv_rmse(df, target, kind, seed=42):
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[target].astype(float).values
    cv = KFold(n_splits=min(5, max(3, len(df)//10)), shuffle=True, random_state=seed)
    scores = []
    for tr, va in cv.split(X):
        pre = _preprocessor(); ztr = pre.fit_transform(X.iloc[tr]); zva = pre.transform(X.iloc[va])
        if kind == "gpr":
            m = GaussianProcessRegressor(kernel=ConstantKernel(1.0)*Matern(nu=2.5)+WhiteKernel(0.5), normalize_y=True, random_state=seed)
        else:
            m = XGBRegressor(n_estimators=180,max_depth=3,learning_rate=0.04,subsample=0.85,colsample_bytree=0.85,objective="reg:squarederror",random_state=seed,n_jobs=2)
        m.fit(ztr, y[tr]); p = m.predict(zva)
        scores.append(mean_squared_error(y[va], p)**0.5)
    return float(np.mean(scores))


def fit_models(df, random_state=42):
    need = set(NUMERIC_FEATURES+CATEGORICAL_FEATURES+TARGETS)
    missing = sorted(need-set(df.columns))
    if missing: raise ValueError(f"训练数据缺少字段: {missing}")
    clean = df.dropna(subset=TARGETS).copy()
    if len(clean) < 12: raise ValueError("至少需要12条完整记录。")
    X = clean[NUMERIC_FEATURES+CATEGORICAL_FEATURES]
    models, rows = {}, []
    for t in TARGETS:
        y = clean[t].astype(float).values
        rg, rx = _cv_rmse(clean,t,"gpr",random_state), _cv_rmse(clean,t,"xgb",random_state)
        ig, ix = 1/max(rg,1e-6), 1/max(rx,1e-6); wg = ig/(ig+ix); wx = 1-wg
        pre = _preprocessor(); Z = pre.fit_transform(X)
        gpr = GaussianProcessRegressor(kernel=ConstantKernel(1.0)*Matern(nu=2.5)+WhiteKernel(0.5), normalize_y=True, random_state=random_state).fit(Z,y)
        xgb = XGBRegressor(n_estimators=220,max_depth=3,learning_rate=0.035,subsample=0.85,colsample_bytree=0.85,objective="reg:squarederror",random_state=random_state,n_jobs=2,reg_lambda=2.0).fit(Z,y)
        models[t] = TargetModel(t,pre,gpr,xgb,wg,wx,float(np.percentile(y,5)),float(np.percentile(y,95)))
        rows.append({"target":t,"CV_RMSE_GPR":rg,"CV_RMSE_XGB":rx,"weight_GPR":wg,"weight_XGB":wx})
    return models, pd.DataFrame(rows)


def predict_all(models, Xrow):
    pred, unc = {}, {}
    for t,m in models.items():
        mu,sd = m.predict(Xrow); pred[t],unc[t] = float(mu[0]),float(sd[0])
    return pred,unc


def _norm(v, lo, hi):
    return 0.5 if hi<=lo else float(np.clip((v-lo)/(hi-lo),0,1))


def _utility(models,preds,unc,weights,price,rate,risk):
    score=pen=tw=0.0
    for t,w in weights.items():
        if t not in models or w<=0: continue
        m=models[t]; span=max(m.y_max-m.y_min,1e-6)
        score += w*_norm(preds[t],m.y_min,m.y_max); pen += w*unc[t]/span; tw += w
    if tw: score/=tw; pen/=tw
    cost=price*rate; cost_norm=np.clip(cost/max(price*4.0,1),0,1)
    return float(score-weights.get("cost",0)*cost_norm-risk*pen), float(cost)


def _candidate(rng,bounds,adds,mods):
    return [rng.uniform(*bounds[k]) for k in ["sa_pct","cs_pct","glutaraldehyde_pct","additive_pct","application_kg_mu"]] + [int(rng.integers(len(adds))),int(rng.integers(len(mods)))]


def _vec(c,bounds,adds,mods):
    out=[]
    for k,v in zip(["sa_pct","cs_pct","glutaraldehyde_pct","additive_pct","application_kg_mu"],c[:5]):
        lo,hi=bounds[k]; out.append((v-lo)/(hi-lo))
    out += [c[5]/max(len(adds)-1,1), c[6]/max(len(mods)-1,1)]
    return np.array(out)


def _ei(mu,sd,best,xi=0.01):
    sd=np.maximum(sd,1e-12); imp=mu-best-xi; z=imp/sd
    return imp*norm.cdf(z)+sd*norm.pdf(z)


def bayesian_recommend(models,base_env,weights,bounds,additive_choices,module_choices,material_price_yuan_kg,risk_aversion=0.15,n_initial=12,n_iter=20,candidate_pool=1500,random_state=42):
    rng=np.random.default_rng(random_state); xs=[]; ys=[]; meta=[]
    def evaluate(c):
        row=dict(base_env); row.update({"sa_pct":c[0],"cs_pct":c[1],"glutaraldehyde_pct":c[2],"additive_pct":c[3],"application_kg_mu":c[4],"additive_type":additive_choices[c[5]],"function_module":module_choices[c[6]]})
        preds,unc=predict_all(models,pd.DataFrame([row])); s,cost=_utility(models,preds,unc,weights,material_price_yuan_kg,c[4],risk_aversion)
        return s,preds,unc,cost,row
    for _ in range(n_initial):
        c=_candidate(rng,bounds,additive_choices,module_choices); s,p,u,cost,row=evaluate(c); xs.append(_vec(c,bounds,additive_choices,module_choices)); ys.append(s); meta.append((c,p,u,cost,row))
    for _ in range(n_iter):
        X=np.vstack(xs); y=np.array(ys)
        gp=GaussianProcessRegressor(kernel=ConstantKernel(1.0)*Matern(nu=2.5)+WhiteKernel(1e-4),normalize_y=True,random_state=random_state).fit(X,y)
        cs=[_candidate(rng,bounds,additive_choices,module_choices) for _ in range(candidate_pool)]
        Z=np.vstack([_vec(c,bounds,additive_choices,module_choices) for c in cs]); mu,sd=gp.predict(Z,return_std=True)
        c=cs[int(np.argmax(_ei(mu,sd,float(np.max(y)))))]
        s,p,u,cost,row=evaluate(c); xs.append(_vec(c,bounds,additive_choices,module_choices)); ys.append(s); meta.append((c,p,u,cost,row))
    i=int(np.argmax(ys)); c,p,u,cost,row=meta[i]
    return {"best_score":float(ys[i]),"formula":row,"predictions":p,"uncertainty":u,"cost_yuan_mu":cost,"history":pd.DataFrame({"iteration":np.arange(1,len(ys)+1),"utility":ys})}
