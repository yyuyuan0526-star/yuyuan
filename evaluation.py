from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import KFold
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_percentage_error
from xgboost import XGBRegressor
from modeling import NUMERIC_FEATURES, CATEGORICAL_FEATURES, TARGETS


def _preprocessor():
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
    ])


def _safe_mape(y, p):
    y=np.asarray(y,float); p=np.asarray(p,float)
    mask=np.abs(y)>1e-6
    if mask.sum()<2:
        return np.nan
    return float(mean_absolute_percentage_error(y[mask],p[mask])*100.0)


def evaluate_cv(df, random_state=42):
    clean=df.dropna(subset=TARGETS).copy()
    if len(clean)<12:
        raise ValueError("至少需要12条完整记录。")
    X=clean[NUMERIC_FEATURES+CATEGORICAL_FEATURES]
    rows=[]; points=[]
    k=min(5,max(3,len(clean)//10))
    for target in TARGETS:
        y=clean[target].astype(float).values
        pg=np.full(len(clean),np.nan); px=np.full(len(clean),np.nan)
        cv=KFold(n_splits=k,shuffle=True,random_state=random_state)
        for tr,va in cv.split(X):
            pre=_preprocessor(); ztr=pre.fit_transform(X.iloc[tr]); zva=pre.transform(X.iloc[va])
            gpr=GaussianProcessRegressor(kernel=ConstantKernel(1.0)*Matern(nu=2.5)+WhiteKernel(0.5),normalize_y=True,random_state=random_state)
            xgb=XGBRegressor(n_estimators=180,max_depth=3,learning_rate=0.04,subsample=0.85,colsample_bytree=0.85,objective="reg:squarederror",random_state=random_state,n_jobs=2)
            gpr.fit(ztr,y[tr]); xgb.fit(ztr,y[tr])
            pg[va]=gpr.predict(zva); px[va]=xgb.predict(zva)
        rg=mean_squared_error(y,pg)**0.5; rx=mean_squared_error(y,px)**0.5
        ig,ix=1/max(rg,1e-6),1/max(rx,1e-6); wg=ig/(ig+ix); wx=1-wg
        pe=wg*pg+wx*px
        rows.append({
            "target":target,
            "RMSE":float(mean_squared_error(y,pe)**0.5),
            "R2":float(r2_score(y,pe)),
            "MAPE_%":_safe_mape(y,pe),
            "GPR_weight":wg,
            "XGB_weight":wx,
        })
        points.extend([{"target":target,"actual":float(a),"predicted":float(b)} for a,b in zip(y,pe)])
    return pd.DataFrame(rows), pd.DataFrame(points)
