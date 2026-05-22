import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ------------------------------------------------------------
# Virtual Factory Digital Twin Dashboard
# Topic: AI-based Predictive Maintenance for a Virtual Factory
# ------------------------------------------------------------

st.set_page_config(
    page_title="Virtual Factory Digital Twin",
    layout="wide",
)

st.title("🏭 가상 공장 디지털 트윈 대시보드")
st.caption("AI 기반 예지보전 · 운영 KPI · ESG · ROI 분석")

# ------------------------------------------------------------
# 1. Data Generation
# ------------------------------------------------------------

@st.cache_data
def generate_factory_data(hours=168, seed=42):
    np.random.seed(seed)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    timestamps = [now - timedelta(hours=hours - i) for i in range(hours)]

    machines = ["Press-01", "CNC-02", "Robot-03", "Conveyor-04"]
    records = []

    for machine in machines:
        base_temp = np.random.uniform(58, 68)
        base_vibration = np.random.uniform(0.3, 0.7)
        base_power = np.random.uniform(80, 120)

        for i, ts in enumerate(timestamps):
            # Simulate gradual degradation near the end
            degradation = max(0, i - hours * 0.65) / (hours * 0.35)

            temp = base_temp + np.random.normal(0, 3) + degradation * np.random.uniform(15, 28)
            vibration = base_vibration + np.random.normal(0, 0.08) + degradation * np.random.uniform(0.6, 1.4)
            power = base_power + np.random.normal(0, 6) + degradation * np.random.uniform(20, 45)

            defect_rate = max(0.5, np.random.normal(2.0, 0.5) + degradation * np.random.uniform(2, 5))
            production = max(0, np.random.normal(100, 8) - degradation * np.random.uniform(8, 25))

            risk_score = (
                max(0, temp - 75) * 1.2
                + max(0, vibration - 1.0) * 35
                + max(0, power - 130) * 0.5
            )
            failure_probability = min(100, risk_score)

            if failure_probability >= 70:
                status = "위험"
                downtime = np.random.uniform(1.0, 3.0)
            elif failure_probability >= 40:
                status = "주의"
                downtime = np.random.uniform(0.2, 1.0)
            else:
                status = "정상"
                downtime = np.random.uniform(0.0, 0.2)

            records.append({
                "timestamp": ts,
                "machine": machine,
                "temperature": round(temp, 2),
                "vibration": round(max(0, vibration), 2),
                "power_kwh": round(max(0, power), 2),
                "defect_rate": round(defect_rate, 2),
                "production_qty": round(production, 0),
                "failure_probability": round(failure_probability, 1),
                "status": status,
                "downtime_hours": round(downtime, 2),
            })

    return pd.DataFrame(records)


df = generate_factory_data()

# ------------------------------------------------------------
# 2. Sidebar Controls
# ------------------------------------------------------------

st.sidebar.header("분석 조건")
selected_machine = st.sidebar.selectbox("설비 선택", sorted(df["machine"].unique()))
selected_hours = st.sidebar.slider("최근 분석 기간(시간)", 24, 168, 72, step=24)

filtered = df[
    (df["machine"] == selected_machine)
    & (df["timestamp"] >= df["timestamp"].max() - timedelta(hours=selected_hours))
].copy()

latest = filtered.sort_values("timestamp").iloc[-1]

# ------------------------------------------------------------
# 3. Status Header
# ------------------------------------------------------------

status_icon = {
    "정상": "🟢",
    "주의": "🟡",
    "위험": "🔴",
}

st.subheader(f"{selected_machine} 현재 상태: {status_icon[latest['status']]} {latest['status']}")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("고장 확률", f"{latest['failure_probability']}%")
col2.metric("온도", f"{latest['temperature']} ℃")
col3.metric("진동", f"{latest['vibration']} mm/s")
col4.metric("전력 사용", f"{latest['power_kwh']} kWh")
col5.metric("불량률", f"{latest['defect_rate']}%")

# ------------------------------------------------------------
# 4. Digital Twin Visualization - Visual Factory Control Room
# ------------------------------------------------------------

st.divider()
st.subheader("① 가상 공장 3D 스타일 디지털 트윈")

status_df = df.sort_values("timestamp").groupby("machine").tail(1)[
    ["machine", "status", "failure_probability", "temperature", "vibration", "power_kwh"]
].reset_index(drop=True)

status_color = {
    "정상": "#2ecc71",
    "주의": "#f1c40f",
    "위험": "#e74c3c",
}

machine_positions = {
    "Press-01": (18, 68),
    "CNC-02": (40, 48),
    "Robot-03": (62, 60),
    "Conveyor-04": (78, 38),
}

marker_html = ""
for _, row in status_df.iterrows():
    left, top = machine_positions[row["machine"]]
    color = status_color[row["status"]]
    marker_html += f"""
    <div class="machine-marker" style="left:{left}%; top:{top}%; border-color:{color}; box-shadow:0 0 18px {color};">
        <div class="marker-dot" style="background:{color};"></div>
        <div class="marker-label">
            <b>{row['machine']}</b><br>
            상태: {row['status']}<br>
            고장확률: {row['failure_probability']}%<br>
            온도: {row['temperature']}℃ / 진동: {row['vibration']}
        </div>
    </div>
    """

factory_html = f"""
<style>
.factory-wrap {{
    display: grid;
    grid-template-columns: 260px 1fr;
    gap: 16px;
    margin-top: 12px;
}}
.left-panel {{
    background: linear-gradient(180deg, #0c1326, #151f36);
    color: white;
    border-radius: 16px;
    padding: 16px;
    border: 1px solid rgba(255,255,255,0.15);
}}
.panel-title {{
    font-size: 15px;
    font-weight: 700;
    margin: 12px 0 8px 0;
}}
.progress-row {{
    margin-bottom: 8px;
}}
.progress-label {{
    display:flex;
    justify-content:space-between;
    font-size:12px;
    margin-bottom:3px;
}}
.progress-bg {{
    height: 14px;
    border-radius: 8px;
    overflow: hidden;
    background: rgba(255,255,255,0.15);
}}
.progress-bar {{
    height: 14px;
    border-radius: 8px;
}}
.gauge-card {{
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 8px;
    font-size: 13px;
}}
.factory-scene {{
    position: relative;
    height: 520px;
    overflow: hidden;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.12);
    background:
        linear-gradient(180deg, rgba(10,18,35,0.1), rgba(10,18,35,0.55)),
        repeating-linear-gradient(90deg, rgba(255,255,255,0.06) 0 2px, transparent 2px 90px),
        repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 2px, transparent 2px 70px),
        linear-gradient(135deg, #27384f 0%, #6f7d88 45%, #1f2838 100%);
}}
.ceiling {{
    position:absolute;
    top:0; left:0; right:0;
    height:100px;
    background: repeating-linear-gradient(110deg, rgba(255,255,255,0.18) 0 7px, transparent 7px 42px);
    opacity:0.45;
}}
.floor {{
    position:absolute;
    left:-5%; right:-5%; bottom:-20px;
    height:330px;
    background: linear-gradient(160deg, #212a35, #48515c);
    transform: skewY(-8deg);
    border-top: 4px solid rgba(255,255,255,0.2);
}}
.line {{
    position:absolute;
    height: 14px;
    background: #f1c40f;
    opacity:0.9;
    transform: rotate(-8deg);
    border-radius:8px;
}}
.line.a {{ left: 10%; top: 74%; width: 80%; }}
.line.b {{ left: 25%; top: 55%; width: 60%; }}
.machine-box {{
    position:absolute;
    width:95px;
    height:62px;
    background: linear-gradient(145deg, #e8edf4, #9aa7b4);
    border: 1px solid #dbe4ef;
    border-radius: 8px;
    box-shadow: 14px 18px 22px rgba(0,0,0,0.35);
    transform: skewY(-8deg);
}}
.machine-box::after {{
    content:"";
    position:absolute;
    right:-20px; top:10px;
    width:20px; height:52px;
    background:#778391;
    transform: skewY(30deg);
    border-radius: 0 6px 6px 0;
}}
.machine-marker {{
    position:absolute;
    width: 38px;
    height: 38px;
    margin-left:-19px;
    margin-top:-19px;
    border: 3px solid;
    border-radius: 50%;
    background: rgba(9,18,32,0.72);
    z-index:5;
}}
.marker-dot {{
    width: 16px;
    height: 16px;
    border-radius: 50%;
    margin: 8px auto;
}}
.marker-label {{
    display:none;
    position:absolute;
    left:44px;
    top:-20px;
    width: 210px;
    background: rgba(8,14,28,0.94);
    color:white;
    border-radius: 12px;
    padding: 10px;
    font-size: 12px;
    line-height:1.45;
    border: 1px solid rgba(255,255,255,0.2);
}}
.machine-marker:hover .marker-label {{
    display:block;
}}
.top-kpis {{
    position:absolute;
    top:16px; left:20px; right:20px;
    display:grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    z-index:4;
}}
.kpi-pill {{
    background: rgba(4,10,22,0.78);
    color:white;
    border:1px solid rgba(0,234,255,0.35);
    border-radius: 14px;
    padding: 12px;
    text-align:center;
}}
.kpi-pill .num {{
    font-size: 24px;
    font-weight:800;
}}
</style>

<div class="factory-wrap">
  <div class="left-panel">
    <div class="panel-title">Production / Target</div>
    <div class="progress-row"><div class="progress-label"><span>Assembly Shop1</span><b>88%</b></div><div class="progress-bg"><div class="progress-bar" style="width:88%; background:#13c2c2;"></div></div></div>
    <div class="progress-row"><div class="progress-label"><span>Assembly Shop2</span><b>72%</b></div><div class="progress-bg"><div class="progress-bar" style="width:72%; background:#e74c3c;"></div></div></div>
    <div class="progress-row"><div class="progress-label"><span>Processing Shop</span><b>84%</b></div><div class="progress-bg"><div class="progress-bar" style="width:84%; background:#3498db;"></div></div></div>
    <div class="progress-row"><div class="progress-label"><span>Part Shop</span><b>61%</b></div><div class="progress-bg"><div class="progress-bar" style="width:61%; background:#f1c40f;"></div></div></div>

    <div class="panel-title">Warehouse Capacity</div>
    <div class="gauge-card">🚨 위험 설비: {len(status_df[status_df['status']=='위험'])} EA</div>
    <div class="gauge-card">⚠️ 주의 설비: {len(status_df[status_df['status']=='주의'])} EA</div>
    <div class="gauge-card">✅ 정상 설비: {len(status_df[status_df['status']=='정상'])} EA</div>

    <div class="panel-title">Product Yield</div>
    <div class="gauge-card">수율: {100 - avg_defect:.1f}%</div>
    <div class="gauge-card">불량률: {avg_defect:.1f}%</div>
  </div>

  <div class="factory-scene">
    <div class="ceiling"></div>
    <div class="floor"></div>
    <div class="line a"></div>
    <div class="line b"></div>
    <div class="top-kpis">
      <div class="kpi-pill"><div>FACILITY</div><div class="num">{oee:.1f}%</div></div>
      <div class="kpi-pill"><div>CONVEYOR</div><div class="num">{status_df['failure_probability'].mean():.1f}%</div></div>
      <div class="kpi-pill"><div>AGV</div><div class="num">84.0%</div></div>
      <div class="kpi-pill"><div>WORKER</div><div class="num">99.2%</div></div>
    </div>
    <div class="machine-box" style="left:12%; top:64%;"></div>
    <div class="machine-box" style="left:26%; top:58%;"></div>
    <div class="machine-box" style="left:40%; top:50%;"></div>
    <div class="machine-box" style="left:56%; top:55%;"></div>
    <div class="machine-box" style="left:70%; top:45%;"></div>
    <div class="machine-box" style="left:80%; top:62%;"></div>
    {marker_html}
  </div>
</div>
"""

st.markdown(factory_html, unsafe_allow_html=True)
st.caption("마커에 마우스를 올리면 설비별 센서 상태와 고장확률을 확인할 수 있습니다.")

# ------------------------------------------------------------
# 5. Sensor Trend Charts
# ------------------------------------------------------------

st.divider()
st.subheader("② 센서 데이터 추이")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.write("온도 추이")
    fig, ax = plt.subplots()
    ax.plot(filtered["timestamp"], filtered["temperature"])
    ax.axhline(85, linestyle="--")
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature (℃)")
    plt.xticks(rotation=30)
    st.pyplot(fig)

with chart_col2:
    st.write("진동 추이")
    fig, ax = plt.subplots()
    ax.plot(filtered["timestamp"], filtered["vibration"])
    ax.axhline(1.5, linestyle="--")
    ax.set_xlabel("Time")
    ax.set_ylabel("Vibration (mm/s)")
    plt.xticks(rotation=30)
    st.pyplot(fig)

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    st.write("전력 사용량 추이")
    fig, ax = plt.subplots()
    ax.plot(filtered["timestamp"], filtered["power_kwh"])
    ax.set_xlabel("Time")
    ax.set_ylabel("Power (kWh)")
    plt.xticks(rotation=30)
    st.pyplot(fig)

with chart_col4:
    st.write("AI 고장 확률 추이")
    fig, ax = plt.subplots()
    ax.plot(filtered["timestamp"], filtered["failure_probability"])
    ax.axhline(70, linestyle="--")
    ax.set_xlabel("Time")
    ax.set_ylabel("Failure Probability (%)")
    plt.xticks(rotation=30)
    st.pyplot(fig)

# ------------------------------------------------------------
# 6. Operation KPI
# ------------------------------------------------------------

st.divider()
st.subheader("③ 운영 KPI 분석")

total_production = filtered["production_qty"].sum()
avg_defect = filtered["defect_rate"].mean()
total_downtime = filtered["downtime_hours"].sum()
avg_failure_risk = filtered["failure_probability"].mean()

# Simplified OEE formula for educational use
availability = max(0, 1 - total_downtime / selected_hours)
performance = min(1, filtered["production_qty"].mean() / 100)
quality = max(0, 1 - avg_defect / 100)
oee = availability * performance * quality * 100

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("총 생산량", f"{total_production:,.0f} EA")
kpi2.metric("평균 불량률", f"{avg_defect:.2f}%")
kpi3.metric("누적 다운타임", f"{total_downtime:.1f} h")
kpi4.metric("OEE", f"{oee:.1f}%")

st.info(
    "OEE는 가동률, 성능, 품질을 종합한 설비종합효율 지표입니다. "
    "본 대시보드는 교육용 단순화 산식을 사용합니다."
)

# ------------------------------------------------------------
# 7. ESG Impact
# ------------------------------------------------------------

st.divider()
st.subheader("④ ESG 효과 분석")

baseline_energy = filtered["power_kwh"].sum() * 1.12
actual_energy = filtered["power_kwh"].sum()
energy_saving = baseline_energy - actual_energy
carbon_factor = 0.459  # kgCO2 per kWh, illustrative value
carbon_reduction = energy_saving * carbon_factor

esg1, esg2, esg3 = st.columns(3)
esg1.metric("기준 에너지", f"{baseline_energy:,.0f} kWh")
esg2.metric("절감 에너지", f"{energy_saving:,.0f} kWh")
esg3.metric("탄소 감축 추정", f"{carbon_reduction:,.0f} kgCO₂")

# ------------------------------------------------------------
# 8. ROI Analysis
# ------------------------------------------------------------

st.divider()
st.subheader("⑤ ROI 분석")

investment_cost = st.number_input("초기 구축비(원)", value=50_000_000, step=5_000_000)
downtime_cost_per_hour = st.number_input("다운타임 1시간 손실비용(원)", value=1_500_000, step=100_000)
maintenance_saving = st.number_input("연간 유지보수 절감액(원)", value=20_000_000, step=1_000_000)
energy_cost_per_kwh = st.number_input("전력 단가(원/kWh)", value=150, step=10)

before_downtime_year = 420
after_downtime_year = 240
downtime_saving = (before_downtime_year - after_downtime_year) * downtime_cost_per_hour
energy_saving_year = energy_saving * (8760 / selected_hours) * energy_cost_per_kwh
annual_benefit = downtime_saving + maintenance_saving + energy_saving_year
roi = (annual_benefit - investment_cost) / investment_cost * 100
payback = investment_cost / annual_benefit if annual_benefit > 0 else np.nan

roi1, roi2, roi3 = st.columns(3)
roi1.metric("연간 절감효과", f"{annual_benefit:,.0f} 원")
roi2.metric("ROI", f"{roi:.1f}%")
roi3.metric("투자회수기간", f"{payback:.2f} 년")

roi_df = pd.DataFrame({
    "구분": ["다운타임 절감", "유지보수 절감", "에너지 절감"],
    "금액": [downtime_saving, maintenance_saving, energy_saving_year],
})

st.bar_chart(roi_df.set_index("구분"))

# ------------------------------------------------------------
# 9. Decision Recommendation
# ------------------------------------------------------------

st.divider()
st.subheader("⑥ 운영 의사결정 제안")

if latest["failure_probability"] >= 70:
    st.error(
        "AI 분석 결과, 설비 고장 위험이 높습니다. 즉시 예방정비를 수행하고 생산계획을 조정하는 것이 필요합니다."
    )
elif latest["failure_probability"] >= 40:
    st.warning(
        "설비 상태가 주의 단계입니다. 다음 교대조 이전 점검을 권장합니다."
    )
else:
    st.success(
        "설비 상태가 안정적입니다. 현재 운영 조건을 유지하되 센서 데이터를 지속 모니터링합니다."
    )

st.markdown(
    """
    ### 보고서에 쓸 핵심 해석
    - 디지털 트윈은 현실 설비의 상태를 가상 환경에 반영하여 운영관리자의 의사결정을 지원한다.
    - AI 분석은 고장 가능성을 사전에 탐지하여 다운타임과 불량률을 줄인다.
    - 에너지 사용량 감소와 탄소배출 감축을 통해 ESG와 수익성은 상호보완적으로 작동할 수 있다.
    - 단, AI 모델의 예측 결과는 최종 의사결정을 대체하기보다 관리자 판단을 보조하는 역할로 보는 것이 적절하다.
    """
)

st.caption("※ 본 데이터와 수치는 대학원 과제용 가상 시뮬레이션 예시입니다.")

# ------------------------------------------------------------
# requirements.txt
# ------------------------------------------------------------
# 아래 내용을 requirements.txt 파일로 저장하세요.
#
# streamlit
# pandas
# numpy
# matplotlib
