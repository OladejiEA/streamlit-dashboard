import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import requests
import io
import time

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VitaTrack – Patient Monitoring",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Constants ──────────────────────────────────────────────────────────────────
FLASK_API_URL = "https://flask-vitals.onrender.com"
ALERTS_FILE   = "alerts.csv"
REFRESH_INTERVAL = 10  # seconds

# ─── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base & fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0f172a;
    color: #f8fafc;
}
section[data-testid="stSidebar"] * { color: #f8fafc !important; }
section[data-testid="stSidebar"] .stRadio label {
    font-size: 15px;
    padding: 6px 0;
}

/* ── Page background ── */
.main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* ── Metric cards ── */
.metric-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 16px;
    border-left: 5px solid #3b82f6;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.metric-card.alert-card { border-left-color: #ef4444; background: #fff5f5; }
.metric-card .label  { font-size: 13px; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: .5px; }
.metric-card .value  { font-size: 36px; font-weight: 700; color: #0f172a; line-height: 1.1; }
.metric-card .status { font-size: 13px; font-weight: 600; margin-top: 4px; }
.status-normal  { color: #16a34a; }
.status-warning { color: #ef4444; }

/* ── Section titles ── */
.section-title {
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
}
.section-sub {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 20px;
}

/* ── Alert items ── */
.alert-item {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    background: #fff5f5;
    border: 1px solid #fecaca;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.alert-icon { font-size: 22px; }
.alert-body { flex: 1; }
.alert-title { font-weight: 600; color: #b91c1c; font-size: 15px; }
.alert-time  { font-size: 12px; color: #94a3b8; margin-top: 2px; }

/* ── Flash animation ── */
@keyframes flash {
    0%   { background-color: #fff5f5; }
    50%  { background-color: #fca5a5; }
    100% { background-color: #fff5f5; }
}
.flash { animation: flash 1s ease-in-out 3; }

/* ── Download button ── */
.stDownloadButton button {
    background: #3b82f6 !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
}

/* ── Form inputs ── */
.stNumberInput input { border-radius: 8px !important; }
.stButton button {
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* ── Chart container ── */
.chart-box {
    background: #fff;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}

/* ── Badge ── */
.badge {
    display: inline-block;
    background: #ef4444;
    color: white;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    margin-left: 6px;
    vertical-align: middle;
}

/* ── Header bar ── */
.header-bar {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e2e8f0;
}
.header-logo { font-size: 32px; }
.header-title { font-size: 28px; font-weight: 800; color: #0f172a; }
.header-sub   { font-size: 14px; color: #64748b; }

/* ── Last updated ── */
.last-updated { font-size: 12px; color: #94a3b8; text-align: right; margin-bottom: 8px; }

/* ── BP result card ── */
.bp-result {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 10px;
    padding: 16px 20px;
    font-size: 16px;
    font-weight: 600;
    color: #166534;
    margin-top: 16px;
}
</style>
""", unsafe_allow_html=True)

# ─── Sound / Visual Flash helper ────────────────────────────────────────────────
ALERT_SOUND_JS = """
<script>
(function() {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    function beep(freq, dur, vol) {
        var o = ctx.createOscillator();
        var g = ctx.createGain();
        o.connect(g); g.connect(ctx.destination);
        o.frequency.value = freq;
        g.gain.value = vol || 0.3;
        o.start(); o.stop(ctx.currentTime + dur);
    }
    beep(880, 0.18); 
    setTimeout(function(){ beep(660, 0.18); }, 220);
    setTimeout(function(){ beep(880, 0.35); }, 440);
})();
</script>
"""

def play_alert_sound():
    st.components.v1.html(ALERT_SOUND_JS, height=0)

# ─── Session state ───────────────────────────────────────────────────────────────
for key, default in {
    "alerts_viewed": False,
    "alert_count_seen": 0,
    "last_alert_count": 0,
    "flash_active": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Data helpers ────────────────────────────────────────────────────────────────
def load_data():
    try:
        response = requests.get(f"{FLASK_API_URL}/vitals", timeout=8)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            for col in ["Temperature", "Blood Oxygen", "Heart Rate", "Respiration Rate"]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        return pd.DataFrame(columns=["Timestamp","Temperature","Blood Oxygen","Heart Rate","Respiration Rate","Blood Pressure"])
    except Exception as e:
        st.error(f"⚠️ Could not reach Flask API: {e}")
        return pd.DataFrame(columns=["Timestamp","Temperature","Blood Oxygen","Heart Rate","Respiration Rate","Blood Pressure"])

def load_alerts():
    if os.path.exists(ALERTS_FILE):
        return pd.read_csv(ALERTS_FILE)
    return pd.DataFrame(columns=["Timestamp", "Alert", "Dismissed"])

def save_alert(message):
    alerts = load_alerts()
    # Avoid duplicate alerts within the same reading cycle
    if not alerts.empty:
        recent = alerts.tail(1).iloc[0]
        if recent["Alert"] == message:
            age = datetime.now() - datetime.fromisoformat(recent["Timestamp"])
            if age.total_seconds() < 15:
                return
    new_alert = pd.DataFrame([[datetime.now().isoformat(), message, False]],
                              columns=["Timestamp", "Alert", "Dismissed"])
    alerts = pd.concat([alerts, new_alert], ignore_index=True)
    alerts.to_csv(ALERTS_FILE, index=False)

def dismiss_alert(index):
    alerts = load_alerts()
    if "Dismissed" not in alerts.columns:
        alerts["Dismissed"] = False
    alerts.at[index, "Dismissed"] = True
    alerts.to_csv(ALERTS_FILE, index=False)

def clear_all_alerts():
    pd.DataFrame(columns=["Timestamp", "Alert", "Dismissed"]).to_csv(ALERTS_FILE, index=False)

def active_alerts(df):
    if "Dismissed" not in df.columns:
        df["Dismissed"] = False
    return df[df["Dismissed"] != True]

# ─── Chart helper ────────────────────────────────────────────────────────────────
CHART_COLORS = {
    "Temperature":      ("#ef4444", "#fff5f5"),
    "Blood Oxygen":     ("#3b82f6", "#eff6ff"),
    "Heart Rate":       ("#10b981", "#f0fdf4"),
    "Respiration Rate": ("#f59e0b", "#fffbeb"),
}

def make_chart(df, col):
    color, bg = CHART_COLORS[col]
    fig, ax = plt.subplots(figsize=(5.5, 2.8))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.plot(df["Timestamp"], df[col], color=color, linewidth=2.2,
            marker='o', markersize=4, markerfacecolor=color)
    ax.fill_between(df["Timestamp"], df[col], alpha=0.15, color=color)
    ax.set_xlabel("Time", fontsize=9, color="#64748b")
    ax.set_ylabel(col, fontsize=9, color="#64748b")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.tick_params(colors="#64748b", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#e2e8f0")
    ax.grid(True, linestyle='--', alpha=0.4, color="#e2e8f0")
    fig.tight_layout()
    return fig

# ─── Sidebar ─────────────────────────────────────────────────────────────────────
alerts_df   = load_alerts()
active_df   = active_alerts(alerts_df)
alert_count = len(active_df)

with st.sidebar:
    st.markdown("## 🩺 VitaTrack")
    st.markdown("---")

    # Alert badge
    badge_html = ""
    if alert_count > 0 and not st.session_state.alerts_viewed:
        badge_html = f'<span class="badge">{alert_count}</span>'
    st.markdown(f"**Navigation** {badge_html}", unsafe_allow_html=True)

    page = st.radio("", ["🏠 Home", "🔔 Alerts", "💉 BP Measurement", "📥 Data Download"],
                    label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"<span style='font-size:12px;color:#94a3b8'>🔴 {alert_count} active alert(s)</span>",
                unsafe_allow_html=True)
    st.markdown(f"<span style='font-size:12px;color:#94a3b8'>⏱ Auto-refresh: {REFRESH_INTERVAL}s</span>",
                unsafe_allow_html=True)

# ─── Sound trigger when new alerts arrive ────────────────────────────────────────
if alert_count > st.session_state.last_alert_count:
    play_alert_sound()
    st.session_state.flash_active = True
st.session_state.last_alert_count = alert_count

# ══════════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ══════════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.session_state.alerts_viewed = False

    # Header
    st.markdown("""
    <div class="header-bar">
        <div class="header-logo">🩺</div>
        <div>
            <div class="header-title">VitaTrack</div>
            <div class="header-sub">Real-time Patient Vital Signs Monitoring</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df = load_data()

    if df.empty:
        st.warning("No data available from the Flask API. Waiting for sensor data…")
    else:
        display_df = df.tail(10)
        latest     = display_df.iloc[-1]
        now_str    = datetime.now().strftime("%d %b %Y, %H:%M:%S")

        st.markdown(f'<div class="last-updated">Last updated: {now_str}</div>', unsafe_allow_html=True)

        # ── Metric cards row ──────────────────────────────────────────────────────
        vitals = [
            ("Temperature",      "°C",          36.0, 38.0,  "🌡️"),
            ("Blood Oxygen",     "%",            90.0, 100.0, "🫁"),
            ("Heart Rate",       "bpm",          60.0, 100.0, "❤️"),
            ("Respiration Rate", "breaths/min",  12.0, 20.0,  "🌬️"),
        ]

        cols = st.columns(4)
        new_alerts_triggered = False

        for i, (col_name, unit, lo, hi, icon) in enumerate(vitals):
            val = latest[col_name]
            is_alert = pd.notna(val) and (val < lo or val > hi)
            if is_alert:
                save_alert(f"{col_name} out of range ({val:.1f} {unit})")
                new_alerts_triggered = True

            card_class = "metric-card alert-card flash" if (is_alert and st.session_state.flash_active) else "metric-card"
            status_text  = f"⚠️ Out of range [{lo}–{hi}]" if is_alert else f"✓ Normal [{lo}–{hi}]"
            status_class = "status-warning" if is_alert else "status-normal"
            val_str      = f"{val:.1f}" if pd.notna(val) else "—"

            with cols[i]:
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="label">{icon} {col_name}</div>
                    <div class="value">{val_str} <span style="font-size:18px;color:#64748b">{unit}</span></div>
                    <div class="status {status_class}">{status_text}</div>
                </div>
                """, unsafe_allow_html=True)

        if new_alerts_triggered:
            play_alert_sound()

        st.session_state.flash_active = False

        # ── Charts ────────────────────────────────────────────────────────────────
        st.markdown('<div class="section-title">Trend Charts</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Last 10 readings from sensor</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="chart-box">', unsafe_allow_html=True)
            st.pyplot(make_chart(display_df, "Temperature"))
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="chart-box">', unsafe_allow_html=True)
            st.pyplot(make_chart(display_df, "Heart Rate"))
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="chart-box">', unsafe_allow_html=True)
            st.pyplot(make_chart(display_df, "Blood Oxygen"))
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="chart-box">', unsafe_allow_html=True)
            st.pyplot(make_chart(display_df, "Respiration Rate"))
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Latest BP ─────────────────────────────────────────────────────────────
        if "Blood Pressure" in df.columns and df["Blood Pressure"].notna().any():
            last_bp = df["Blood Pressure"].dropna().iloc[-1]
            st.markdown(f"""
            <div class="metric-card" style="border-left-color:#8b5cf6; max-width:320px;">
                <div class="label">💓 Last Blood Pressure Reading</div>
                <div class="value">{last_bp} <span style="font-size:18px;color:#64748b">mmHg</span></div>
            </div>
            """, unsafe_allow_html=True)

    # ── Auto-refresh ──────────────────────────────────────────────────────────────
    with st.spinner(f"⏱ Refreshing in {REFRESH_INTERVAL}s…"):
        time.sleep(REFRESH_INTERVAL)
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════════
# PAGE: ALERTS
# ══════════════════════════════════════════════════════════════════════════════════
elif page == "🔔 Alerts":
    st.session_state.alerts_viewed = True

    st.markdown("""
    <div class="header-bar">
        <div class="header-logo">🔔</div>
        <div>
            <div class="header-title">Alerts & Notifications</div>
            <div class="header-sub">All triggered vital sign alerts</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    alerts_df = load_alerts()
    if "Dismissed" not in alerts_df.columns:
        alerts_df["Dismissed"] = False

    active  = active_alerts(alerts_df)
    dismissed_count = len(alerts_df) - len(active)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(f"**{len(active)} active alert(s)** · {dismissed_count} dismissed")
    with col_b:
        if st.button("🗑️ Clear All Alerts", use_container_width=True):
            clear_all_alerts()
            st.success("All alerts cleared.")
            st.rerun()

    st.markdown("---")

    if active.empty:
        st.markdown("""
        <div style="text-align:center;padding:40px;color:#64748b;">
            <div style="font-size:48px">✅</div>
            <div style="font-size:18px;font-weight:600;margin-top:12px">No active alerts</div>
            <div style="font-size:14px;margin-top:4px">All vitals are within normal range.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        alert_icons = {
            "Temperature":      "🌡️",
            "Blood Oxygen":     "🫁",
            "Heart Rate":       "❤️",
            "Respiration Rate": "🌬️",
        }
        for idx, row in active.iterrows():
            icon = next((v for k, v in alert_icons.items() if k in row["Alert"]), "⚠️")
            ts   = row["Timestamp"]
            try:
                ts = datetime.fromisoformat(ts).strftime("%d %b %Y, %H:%M:%S")
            except Exception:
                pass

            col_msg, col_btn = st.columns([5, 1])
            with col_msg:
                st.markdown(f"""
                <div class="alert-item">
                    <div class="alert-icon">{icon}</div>
                    <div class="alert-body">
                        <div class="alert-title">{row['Alert']}</div>
                        <div class="alert-time">{ts}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if st.button("Dismiss", key=f"dismiss_{idx}"):
                    dismiss_alert(idx)
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════════
# PAGE: BP MEASUREMENT
# ══════════════════════════════════════════════════════════════════════════════════
elif page == "💉 BP Measurement":

    st.markdown("""
    <div class="header-bar">
        <div class="header-logo">💉</div>
        <div>
            <div class="header-title">Blood Pressure Measurement</div>
            <div class="header-sub">Manually log a BP reading to the database</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_form, col_info = st.columns([1, 1])

    with col_form:
        st.markdown("#### Enter Reading")
        systolic  = st.number_input("Systolic BP (mmHg)",  min_value=50,  max_value=200, step=1, value=120)
        diastolic = st.number_input("Diastolic BP (mmHg)", min_value=30,  max_value=150, step=1, value=80)

        # BP classification
        def classify_bp(sys, dia):
            if sys < 120 and dia < 80:
                return "Normal", "#16a34a"
            elif sys < 130 and dia < 80:
                return "Elevated", "#ca8a04"
            elif sys < 140 or dia < 90:
                return "High Stage 1", "#ea580c"
            else:
                return "High Stage 2", "#dc2626"

        category, cat_color = classify_bp(systolic, diastolic)
        st.markdown(f"""
        <div style="background:#f8fafc;border-radius:8px;padding:10px 16px;margin:8px 0;
                    border-left:4px solid {cat_color};font-size:14px;">
            <strong>Classification:</strong>
            <span style="color:{cat_color};font-weight:700"> {category}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💾 Save BP Measurement", use_container_width=True):
            payload = {
                "temperature":     None,
                "blood_oxygen":    None,
                "heart_rate":      None,
                "respiration_rate": None,
                "blood_pressure":  f"{systolic}/{diastolic}"
            }
            try:
                resp = requests.post(f"{FLASK_API_URL}/data", json=payload, timeout=8)
                if resp.status_code == 200:
                    st.success(f"✅ BP {systolic}/{diastolic} mmHg saved successfully!")
                    if systolic >= 140 or diastolic >= 90:
                        save_alert(f"High BP recorded: {systolic}/{diastolic} mmHg")
                        play_alert_sound()
                        st.error("⚠️ High blood pressure detected — alert saved.")
                else:
                    st.error(f"Failed to save: {resp.text}")
            except Exception as e:
                st.error(f"Error saving BP: {e}")

    with col_info:
        st.markdown("#### BP Reference Guide")
        st.markdown("""
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <tr style="background:#f1f5f9;font-weight:600">
            <td style="padding:8px 12px">Category</td>
            <td style="padding:8px 12px">Systolic</td>
            <td style="padding:8px 12px">Diastolic</td>
        </tr>
        <tr><td style="padding:8px 12px;color:#16a34a;font-weight:600">Normal</td>
            <td style="padding:8px 12px">&lt; 120</td><td style="padding:8px 12px">&lt; 80</td></tr>
        <tr style="background:#f8fafc"><td style="padding:8px 12px;color:#ca8a04;font-weight:600">Elevated</td>
            <td style="padding:8px 12px">120–129</td><td style="padding:8px 12px">&lt; 80</td></tr>
        <tr><td style="padding:8px 12px;color:#ea580c;font-weight:600">High Stage 1</td>
            <td style="padding:8px 12px">130–139</td><td style="padding:8px 12px">80–89</td></tr>
        <tr style="background:#f8fafc"><td style="padding:8px 12px;color:#dc2626;font-weight:600">High Stage 2</td>
            <td style="padding:8px 12px">≥ 140</td><td style="padding:8px 12px">≥ 90</td></tr>
        </table>
        """, unsafe_allow_html=True)

        # Show last BP from database
        df = load_data()
        if not df.empty and "Blood Pressure" in df.columns and df["Blood Pressure"].notna().any():
            last_bp = df["Blood Pressure"].dropna().iloc[-1]
            st.markdown(f"""
            <div class="bp-result">
                💓 Last recorded BP: <span style="font-size:20px">{last_bp}</span> mmHg
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════════
# PAGE: DATA DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════════
elif page == "📥 Data Download":

    st.markdown("""
    <div class="header-bar">
        <div class="header-logo">📥</div>
        <div>
            <div class="header-title">Download Patient Data</div>
            <div class="header-sub">Export all vitals data as CSV</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df = load_data()

    if df.empty:
        st.warning("No data available to download yet.")
    else:
        # Summary stats
        st.markdown("#### Data Summary")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Readings", len(df))
        s2.metric("From",  df["Timestamp"].min().strftime("%d %b %Y"))
        s3.metric("To",    df["Timestamp"].max().strftime("%d %b %Y"))
        s4.metric("Columns", len(df.columns))

        st.markdown("---")
        st.markdown("#### Preview (last 10 rows)")
        st.dataframe(df.tail(10), use_container_width=True, hide_index=True)

        st.markdown("---")
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="⬇️ Download Full CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"vitatrack_vitals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_dl2:
            alerts_export = load_alerts()
            if not alerts_export.empty:
                st.download_button(
                    label="⬇️ Download Alerts Log",
                    data=alerts_export.to_csv(index=False).encode("utf-8"),
                    file_name=f"vitatrack_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
