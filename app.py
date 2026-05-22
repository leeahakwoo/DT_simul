import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import html

st.set_page_config(
    page_title="Virtual Factory Digital Twin",
    page_icon="🏭",
    layout="wide",
)

# ------------------------------------------------------------
# Sample Data
# ------------------------------------------------------------

@st.cache_data
def generate_factory_data(hours=168, seed=42):
    np.random.seed(seed)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    timestamps = [now - timedelta(hours=hours - i - 1) for i in range(hours)]

    machines = ["Press-01", "CNC-02", "Robot-03", "Conveyor-04", "Packing-05", "Inspection-06"]
    records = []

    for machine in machines:
        base_temp = np.random.uniform(55, 68)
        base_vibration = np.random.uniform(0.25, 0.75)
        base_power = np.random.uniform(60, 130)

        for i, ts in enumerate(timestamps):
            degradation = max(0, i - hours * 0.65) / (hours * 0.35)

            temp = base_temp + np.random.normal(0, 2.5) + degradation * np.random.uniform(12, 25)
            vibration = base_vibration + np.random.normal(0, 0.06) + degradation * np.random.uniform(0.5, 1.3)
            power = base_power + np.random.normal(0, 5) + degradation * np.random.uniform(15, 38)
            defect_rate = max(0.3, np.random.normal(1.8, 0.45) + degradation * np.random.uniform(2, 5))
            production = max(0, np.random.normal(100, 7) - degradation * np.random.uniform(8, 24))

            risk_score = (
                max(0, temp - 75) * 1.3
                + max(0, vibration - 1.0) * 36
                + max(0, power - 130) * 0.45
                + max(0, defect_rate - 3.5) * 5
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

            records.append(
                {
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
                }
            )

    return pd.DataFrame(records)


df = generate_factory_data()

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------

st.sidebar.header("분석 조건")
selected_machine = st.sidebar.selectbox("설비 선택", sorted(df["machine"].unique()))
selected_hours = st.sidebar.slider("최근 분석 기간(시간)", 24, 168, 72, step=24)

filtered = df[
    (df["machine"] == selected_machine)
    & (df["timestamp"] >= df["timestamp"].max() - timedelta(hours=selected_hours))
].copy()

latest = filtered.sort_values("timestamp").iloc[-1]

status_df = (
    df.sort_values("timestamp")
    .groupby("machine")
    .tail(1)
    .reset_index(drop=True)
)

avg_defect = filtered["defect_rate"].mean()
total_downtime = filtered["downtime_hours"].sum()
availability = max(0, 1 - total_downtime / selected_hours)
performance = min(1, filtered["production_qty"].mean() / 100)
quality = max(0, 1 - avg_defect / 100)
oee = availability * performance * quality * 100

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

st.title("🏭 가상 공장 디지털 트윈 대시보드")
st.caption("AI 기반 예지보전 · 운영 KPI · ESG · ROI 분석")

status_icon = {
    "정상": "🟢",
    "주의": "🟡",
    "위험": "🔴",
}

st.subheader(f"{selected_machine} 현재 상태: {status_icon[latest['status']]} {latest['status']}")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("고장 확률", f"{latest['failure_probability']}%")
c2.metric("온도", f"{latest['temperature']} ℃")
c3.metric("진동", f"{latest['vibration']} mm/s")
c4.metric("전력 사용", f"{latest['power_kwh']} kWh")
c5.metric("불량률", f"{latest['defect_rate']}%")

# ------------------------------------------------------------
# Digital Twin Visualization
# ------------------------------------------------------------

st.divider()
st.subheader("① 가상 공장 디지털 트윈 관제 화면")

# 방법 1: 온라인 이미지 URL 사용
# 원하는 공장 이미지 URL로 교체 가능
factory_bg_url = "https://images.unsplash.com/photo-1581093458791-9d42cc81a6d5?auto=format&fit=crop&w=1600&q=80"

# 방법 2: 직접 업로드한 이미지 사용
uploaded_bg = st.file_uploader(
    "공장 배경 이미지 업로드",
    type=["png", "jpg", "jpeg"],
    help="스크린샷처럼 보이게 하려면 공장 내부 또는 3D 공장 렌더링 이미지를 업로드하세요.",
)

if uploaded_bg is not None:
    import base64

    encoded = base64.b64encode(uploaded_bg.read()).decode()
    factory_bg = f"data:image/png;base64,{encoded}"
else:
    factory_bg = factory_bg_url

status_color = {
    "정상": "#22c55e",
    "주의": "#facc15",
    "위험": "#ef4444",
}

# 이미지 위 마커 위치
# 배경 이미지를 바꾸면 이 좌표만 조정하면 됩니다.
machine_positions = {
    "Press-01": (21, 68),
    "CNC-02": (38, 57),
    "Robot-03": (53, 63),
    "Conveyor-04": (67, 51),
    "Packing-05": (78, 39),
    "Inspection-06": (32, 43),
}

marker_html = ""

for _, row in status_df.iterrows():
    machine = row["machine"]
    left, top = machine_positions.get(machine, (50, 50))
    color = status_color[row["status"]]

    marker_html += f"""
    <div class="dt-marker" style="left:{left}%; top:{top}%; border-color:{color}; box-shadow:0 0 18px {color};">
        <div class="dt-marker-core" style="background:{color};"></div>
        <div class="dt-tooltip">
            <b>{html.escape(machine)}</b><br>
            상태: {html.escape(row["status"])}<br>
            고장확률: {row["failure_probability"]}%<br>
            온도: {row["temperature"]}℃<br>
            진동: {row["vibration"]} mm/s<br>
            전력: {row["power_kwh"]} kWh
        </div>
    </div>
    """

danger_count = len(status_df[status_df["status"] == "위험"])
warning_count = len(status_df[status_df["status"] == "주의"])
normal_count = len(status_df[status_df["status"] == "정상"])

dashboard_html = f"""
<style>
.dt-shell {{
    display: grid;
    grid-template-columns: 250px 1fr;
    min-height: 640px;
    border-radius: 10px;
    overflow: hidden;
    background: #020617;
    border: 1px solid rgba(148, 163, 184, 0.35);
}}

.dt-side {{
    background: rgba(2, 6, 23, 0.94);
    color: white;
    padding: 14px;
    border-right: 1px solid rgba(148, 163, 184, 0.25);
}}

.dt-brand {{
    font-size: 13px;
    font-weight: 800;
    color: #38bdf8;
    margin-bottom: 16px;
}}

.dt-panel-title {{
    font-size: 13px;
    font-weight: 800;
    color: #e5e7eb;
    margin: 14px 0 8px;
}}

.dt-progress-row {{
    margin-bottom: 8px;
}}

.dt-progress-label {{
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    margin-bottom: 3px;
}}

.dt-progress-track {{
    height: 15px;
    background: rgba(255,255,255,0.12);
    border-radius: 6px;
    overflow: hidden;
}}

.dt-progress-fill {{
    height: 15px;
}}

.dt-mini-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 7px;
}}

.dt-mini-card {{
    background: rgba(15, 23, 42, 0.92);
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 8px;
    padding: 9px 6px;
    text-align: center;
}}

.dt-mini-num {{
    font-size: 16px;
    font-weight: 900;
}}

.dt-mini-label {{
    font-size: 10px;
    color: #cbd5e1;
}}

.dt-gauge {{
    margin-top: 10px;
    height: 110px;
    border-radius: 110px 110px 0 0;
    background:
        conic-gradient(from 270deg, #22d3ee 0deg, #22d3ee 108deg, rgba(255,255,255,0.12) 108deg, rgba(255,255,255,0.12) 180deg);
    position: relative;
    overflow: hidden;
}}

.dt-gauge::after {{
    content: "";
    position: absolute;
    left: 18px;
    right: 18px;
    bottom: 0;
    height: 72px;
    background: #020617;
    border-radius: 80px 80px 0 0;
}}

.dt-gauge-value {{
    position: relative;
    margin-top: -48px;
    text-align: center;
    font-size: 22px;
    font-weight: 900;
    color: white;
    z-index: 2;
}}

.dt-main {{
    position: relative;
    min-height: 640px;
    background-image:
        linear-gradient(180deg, rgba(2,6,23,0.12), rgba(2,6,23,0.55)),
        url("{factory_bg}");
    background-size: cover;
    background-position: center;
}}

.dt-topbar {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 82px;
    background: rgba(2, 6, 23, 0.78);
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    z-index: 3;
}}

.dt-kpi {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: white;
    border-left: 1px solid rgba(148, 163, 184, 0.18);
}}

.dt-ring {{
    width: 48px;
    height: 48px;
    border-radius: 50%;
    border: 4px solid #22d3ee;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #67e8f9;
    font-size: 12px;
    font-weight: 800;
}}

.dt-kpi-label {{
    font-size: 12px;
    color: #cbd5e1;
    font-weight: 700;
}}

.dt-kpi-value {{
    font-size: 25px;
    font-weight: 900;
}}

.dt-marker {{
    position: absolute;
    width: 38px;
    height: 38px;
    margin-left: -19px;
    margin-top: -19px;
    border: 3px solid;
    border-radius: 50%;
    background: rgba(15, 23, 42, 0.78);
    z-index: 5;
    cursor: pointer;
}}

.dt-marker-core {{
    width: 16px;
    height: 16px;
    border-radius: 50%;
    margin: 8px auto;
}}

.dt-tooltip {{
    display: none;
    position: absolute;
    left: 46px;
    top: -24px;
    width: 205px;
    background: rgba(2, 6, 23, 0.94);
    color: white;
    border-radius: 8px;
    padding: 10px;
    font-size: 12px;
    line-height: 1.45;
    border: 1px solid rgba(148, 163, 184, 0.35);
}}

.dt-marker:hover .dt-tooltip {{
    display: block;
}}

.dt-bottom-strip {{
    position: absolute;
    left: 20px;
    right: 20px;
    bottom: 18px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    z-index: 3;
}}

.dt-bottom-card {{
    background: rgba(2, 6, 23, 0.82);
    color: white;
    border: 1px solid rgba(148, 163, 184, 0.35);
    border-radius: 8px;
    padding: 12px;
}}

.dt-bottom-label {{
    font-size: 12px;
    color: #cbd5e1;
}}

.dt-bottom-value {{
    font-size: 21px;
    font-weight: 900;
}}

@media (max-width: 900px) {{
    .dt-shell {{
        grid-template-columns: 1fr;
    }}

    .dt-topbar {{
        grid-template-columns: repeat(2, 1fr);
        height: 150px;
    }}

    .dt-main {{
        min-height: 720px;
    }}

    .dt-bottom-strip {{
        grid-template-columns: repeat(2, 1fr);
    }}
}}
</style>

<div class="dt-shell">
    <div class="dt-side">
        <div class="dt-brand">Metanet Meta Factory</div>

        <div class="dt-panel-title">Production / Target</div>

        <div class="dt-progress-row">
            <div class="dt-progress-label"><span>Assembly Shop1</span><b>88%</b></div>
            <div class="dt-progress-track"><div class="dt-progress-fill" style="width:88%; background:#06b6d4;"></div></div>
        </div>

        <div class="dt-progress-row">
            <div class="dt-progress-label"><span>Assembly Shop2</span><b>72%</b></div>
            <div class="dt-progress-track"><div class="dt-progress-fill" style="width:72%; background:#ef4444;"></div></div>
        </div>

        <div class="dt-progress-row">
            <div class="dt-progress-label"><span>Processing Shop</span><b>84%</b></div>
            <div class="dt-progress-track"><div class="dt-progress-fill" style="width:84%; background:#3b82f6;"></div></div>
        </div>

        <div class="dt-progress-row">
            <div class="dt-progress-label"><span>Part Shop</span><b>61%</b></div>
            <div class="dt-progress-track"><div class="dt-progress-fill" style="width:61%; background:#f59e0b;"></div></div>
        </div>

        <div class="dt-panel-title">Warehouse Capacity</div>
        <div class="dt-mini-grid">
            <div class="dt-mini-card"><div class="dt-mini-num" style="color:#ef4444;">{danger_count}</div><div class="dt-mini-label">위험</div></div>
            <div class="dt-mini-card"><div class="dt-mini-num" style="color:#facc15;">{warning_count}</div><div class="dt-mini-label">주의</div></div>
            <div class="dt-mini-card"><div class="dt-mini-num" style="color:#22c55e;">{normal_count}</div><div class="dt-mini-label">정상</div></div>
        </div>

        <div class="dt-panel-title">Product Yield</div>
        <div class="dt-gauge"></div>
        <div class="dt-gauge-value">{100 - avg_defect:.1f}%</div>

        <div class="dt-panel-title">Quality Defect Rate</div>
        <div class="dt-gauge"></div>
        <div class="dt-gauge-value">{avg_defect:.2f}%</div>
    </div>

    <div class="dt-main">
        <div class="dt-topbar">
            <div class="dt-kpi">
                <div class="dt-ring">{danger_count}</div>
                <div>
                    <div class="dt-kpi-label">FACILITY</div>
                    <div class="dt-kpi-value">{oee:.1f}%</div>
                </div>
            </div>

            <div class="dt-kpi">
                <div class="dt-ring">{warning_count}</div>
                <div>
                    <div class="dt-kpi-label">CONVEYOR</div>
                    <div class="dt-kpi-value">{status_df["failure_probability"].mean():.1f}%</div>
                </div>
            </div>

            <div class="dt-kpi">
                <div class="dt-ring">2</div>
                <div>
                    <div class="dt-kpi-label">AGV</div>
                    <div class="dt-kpi-value">84.0%</div>
                </div>
            </div>

            <div class="dt-kpi">
                <div class="dt-ring">1/1</div>
                <div>
                    <div class="dt-kpi-label">WORKER</div>
                    <div class="dt-kpi-value">99.2%</div>
                </div>
            </div>
        </div>

        {marker_html}

        <div class="dt-bottom-strip">
            <div class="dt-bottom-card">
                <div class="dt-bottom-label">Selected Machine</div>
                <div class="dt-bottom-value">{html.escape(selected_machine)}</div>
            </div>
            <div class="dt-bottom-card">
                <div class="dt-bottom-label">Failure Probability</div>
                <div class="dt-bottom-value">{latest["failure_probability"]}%</div>
            </div>
            <div class="dt-bottom-card">
                <div class="dt-bottom-label">Temperature</div>
                <div class="dt-bottom-value">{latest["temperature"]}℃</div>
            </div>
            <div class="dt-bottom-card">
                <div class="dt-bottom-label">Vibration</div>
                <div class="dt-bottom-value">{latest["vibration"]}</div>
            </div>
        </div>
    </div>
</div>
"""

st.markdown(dashboard_html, unsafe_allow_html=True)

st.caption("배경 이미지를 업로드하면 해당 이미지 위에 설비 마커와 KPI가 오버레이됩니다.")

# ------------------------------------------------------------
# Table
# ------------------------------------------------------------

st.write("설비별 최신 상태")
st.dataframe(
    status_df[
        [
            "machine",
            "status",
            "failure_probability",
            "temperature",
            "vibration",
            "power_kwh",
            "defect_rate",
        ]
    ].sort_values("failure_probability", ascending=False),
    use_container_width=True,
    hide_index=True,
)
