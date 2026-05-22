import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import html

# ------------------------------------------------------------
# Virtual Factory Digital Twin Dashboard
# ------------------------------------------------------------

st.set_page_config(
    page_title="Virtual Factory Digital Twin",
    page_icon="🏭",
    layout="wide",
)

plt.rcParams["axes.unicode_minus"] = False

# ------------------------------------------------------------
# Style
# ------------------------------------------------------------

st.markdown(
    """
    <style>
    .main {
        background: #f5f7fb;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    .metric-card {
        background: white;
        border: 1px solid #e5e9f2;
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
    }

    .metric-label {
        color: #64748b;
        font-size: 13px;
        margin-bottom: 4px;
    }

    .metric-value {
        font-size: 24px;
        font-weight: 800;
        color: #0f172a;
    }

    .metric-sub {
        color: #64748b;
        font-size: 12px;
    }

    .section-title {
        font-size: 20px;
        font-weight: 800;
        color: #111827;
        margin: 18px 0 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Data Generation
# ------------------------------------------------------------

@st.cache_data
def generate_factory_data(hours=168, seed=42):
    np.random.seed(seed)

    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    timestamps = [now - timedelta(hours=hours - i - 1) for i in range(hours)]

    machine_specs = {
        "Press-01": {"temp": (62, 69), "vibration": (0.45, 0.75), "power": (105, 130)},
        "CNC-02": {"temp": (56, 64), "vibration": (0.25, 0.55), "power": (80, 105)},
        "Robot-03": {"temp": (52, 60), "vibration": (0.20, 0.45), "power": (55, 90)},
        "Conveyor-04": {"temp": (48, 58), "vibration": (0.35, 0.65), "power": (45, 75)},
    }

    records = []

    for machine, spec in machine_specs.items():
        base_temp = np.random.uniform(*spec["temp"])
        base_vibration = np.random.uniform(*spec["vibration"])
        base_power = np.random.uniform(*spec["power"])
        degradation_start = np.random.uniform(0.55, 0.75)

        for i, ts in enumerate(timestamps):
            ratio = i / max(1, hours - 1)
            shift_effect = 1 + 0.08 * np.sin((i % 24) / 24 * 2 * np.pi)
            degradation = max(0, ratio - degradation_start) / max(0.01, 1 - degradation_start)

            temp = base_temp + np.random.normal(0, 2.6) + degradation * np.random.uniform(14, 26)
            vibration = base_vibration + np.random.normal(0, 0.07) + degradation * np.random.uniform(0.55, 1.35)
            power = (base_power + np.random.normal(0, 5.5) + degradation * np.random.uniform(18, 40)) * shift_effect

            defect_rate = max(0.2, np.random.normal(1.8, 0.45) + degradation * np.random.uniform(2.0, 5.2))
            production = max(0, np.random.normal(102, 7) * shift_effect - degradation * np.random.uniform(10, 28))

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


def calculate_oee(data, selected_hours):
    avg_defect = data["defect_rate"].mean()
    total_downtime = data["downtime_hours"].sum()

    availability = max(0, 1 - total_downtime / selected_hours)
    performance = min(1, data["production_qty"].mean() / 100)
    quality = max(0, 1 - avg_defect / 100)

    oee = availability * performance * quality * 100
    return availability, performance, quality, oee


def estimate_rul_hours(row):
    risk = float(row["failure_probability"])
    vibration = float(row["vibration"])
    temperature = float(row["temperature"])

    if risk >= 85:
        return 8
    if risk >= 70:
        return 24
    if risk >= 40:
        return max(36, int(120 - risk))

    stress_penalty = max(0, vibration - 0.8) * 18 + max(0, temperature - 72) * 1.5
    return max(72, int(240 - stress_penalty))


def status_badge(status):
    if status == "위험":
        return "🔴 위험"
    if status == "주의":
        return "🟡 주의"
    return "🟢 정상"


# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------

st.sidebar.header("분석 조건")

seed = st.sidebar.number_input(
    "시뮬레이션 Seed",
    min_value=1,
    max_value=9999,
    value=42,
    step=1,
)

selected_hours = st.sidebar.slider(
    "최근 분석 기간(시간)",
    min_value=24,
    max_value=168,
    value=72,
    step=24,
)

risk_threshold = st.sidebar.slider(
    "위험 알람 기준(%)",
    min_value=50,
    max_value=90,
    value=70,
    step=5,
)

st.sidebar.divider()
st.sidebar.caption("Seed 값을 바꾸면 다른 가상 공장 상황이 생성됩니다.")

df = generate_factory_data(seed=seed)

selected_machine = st.sidebar.selectbox(
    "설비 선택",
    sorted(df["machine"].unique()),
)

filtered = df[
    (df["machine"] == selected_machine)
    & (df["timestamp"] >= df["timestamp"].max() - timedelta(hours=selected_hours))
].copy()

fleet_filtered = df[
    df["timestamp"] >= df["timestamp"].max() - timedelta(hours=selected_hours)
].copy()

latest = filtered.sort_values("timestamp").iloc[-1]

status_df = (
    df.sort_values("timestamp")
    .groupby("machine")
    .tail(1)
    [["machine", "status", "failure_probability", "temperature", "vibration", "power_kwh"]]
    .reset_index(drop=True)
)

availability, performance, quality, oee = calculate_oee(filtered, selected_hours)

avg_defect = filtered["defect_rate"].mean()
total_downtime = filtered["downtime_hours"].sum()
total_production = filtered["production_qty"].sum()
avg_failure_risk = filtered["failure_probability"].mean()
rul_hours = estimate_rul_hours(latest)

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

st.title("🏭 가상 공장 디지털 트윈 대시보드")
st.caption("AI 기반 예지보전 · 운영 KPI · ESG · ROI 분석")

st.subheader(f"{selected_machine} 현재 상태: {status_badge(latest['status'])}")

m1, m2, m3, m4, m5, m6 = st.columns(6)

with m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">고장 확률</div>
            <div class="metric-value">{latest['failure_probability']}%</div>
            <div class="metric-sub">AI risk score</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">잔여수명 추정</div>
            <div class="metric-value">{rul_hours} h</div>
            <div class="metric-sub">RUL estimate</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">온도</div>
            <div class="metric-value">{latest['temperature']}℃</div>
            <div class="metric-sub">threshold 85℃</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">진동</div>
            <div class="metric-value">{latest['vibration']}</div>
            <div class="metric-sub">mm/s</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m5:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">전력 사용</div>
            <div class="metric-value">{latest['power_kwh']}</div>
            <div class="metric-sub">kWh</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m6:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">불량률</div>
            <div class="metric-value">{latest['defect_rate']}%</div>
            <div class="metric-sub">quality loss</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# Tabs
# ------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["① 디지털 트윈", "② 센서 추이", "③ 운영 KPI", "④ ESG · ROI", "⑤ 의사결정"]
)

# ------------------------------------------------------------
# Digital Twin View
# ------------------------------------------------------------

with tab1:
    st.markdown('<div class="section-title">가상 공장 3D 스타일 관제 화면</div>', unsafe_allow_html=True)

    status_color = {
        "정상": "#2ecc71",
        "주의": "#f1c40f",
        "위험": "#e74c3c",
    }

    machine_positions = {
        "Press-01": (18, 66),
        "CNC-02": (38, 50),
        "Robot-03": (61, 61),
        "Conveyor-04": (79, 42),
    }

    marker_html = ""

    for _, row in status_df.iterrows():
        left, top = machine_positions[row["machine"]]
        color = status_color[row["status"]]

        marker_html += f"""
        <div class="machine-marker" style="left:{left}%; top:{top}%; border-color:{color}; box-shadow:0 0 18px {color};">
            <div class="marker-dot" style="background:{color};"></div>
            <div class="marker-label">
                <b>{html.escape(row['machine'])}</b><br>
                상태: {html.escape(row['status'])}<br>
                고장확률: {row['failure_probability']}%<br>
                온도: {row['temperature']}℃<br>
                진동: {row['vibration']} mm/s
            </div>
        </div>
        """

    factory_html = f"""
    <style>
    .factory-wrap {{
        display: grid;
        grid-template-columns: 260px 1fr;
        gap: 14px;
        margin-top: 8px;
    }}

    .factory-side {{
        background: linear-gradient(180deg, #0b1020, #111827);
        color: white;
        border-radius: 10px;
        padding: 14px;
        border: 1px solid rgba(255,255,255,0.15);
    }}

    .side-title {{
        font-size: 13px;
        font-weight: 800;
        margin: 10px 0 8px 0;
        color: #e5e7eb;
    }}

    .progress-row {{
        margin-bottom: 8px;
    }}

    .progress-label {{
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        margin-bottom: 3px;
    }}

    .progress-bg {{
        height: 14px;
        background: rgba(255,255,255,0.15);
        border-radius: 7px;
        overflow: hidden;
    }}

    .progress-bar {{
        height: 14px;
        border-radius: 7px;
    }}

    .side-card {{
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 8px;
        padding: 9px;
        margin-bottom: 7px;
        font-size: 13px;
    }}

    .factory-scene {{
        position: relative;
        min-height: 560px;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(15,23,42,0.18);
        background:
            linear-gradient(180deg, rgba(7,13,28,0.25), rgba(7,13,28,0.7)),
            repeating-linear-gradient(90deg, rgba(255,255,255,0.08) 0 2px, transparent 2px 95px),
            repeating-linear-gradient(0deg, rgba(255,255,255,0.06) 0 2px, transparent 2px 72px),
            linear-gradient(135deg, #334155 0%, #94a3b8 42%, #1e293b 100%);
    }}

    .roof {{
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 105px;
        background: repeating-linear-gradient(112deg, rgba(255,255,255,0.22) 0 7px, transparent 7px 44px);
        opacity: 0.45;
    }}

    .floor {{
        position: absolute;
        left: -5%;
        right: -5%;
        bottom: -20px;
        height: 340px;
        background:
            linear-gradient(160deg, #111827, #475569);
        transform: skewY(-8deg);
        border-top: 4px solid rgba(255,255,255,0.22);
    }}

    .yellow-line {{
        position: absolute;
        height: 13px;
        background: #facc15;
        opacity: 0.95;
        border-radius: 8px;
        transform: rotate(-8deg);
    }}

    .yellow-line.a {{
        left: 8%;
        top: 75%;
        width: 85%;
    }}

    .yellow-line.b {{
        left: 28%;
        top: 56%;
        width: 58%;
    }}

    .machine-box {{
        position: absolute;
        width: 98px;
        height: 62px;
        background: linear-gradient(145deg, #f8fafc, #94a3b8);
        border: 1px solid #e2e8f0;
        border-radius: 7px;
        box-shadow: 15px 18px 22px rgba(0,0,0,0.35);
        transform: skewY(-8deg);
    }}

    .machine-box::after {{
        content: "";
        position: absolute;
        right: -20px;
        top: 10px;
        width: 20px;
        height: 52px;
        background: #64748b;
        transform: skewY(30deg);
        border-radius: 0 6px 6px 0;
    }}

    .top-kpis {{
        position: absolute;
        top: 15px;
        left: 18px;
        right: 18px;
        display: grid;
        grid-template-columns: repeat(4, minmax(110px, 1fr));
        gap: 10px;
        z-index: 4;
    }}

    .kpi-pill {{
        background: rgba(2,6,23,0.8);
        color: white;
        border: 1px solid rgba(34,211,238,0.45);
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }}

    .kpi-pill .label {{
        font-size: 11px;
        color: #cbd5e1;
    }}

    .kpi-pill .num {{
        font-size: 23px;
        font-weight: 900;
        color: #f8fafc;
    }}

    .machine-marker {{
        position: absolute;
        width: 38px;
        height: 38px;
        margin-left: -19px;
        margin-top: -19px;
        border: 3px solid;
        border-radius: 50%;
        background: rgba(15,23,42,0.75);
        z-index: 6;
    }}

    .marker-dot {{
        width: 16px;
        height: 16px;
        border-radius: 50%;
        margin: 8px auto;
    }}

    .marker-label {{
        display: none;
        position: absolute;
        left: 44px;
        top: -20px;
        width: 210px;
        background: rgba(15,23,42,0.96);
        color: white;
        border-radius: 8px;
        padding: 10px;
        font-size: 12px;
        line-height: 1.45;
        border: 1px solid rgba(255,255,255,0.2);
    }}

    .machine-marker:hover .marker-label {{
        display: block;
    }}

    @media (max-width: 900px) {{
        .factory-wrap {{
            grid-template-columns: 1fr;
        }}

        .top-kpis {{
            grid-template-columns: repeat(2, minmax(120px, 1fr));
        }}

        .factory-scene {{
            min-height: 620px;
        }}
    }}
    </style>

    <div class="factory-wrap">
        <div class="factory-side">
            <div class="side-title">Production / Target</div>

            <div class="progress-row">
                <div class="progress-label"><span>Assembly Shop1</span><b>88%</b></div>
                <div class="progress-bg"><div class="progress-bar" style="width:88%; background:#14b8a6;"></div></div>
            </div>

            <div class="progress-row">
                <div class="progress-label"><span>Assembly Shop2</span><b>72%</b></div>
                <div class="progress-bg"><div class="progress-bar" style="width:72%; background:#ef4444;"></div></div>
            </div>

            <div class="progress-row">
                <div class="progress-label"><span>Processing Shop</span><b>84%</b></div>
                <div class="progress-bg"><div class="progress-bar" style="width:84%; background:#3b82f6;"></div></div>
            </div>

            <div class="progress-row">
                <div class="progress-label"><span>Part Shop</span><b>61%</b></div>
                <div class="progress-bg"><div class="progress-bar" style="width:61%; background:#facc15;"></div></div>
            </div>

            <div class="side-title">Warehouse Capacity</div>
            <div class="side-card">🔴 위험 설비: {len(status_df[status_df["status"] == "위험"])} EA</div>
            <div class="side-card">🟡 주의 설비: {len(status_df[status_df["status"] == "주의"])} EA</div>
            <div class="side-card">🟢 정상 설비: {len(status_df[status_df["status"] == "정상"])} EA</div>

            <div class="side-title">Product Yield</div>
            <div class="side-card">수율: {100 - avg_defect:.1f}%</div>
            <div class="side-card">불량률: {avg_defect:.1f}%</div>

            <div class="side-title">Selected Machine</div>
            <div class="side-card">{html.escape(selected_machine)}</div>
            <div class="side-card">RUL: {rul_hours} h</div>
        </div>

        <div class="factory-scene">
            <div class="roof"></div>
            <div class="floor"></div>

            <div class="yellow-line a"></div>
            <div class="yellow-line b"></div>

            <div class="top-kpis">
                <div class="kpi-pill">
                    <div class="label">FACILITY OEE</div>
                    <div class="num">{oee:.1f}%</div>
                </div>
                <div class="kpi-pill">
                    <div class="label">AVG RISK</div>
                    <div class="num">{status_df["failure_probability"].mean():.1f}%</div>
                </div>
                <div class="kpi-pill">
                    <div class="label">ENERGY</div>
                    <div class="num">{status_df["power_kwh"].sum():.0f}</div>
                </div>
                <div class="kpi-pill">
                    <div class="label">QUALITY</div>
                    <div class="num">{100 - avg_defect:.1f}%</div>
                </div>
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

    st.write("설비별 최신 상태")
    st.dataframe(
        status_df.sort_values("failure_probability", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

# ------------------------------------------------------------
# Sensor Trend
# ------------------------------------------------------------

with tab2:
    st.markdown('<div class="section-title">센서 데이터 추이</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        fig, ax = plt.subplots(figsize=(8, 3.2))
        ax.plot(filtered["timestamp"], filtered["temperature"], linewidth=2)
        ax.axhline(85, linestyle="--", color="red", linewidth=1)
        ax.set_title("온도 추이")
        ax.set_xlabel("Time")
        ax.set_ylabel("Temperature (℃)")
        ax.grid(alpha=0.25)
        fig.autofmt_xdate(rotation=30)
        st.pyplot(fig, use_container_width=True)

    with c2:
        fig, ax = plt.subplots(figsize=(8, 3.2))
        ax.plot(filtered["timestamp"], filtered["vibration"], linewidth=2)
        ax.axhline(1.5, linestyle="--", color="red", linewidth=1)
        ax.set_title("진동 추이")
        ax.set_xlabel("Time")
        ax.set_ylabel("Vibration (mm/s)")
        ax.grid(alpha=0.25)
        fig.autofmt_xdate(rotation=30)
        st.pyplot(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        fig, ax = plt.subplots(figsize=(8, 3.2))
        ax.plot(filtered["timestamp"], filtered["power_kwh"], linewidth=2)
        ax.set_title("전력 사용량 추이")
        ax.set_xlabel("Time")
        ax.set_ylabel("Power (kWh)")
        ax.grid(alpha=0.25)
        fig.autofmt_xdate(rotation=30)
        st.pyplot(fig, use_container_width=True)

    with c4:
        fig, ax = plt.subplots(figsize=(8, 3.2))
        ax.plot(filtered["timestamp"], filtered["failure_probability"], linewidth=2)
        ax.axhline(risk_threshold, linestyle="--", color="red", linewidth=1)
        ax.set_title("AI 고장 확률 추이")
        ax.set_xlabel("Time")
        ax.set_ylabel("Failure Probability (%)")
        ax.grid(alpha=0.25)
        fig.autofmt_xdate(rotation=30)
        st.pyplot(fig, use_container_width=True)

    st.download_button(
        "선택 설비 데이터 CSV 다운로드",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{selected_machine}_digital_twin_data.csv",
        mime="text/csv",
    )

# ------------------------------------------------------------
# Operation KPI
# ------------------------------------------------------------

with tab3:
    st.markdown('<div class="section-title">운영 KPI 분석</div>', unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("총 생산량", f"{total_production:,.0f} EA")
    k2.metric("평균 불량률", f"{avg_defect:.2f}%")
    k3.metric("누적 다운타임", f"{total_downtime:.1f} h")
    k4.metric("OEE", f"{oee:.1f}%")

    oee_df = pd.DataFrame(
        {
            "항목": ["가동률", "성능", "품질", "OEE"],
            "값": [availability * 100, performance * 100, quality * 100, oee],
        }
    )

    st.bar_chart(oee_df.set_index("항목"))

    st.info(
        "OEE는 가동률, 성능, 품질을 종합한 설비종합효율 지표입니다. "
        "본 대시보드는 교육용 단순화 산식을 사용합니다."
    )

    st.write("최근 알람 로그")

    alarm_log = fleet_filtered[fleet_filtered["failure_probability"] >= risk_threshold].copy()
    alarm_log = alarm_log.sort_values(
        ["timestamp", "failure_probability"],
        ascending=[False, False],
    ).head(20)

    st.dataframe(
        alarm_log[
            [
                "timestamp",
                "machine",
                "status",
                "failure_probability",
                "temperature",
                "vibration",
                "downtime_hours",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

# ------------------------------------------------------------
# ESG + ROI
# ------------------------------------------------------------

with tab4:
    st.markdown('<div class="section-title">ESG 효과 분석</div>', unsafe_allow_html=True)

    baseline_energy = filtered["power_kwh"].sum() * 1.12
    actual_energy = filtered["power_kwh"].sum()
    energy_saving = baseline_energy - actual_energy

    carbon_factor = 0.459
    carbon_reduction = energy_saving * carbon_factor

    e1, e2, e3 = st.columns(3)

    e1.metric("기준 에너지", f"{baseline_energy:,.0f} kWh")
    e2.metric("절감 에너지", f"{energy_saving:,.0f} kWh")
    e3.metric("탄소 감축 추정", f"{carbon_reduction:,.0f} kgCO₂")

    st.divider()
    st.markdown('<div class="section-title">ROI 분석</div>', unsafe_allow_html=True)

    investment_cost = st.number_input("초기 구축비(원)", value=50_000_000, step=5_000_000)
    downtime_cost_per_hour = st.number_input("다운타임 1시간 손실비용(원)", value=1_500_000, step=100_000)
    maintenance_saving = st.number_input("연간 유지보수 절감액(원)", value=20_000_000, step=1_000_000)
    energy_cost_per_kwh = st.number_input("전력 단가(원/kWh)", value=150, step=10)

    before_downtime_year = st.slider("도입 전 연간 다운타임(h)", 100, 800, 420, step=20)
    after_downtime_year = st.slider("도입 후 연간 다운타임(h)", 50, 600, 240, step=20)

    downtime_saving = max(0, before_downtime_year - after_downtime_year) * downtime_cost_per_hour
    energy_saving_year = energy_saving * (8760 / selected_hours) * energy_cost_per_kwh
    annual_benefit = downtime_saving + maintenance_saving + energy_saving_year

    roi = (annual_benefit - investment_cost) / investment_cost * 100
    payback = investment_cost / annual_benefit if annual_benefit > 0 else np.nan

    r1, r2, r3 = st.columns(3)

    r1.metric("연간 절감효과", f"{annual_benefit:,.0f} 원")
    r2.metric("ROI", f"{roi:.1f}%")
    r3.metric("투자회수기간", f"{payback:.2f} 년")

    roi_df = pd.DataFrame(
        {
            "구분": ["다운타임 절감", "유지보수 절감", "에너지 절감"],
            "금액": [downtime_saving, maintenance_saving, energy_saving_year],
        }
    )

    st.bar_chart(roi_df.set_index("구분"))

# ------------------------------------------------------------
# Decision Recommendation
# ------------------------------------------------------------

with tab5:
    st.markdown('<div class="section-title">운영 의사결정 제안</div>', unsafe_allow_html=True)

    if latest["failure_probability"] >= risk_threshold:
        st.error(
            "AI 분석 결과, 설비 고장 위험이 높습니다. "
            "즉시 예방정비를 수행하고 생산계획을 조정하는 것이 필요합니다."
        )
        action = "즉시 정비 지시, 예비 설비 전환, 생산계획 재배치"
        priority = "높음"

    elif latest["failure_probability"] >= 40:
        st.warning(
            "설비 상태가 주의 단계입니다. "
            "다음 교대조 이전 점검을 권장합니다."
        )
        action = "점검 예약, 윤활 및 체결 상태 확인, 센서 추세 재확인"
        priority = "중간"

    else:
        st.success(
            "설비 상태가 안정적입니다. "
            "현재 운영 조건을 유지하되 센서 데이터를 지속 모니터링합니다."
        )
        action = "정상 운전 유지, 일상 점검"
        priority = "낮음"

    recommendation_df = pd.DataFrame(
        {
            "항목": ["권장 조치", "우선순위", "예상 잔여수명", "판단 근거"],
            "내용": [
                action,
                priority,
                f"{rul_hours}시간",
                f"고장확률 {latest['failure_probability']}%, 온도 {latest['temperature']}℃, 진동 {latest['vibration']} mm/s",
            ],
        }
    )

    st.table(recommendation_df)

    st.markdown(
        """
        ### 보고서에 쓸 핵심 해석

        - 디지털 트윈은 현실 설비의 센서 상태를 가상 환경에 반영하여 운영관리자의 의사결정을 지원한다.
        - AI 기반 예지보전은 고장 가능성을 사전에 탐지하여 다운타임, 불량률, 긴급정비 비용을 줄인다.
        - 에너지 사용량 감소와 탄소배출 감축을 통해 ESG와 수익성은 상호보완적으로 작동할 수 있다.
        - 단, AI 모델의 예측 결과는 최종 의사결정을 대체하기보다 관리자 판단을 보조하는 역할로 보는 것이 적절하다.
        """
    )

st.caption("※ 본 데이터와 수치는 대학원 과제용 가상 시뮬레이션 예시입니다.")
