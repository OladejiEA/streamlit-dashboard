import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import requests
import io
import time

# Page configuration
st.set_page_config(
    page_title="Patient Monitoring Dashboard",
    page_icon="🩺",
    layout="wide"
)

# Flask API URL
FLASK_API_URL = "https://flask-vitals.onrender.com"  # Adjust if Render URL differs

# Constants
ALERTS_FILE = "alerts.csv"
CONNECTION_THRESHOLD = 20  # Seconds to consider hardware disconnected (2x ESP32 interval)

# Initialize session state
if "alerts_viewed" not in st.session_state:
    st.session_state.alerts_viewed = False

# Load data from Flask API (CSV)
def load_data():
    try:
        response = requests.get(f"{FLASK_API_URL}/vitals", headers={"Cache-Control": "no-cache"})
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            df["Temperature"] = pd.to_numeric(df["Temperature"], errors='coerce')
            df["Blood Oxygen"] = pd.to_numeric(df["Blood Oxygen"], errors='coerce')
            df["Heart Rate"] = pd.to_numeric(df["Heart Rate"], errors='coerce')
            df["Respiration Rate"] = pd.to_numeric(df["Respiration Rate"], errors='coerce')
            return df
        else:
            st.warning("No data available from Flask.")
            return pd.DataFrame(columns=["Timestamp", "Temperature", "Blood Oxygen", "Heart Rate", "Respiration Rate", "Blood Pressure"])
    except Exception as e:
        st.error(f"Error fetching data from Flask: {e}")
        return pd.DataFrame(columns=["Timestamp", "Temperature", "Blood Oxygen", "Heart Rate", "Respiration Rate", "Blood Pressure"])

# Check hardware connection status
def is_hardware_connected(df):
    if df.empty:
        return False
    latest_timestamp = df["Timestamp"].iloc[-1]
    current_time = datetime.now(latest_timestamp.tzinfo)  # Match timezone if present
    time_diff = (current_time - latest_timestamp).total_seconds()
    return time_diff <= CONNECTION_THRESHOLD

# Load and save alerts
def load_alerts():
    if os.path.exists(ALERTS_FILE):
        return pd.read_csv(ALERTS_FILE)
    return pd.DataFrame(columns=["Timestamp", "Alert"])

def save_alert(message):
    alerts = load_alerts()
    new_alert = pd.DataFrame([[datetime.now().isoformat(), message]], columns=["Timestamp", "Alert"])
    alerts = pd.concat([alerts, new_alert], ignore_index=True)
    alerts.to_csv(ALERTS_FILE, index=False)

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Home", "Alerts", "BP Measurement", "Data Download"])

# Alert indicator
alerts_df = load_alerts()
if not alerts_df.empty and not st.session_state.alerts_viewed:
    st.sidebar.markdown("🔴 **Active Alerts!**")

# Home page with auto-refresh
if page == "Home":
    st.title("Patient Vital Signs")
    df = load_data()

    # Hardware connection status
    if is_hardware_connected(df):
        st.markdown('<p style="background-color: #00FF00; padding: 10px; border-radius: 5px; text-align: center;">Device Connected</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="background-color: #FF0000; padding: 10px; border-radius: 5px; text-align: center;">Device Disconnected</p>', unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available.")
    else:
        df = df.tail(5)
        col1, col2 = st.columns(2)

        with col1:
            temp = df["Temperature"].iloc[-1]
            st.metric("Current Temperature (°C)", f"{temp:.1f}" if pd.notna(temp) else "N/A")
            if pd.notna(temp) and (temp < 36 or temp > 38):
                st.error("⚠️ Temperature Alert!")
                save_alert("Temperature Alert")
            fig, ax = plt.subplots()
            ax.plot(df["Timestamp"], df["Temperature"], color="red")
            ax.set_ylabel("Temperature (°C)")
            ax.set_xlabel("Time")
            ax.grid(True)
            st.pyplot(fig)

        with col2:
            spo2 = df["Blood Oxygen"].iloc[-1]
            st.metric("Blood Oxygen (%)", f"{spo2:.1f}" if pd.notna(spo2) else "N/A")
            if pd.notna(spo2) and spo2 < 90:
                st.error("⚠️ Oxygen Level Alert!")
                save_alert("Oxygen Level Alert")
            fig, ax = plt.subplots()
            ax.plot(df["Timestamp"], df["Blood Oxygen"], color="blue")
            ax.set_ylabel("Blood Oxygen (%)")
            ax.set_xlabel("Time")
            ax.grid(True)
            st.pyplot(fig)

        with col1:
            hr = df["Heart Rate"].iloc[-1]
            st.metric("Heart Rate (bpm)", f"{hr:.0f}" if pd.notna(hr) else "N/A")
            if pd.notna(hr) and (hr < 60 or hr > 100):
                st.error("⚠️ Heart Rate Alert!")
                save_alert("Heart Rate Alert")
            fig, ax = plt.subplots()
            ax.plot(df["Timestamp"], df["Heart Rate"], color="green")
            ax.set_ylabel("Heart Rate (bpm)")
            ax.set_xlabel("Time")
            ax.grid(True)
            st.pyplot(fig)

        with col2:
            resp_rate = df["Respiration Rate"].iloc[-1]
            st.metric("Respiration Rate (breaths/min)", f"{resp_rate:.0f}" if pd.notna(resp_rate) else "N/A")
            if pd.notna(resp_rate) and (resp_rate < 12 or resp_rate > 20):
                st.error("⚠️ Respiration Rate Alert!")
                save_alert("Respiration Rate Alert")
            fig, ax = plt.subplots()
            ax.plot(df["Timestamp"], df["Respiration Rate"], color="orange")
            ax.set_ylabel("Respiration Rate (breaths/min)")
            ax.set_xlabel("Time")
            ax.grid(True)
            st.pyplot(fig)

    # Auto-refresh every 10 seconds on Home page only
    time.sleep(10)
    st.rerun()

elif page == "Alerts":
    st.title("Alerts & Notifications")
    st.session_state.alerts_viewed = True
    alerts_df = load_alerts()
    if alerts_df.empty:
        st.info("No alerts recorded.")
    else:
        for _, row in alerts_df.iterrows():
            st.markdown(
                f"""
                <div style="padding: 10px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 5px; background-color: #ffcccc;">
                <strong>{row['Timestamp']}</strong>: {row['Alert']}
                </div>
                """,
                unsafe_allow_html=True
            )

elif page == "BP Measurement":
    st.title("Blood Pressure Measurement")
    systolic = st.number_input("Systolic BP (mmHg)", min_value=50, max_value=200, step=1)
    diastolic = st.number_input("Diastolic BP (mmHg)", min_value=30, max_value=150, step=1)
    if st.button("Save BP Measurement"):
        payload = {
            "temperature": None,
            "blood_oxygen": None,
            "heart_rate": None,
            "respiration_rate": None,
            "blood_pressure": f"{systolic}/{diastolic}"
        }
        try:
            response = requests.post(f"{FLASK_API_URL}/data", json=payload)
            if response.status_code == 200:
                st.success("Blood Pressure measurement saved!")
            else:
                st.error(f"Failed to save BP: {response.text}")
        except Exception as e:
            st.error(f"Error saving BP: {e}")

    df = load_data()
    if not df.empty and df["Blood Pressure"].notna().any():
        last_bp = df["Blood Pressure"].dropna().iloc[-1]
        st.metric("Last Measured BP", last_bp)

elif page == "Data Download":
    st.title("Download Patient Data")
    df = load_data()
    if df.empty:
        st.warning("No data available to download.")
    else:
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="patient_vitals.csv",
            mime="text/csv"
        )
