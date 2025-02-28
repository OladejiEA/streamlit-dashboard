import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import os
import requests
import time

# Page configuration
st.set_page_config(
    page_title="Patient Monitoring Dashboard",
    page_icon="🩺",
    layout="wide"
)

# Firebase setup
CREDS_FILE = "credentials.json"
if not firebase_admin._apps:  # Prevent re-initialization
    cred = credentials.Certificate(CREDS_FILE)
    firebase_admin.initialize_app(cred)
db = firestore.client()
vitals_ref = db.collection('vitals')

# Constants
ALERTS_FILE = "alerts.csv"
FLASK_API_URL = "https://flask-vitals.onrender.com"

# Initialize session state
if "alerts_viewed" not in st.session_state:
    st.session_state.alerts_viewed = False

# Load data from Firestore
def load_data():
    try:
        docs = vitals_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
        data = [doc.to_dict() for doc in docs]
        if not data:
            st.warning("No data available in Firestore.")
            return pd.DataFrame(columns=["Timestamp", "Temperature", "Blood Oxygen", "Heart Rate", "Respiration Rate", "Blood Pressure"])
        
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["temperature"] = pd.to_numeric(df["temperature"], errors='coerce')
        df["blood_oxygen"] = pd.to_numeric(df["blood_oxygen"], errors='coerce')
        df["heart_rate"] = pd.to_numeric(df["heart_rate"], errors='coerce')
        df["respiration_rate"] = pd.to_numeric(df["respiration_rate"], errors='coerce')
        df.rename(columns={"timestamp": "Timestamp", "temperature": "Temperature", 
                          "blood_oxygen": "Blood Oxygen", "heart_rate": "Heart Rate", 
                          "respiration_rate": "Respiration Rate", "blood_pressure": "Blood Pressure"}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Error fetching data from Firestore: {e}")
        return pd.DataFrame(columns=["Timestamp", "Temperature", "Blood Oxygen", "Heart Rate", "Respiration Rate", "Blood Pressure"])

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

# Home page
if page == "Home":
    st.title("Patient Vital Signs")
    df = load_data()
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
                st.success("Blood Pressure measurement saved to Firestore!")
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
# --- Auto Refresh Functionality ---
while True:
    time.sleep(10)
    st.rerun()
