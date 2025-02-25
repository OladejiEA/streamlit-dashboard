import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import requests
import os

# Page configuration
st.set_page_config(
    page_title="Patient Monitoring Dashboard",
    page_icon="🩺",
    layout="wide"
)

# Flask API URL (update with your Flask Render URL after deployment)
FLASK_API_URL = "https://flask-vitals.onrender.com/"  # Replace with your Flask URL after deployment

# Constants
ALERTS_FILE = "alerts.csv"

# Initialize session state
if "alerts_viewed" not in st.session_state:
    st.session_state.alerts_viewed = False

# Load data from Flask API
def load_data():
    try:
        response = requests.get(f"{FLASK_API_URL}/vitals")
        if response.status_code == 200:
            df = pd.read_csv(response.text.splitlines())
            return df
        else:
            return pd.DataFrame(columns=["Timestamp", "Temperature", "Blood Oxygen", "Heart Rate", "Respiration Rate", "Blood Pressure"])
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame(columns=["Timestamp", "Temperature", "Blood Oxygen", "Heart Rate", "Respiration Rate", "Blood Pressure"])

# Load and save alerts (local to Streamlit for now)
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

# Home page
if page == "Home":
    st.title("Patient Vital Signs")
    df = load_data()
    if df.empty:
        st.warning("No data available.")
    else:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df = df.tail(5)  # Last 5 readings

        col1, col2 = st.columns(2)

        with col1:
            temp = df["Temperature"].iloc[-1]
            st.metric("Current Temperature (°C)", f"{temp:.1f}")
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
            st.metric("Blood Oxygen (%)", f"{spo2:.1f}")
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
            st.metric("Heart Rate (bpm)", f"{hr:.0f}")
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
            st.metric("Respiration Rate (breaths/min)", f"{resp_rate:.0f}")
            if pd.notna(resp_rate) and (resp_rate < 12 or resp_rate > 20):
                st.error("⚠️ Respiration Rate Alert!")
                save_alert("Respiration Rate Alert")
            fig, ax = plt.subplots()
            ax.plot(df["Timestamp"], df["Respiration Rate"], color="orange")
            ax.set_ylabel("Respiration Rate (breaths/min)")
            ax.set_xlabel("Time")
            ax.grid(True)
            st.pyplot(fig)

# Alerts page
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

# BP Measurement page
elif page == "BP Measurement":
    st.title("Blood Pressure Measurement")
    systolic = st.number_input("Systolic BP (mmHg)", min_value=50, max_value=200, step=1)
    diastolic = st.number_input("Diastolic BP (mmHg)", min_value=30, max_value=150, step=1)
    if st.button("Save BP Measurement"):
        df = load_data()
        new_entry = pd.DataFrame([[datetime.now().isoformat(), None, None, None, None, f"{systolic}/{diastolic}"]],
                                 columns=df.columns)
        df = pd.concat([df, new_entry], ignore_index=True)
        # Note: This only saves locally; to persist, you'd need to POST to Flask (future enhancement)
        st.success("Blood Pressure measurement saved locally (not synced to Flask yet).")

    df = load_data()
    if not df.empty and df["Blood Pressure"].notna().any():
        last_bp = df["Blood Pressure"].dropna().iloc[-1]
        st.metric("Last Measured BP", last_bp)

# Data Download page
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
