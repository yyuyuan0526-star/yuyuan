# 凝策 AgriGel-Opt

第一版概念验证：
- NASA POWER：气温、湿度、降水、太阳辐射、风速
- SoilGrids：pH、SOC、砂/粉/黏粒、容重（仅背景先验）
- GPR + XGBoost：水凝胶性能多目标预测
- Gaussian Process Bayesian Optimization + Expected Improvement：配方/用量寻优
- Streamlit：网页版交互

## 运行

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## 正式数据要求

请用 `data/real_trials_template.csv` 为模板。每一行必须是一条“独立试验单元/重复”，而不是一张汇总表。

正式建模前至少做到：
1. 靖安、玉山使用相同字段和采样时间点；
2. 用精确试验地 GPS，不用县城坐标；
3. 土壤 pH、EC、有机质、速效N/P/K、质地、初始含水率用现场实测；
4. 每个配方至少3个独立重复；
5. 记录灌水量、肥料量、生育期、产量、糖度/品质、病害指标；
6. PPT里现有G1-G6结果的组号/指标口径先统一，再进入训练集。

## 注意

`demo_data.py` 生成的是“合成演示数据”，目的只是让网页和模型立即跑通。
它不能作为论文、比赛或产品配方依据。
