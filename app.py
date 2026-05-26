"""
VitaTrack Streamlit Frontend
Update using firebase
Role-based page access:
  developer   -> All pages + Admin Panel
  admin       -> Admin Panel only
  doctor      -> Home, Alerts, Data Download
  nurse/paramedic/lab technician/other -> Home, Alerts, BP Measurement, Data Download
"""
# Imports
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import time, base64, json
import firebase_admin
from firebase_admin import credentials, auth as fb_auth, db as fb_db
import pyrebase

st.set_page_config(
    page_title="VitaTrack", page_icon="🩺",
    layout="wide", initial_sidebar_state="expanded"
)

# Firebase Initialisation
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyADKFqN7GuwNQL21ono9L2pg2O6rq6Z-ZM",
    "authDomain": "vitatrack-4d6fb.firebaseapp.com",
    "databaseURL": "https://vitatrack-4d6fb-default-rtdb.firebaseio.com",
    "projectId": "vitatrack-4d6fb",
    "storageBucket": "vitatrack-4d6fb.firebasestorage.app",
    "messagingSenderId": "24157234689",
    "appId": "1:24157234689:web:06d4e172b28d8681240200"
}

SERVICE_ACCOUNT = {
    "type": "service_account",
    "project_id": "vitatrack-4d6fb",
    "private_key_id": "56459cb5448342e99a3d98d1fc2af67f8ee1663d",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDFiD6gFSa32w4A\n8MnA+X5uPVhAs8CascXDEwPm/syKPJ1GoNYLUWFWRFELA00Sseaz8MmqttgwO+sW\nelJm3jWbqPresVOKI6JDGoYmjf7IJJRfdzyLJai96lbaymw1mdsbBUeo1niHwmYY\n1Tw0sOwvYImfgUMwSXlkDs1yG0PV8215I+9aR9Qd+Mt/C6ZWh88V4v7zb8UdXypb\n51cRl59iTb3Rj1F4CBaDJebBlATy6KyXngAqUwfzn0K3n5+tkRF+1qjEqMiOKGU0\nVqZbTMEthedEFDq2H7yMyYeuLtKoqqIW4w8Ly/YvkVUjSXUzSnIjRKWZeNhgpIuR\n6cINqgQPAgMBAAECggEAYXpDlVH6wl4aQgKRPWahqpshMwTBdlVmB0cZ9OMmYs1Y\nu6LhHcKyKxUZfTrKzP/3njKkAleqxdq7v2LryRG9GKzB6CVP2WqOR1kOfHY0FeZf\nReEcgno6FEZRSDT+Q1FCm8n2O+5imnQnV/fadxIb66FTKOBsHKcVfXgEkFu+FRTl\nd3EjB9bYxwrU5jZ3CGsjNw7+H378DT9XdXQ+z8UWiPWnhcYlrofWcDIu2kkczsNK\nNqyhfBOU5u1hZxRpixvPV33vet25tzZFaykaGXLB2tR8p6jXZWW50sGoUDQ+uZOS\nsMy+EX75lg36PKUtzDkdt+w2c5N5QZk3ynA92uhZSQKBgQD5q1nRfG4C26GqsKlV\nVtQOW+KIK1enMMjbGfn2BDA6wq3QYW8dbh8UR4f6usNOCLem9T4AqpWGKk+R2c4+\nFN0vhY4xqCLdSnvUe8B/40VslRpuD4SdOEBNvq6Sl7VeC0v0A2nYiLfPHHFhPHN3\njbxyFMcwD3wtfzm+RTCROL3SNQKBgQDKinZPWPbCk5TtE7rsF1AtR7ze7o40xFM2\nAhsQ7hciRjE1HmQz+FNO51F23w4lqeRT1VA8mimEJCYnpSKpf4UrPRYZJXVQtji2\n/WKeCc3qdS04kKHD7Z318/xc4wSvNzdOMNxhmFLwXIvA75JM802JH6jfnkiGRSSI\nGpPXpyEFswKBgDelkGRXlnF+oF7Z9zP1IVh99FSjTGsQPYRQGt1Re6ptH651OP3X\nQIgVlWI15DftS3mj6YjefGsl3QxF/mjp346q9tFshzDJXCY02ufmMOANr5FeVhFw\nqyxo1qIHvD3UyL3/UMUZW9aGoWKpxZac+aZ3qRm2Kdg+JhGZfESx3+UNAoGAbaG5\nHIYZO4VK7XDqkvSjj37vOvSBwQoryGYnZGib2Q+JfykuL/tQjLslG2TtcXGeh8pF\nHiiMJFy00mzOcFT4LklodsAR2lhoJpTNFqJT9X7rtVyEU1uBTyp8BYNUe8s1gnts\nLt+WtUhC1XJYDJL9+yVJ8ZDpzNQMTCemsupiM4UCgYBPgHoY1xv4wqvcoYe6Eebn\n5Fgf90BpMquEcw8rZ1IItoGEr+bBexPKwPtX7fUa7px4IWzzm1PUwlnsHPHa+Ab+\nFsRcmz5aPRGSyyE/UsyO9/zcrw8wxHP4yCKlik0VeKK/uK1R+F43ksi2Vn0EMdEn\n0cSufhZen3MclRbw74ypIw==\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@vitatrack-4d6fb.iam.gserviceaccount.com",
    "client_id": "101280254139902814972",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40vitatrack-4d6fb.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

DATABASE_URL = "https://vitatrack-4d6fb-default-rtdb.firebaseio.com"
POSTS = ["Doctor","Nurse","Paramedic","Lab Technician","Physiotherapist","Other"]

ROLE_PAGES = {
    "developer":      ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download","👥 Admin Panel","⚙️ My Profile"],
    "admin":          ["👥 Admin Panel","⚙️ My Profile"],
    "doctor":         ["🏠 Home","🔔 Alerts","📥 Data Download","⚙️ My Profile"],
    "nurse":          ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download","⚙️ My Profile"],
    "paramedic":      ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download","⚙️ My Profile"],
    "lab technician": ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download","⚙️ My Profile"],
    "physiotherapist":["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download","⚙️ My Profile"],
    "other":          ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download","⚙️ My Profile"],
    "staff":          ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download","⚙️ My Profile"],
}

def allowed_pages(user):
    role = user.get("role","other").lower()
    post = user.get("post","other").lower()
    if role == "staff":
        return ROLE_PAGES.get(post, ROLE_PAGES["other"])
    return ROLE_PAGES.get(role, ROLE_PAGES["other"])

@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT)
        firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
    pb = pyrebase.initialize_app({
        "apiKey": FIREBASE_CONFIG["apiKey"],
        "authDomain": FIREBASE_CONFIG["authDomain"],
        "databaseURL": FIREBASE_CONFIG["databaseURL"],
        "storageBucket": FIREBASE_CONFIG["storageBucket"],
    })
    return pb

pb_app  = init_firebase()
pb_auth = pb_app.auth()

# Db and Auth Helpers
def db_get(path):
    try:
        return fb_db.reference(path).get()
    except Exception as e:
        return None

def db_set(path, data):
    try:
        fb_db.reference(path).set(data); return True
    except Exception:
        return False

def db_update(path, data):
    try:
        fb_db.reference(path).update(data); return True
    except Exception:
        return False

def db_push(path, data):
    try:
        fb_db.reference(path).push(data); return True
    except Exception:
        return False

def db_delete(path):
    try:
        fb_db.reference(path).delete(); return True
    except Exception:
        return False

def login_user(email, password):
    try:
        user = pb_auth.sign_in_with_email_and_password(email, password)
        uid  = user["localId"]
        profile = db_get(f"/vitatrack/users/{uid}")
        if not profile:
            return None, "User profile not found."
        if not profile.get("approved", False):
            return None, "Account pending admin approval."
        profile["uid"] = uid
        return profile, None
    except Exception as e:
        msg = str(e)
        if "INVALID_PASSWORD" in msg or "EMAIL_NOT_FOUND" in msg or "INVALID_LOGIN_CREDENTIALS" in msg:
            return None, "Invalid email or password."
        return None, "Login failed."

def signup_user(full_name, email, password, post, photo_b64=None):
    try:
        fb_user = fb_auth.create_user(email=email, password=password, display_name=full_name)
        uid = fb_user.uid
        db_set(f"/vitatrack/users/{uid}", {
            "full_name":  full_name,
            "email":      email,
            "role":       "staff",
            "post":       post,
            "approved":   False,
            "created_at": datetime.now().isoformat(),
            "photo_b64":  photo_b64 or ""
        })
        return uid, None
    except Exception as e:
        msg = str(e)
        if "EMAIL_EXISTS" in msg:
            return None, "Email already registered."
        return None, f"Signup failed: {msg}"

# Vitals, Alerts, Chart Helpers
def load_vitals(device_id=None):
    try:
        if device_id:
            data = db_get(f"/vitatrack/devices/{device_id}/vitals/history")
        else:
            devices = db_get("/vitatrack/devices") or {}
            data = {}
            for did, ddata in devices.items():
                h = (ddata or {}).get("vitals", {}).get("history", {})
                data.update(h or {})
        if not data:
            return pd.DataFrame()
        rows = [v for v in data.values() if isinstance(v, dict)]
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        for col in ["heart_rate","blood_oxygen","temperature","respiration_rate"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")
            mask = df["Timestamp"].isna()
            df.loc[mask, "Timestamp"] = pd.to_datetime(df.loc[mask, "timestamp"], errors="coerce")
        df = df.sort_values("Timestamp") if "Timestamp" in df.columns else df
        return df
    except Exception as e:
        return pd.DataFrame()

def load_latest(device_id):
    return db_get(f"/vitatrack/devices/{device_id}/vitals/latest") or {}

def load_alerts():
    try:
        data = db_get("/vitatrack/alerts") or {}
        rows = []
        for device_id, alerts in data.items():
            if isinstance(alerts, dict):
                for key, alert in alerts.items():
                    if isinstance(alert, dict):
                        alert["_key"] = key
                        alert["device_id"] = device_id
                        rows.append(alert)
        return rows
    except Exception:
        return []

def save_alert(device_id, message):
    db_push(f"/vitatrack/alerts/{device_id}", {
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "dismissed": False
    })

def dismiss_alert(device_id, key):
    db_update(f"/vitatrack/alerts/{device_id}/{key}", {"dismissed": True})

def clear_all_alerts():
    db_delete("/vitatrack/alerts")

CHART_CFG = {
    "heart_rate":       ("#ef4444","#fff5f5","Heart Rate","bpm"),
    "blood_oxygen":     ("#3b82f6","#eff6ff","Blood Oxygen","%"),
    "temperature":      ("#f59e0b","#fffbeb","Temperature","°C"),
    "respiration_rate": ("#10b981","#f0fdf4","Respiration","br/m"),
}

def make_chart(df, col):
    if col not in df.columns or "Timestamp" not in df.columns:
        return None
    color, bg, label, unit = CHART_CFG[col]
    fig, ax = plt.subplots(figsize=(5.5, 2.8))
    fig.patch.set_facecolor(bg); ax.set_facecolor(bg)
    ax.plot(df["Timestamp"], df[col], color=color, linewidth=2.2,
            marker="o", markersize=4, markerfacecolor=color)
    ax.fill_between(df["Timestamp"], df[col], alpha=0.15, color=color)
    ax.set_xlabel("Time", fontsize=9, color="#64748b")
    ax.set_ylabel(f"{label} ({unit})", fontsize=9, color="#64748b")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.tick_params(colors="#64748b", labelsize=8)
    for s in ax.spines.values(): s.set_edgecolor("#e2e8f0")
    ax.grid(True, linestyle="--", alpha=0.4, color="#e2e8f0")
    fig.tight_layout()
    return fig

ALERT_SOUND_JS = """<script>
(function(){var c=new(window.AudioContext||window.webkitAudioContext)();
function b(f,d){var o=c.createOscillator(),g=c.createGain();
o.connect(g);g.connect(c.destination);o.frequency.value=f;
g.gain.value=0.3;o.start();o.stop(c.currentTime+d);}
b(880,0.18);setTimeout(function(){b(660,0.18)},220);
setTimeout(function(){b(880,0.35)},440);})();
</script>"""

def play_alert_sound():
    st.components.v1.html(ALERT_SOUND_JS, height=0)

for k, v in {
    "logged_in":False,"user":None,"auth_page":"login",
    "last_alert_count":0,"flash_active":False,"nav_page":None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
section[data-testid="stSidebar"]{background:#0f172a;}
section[data-testid="stSidebar"] *{color:#f8fafc !important;}
section[data-testid="stSidebar"] hr{border-color:#1e293b !important;}
.metric-card{background:#fff;border-radius:12px;padding:20px 24px;
    box-shadow:0 2px 8px rgba(0,0,0,0.07);margin-bottom:16px;border-left:5px solid #3b82f6;}
.metric-card.alert-card{border-left-color:#ef4444;background:#fff5f5;}
.metric-card .label{font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:.5px;}
.metric-card .value{font-size:34px;font-weight:800;color:#0f172a;line-height:1.1;}
.metric-card .status{font-size:13px;font-weight:600;margin-top:4px;}
.status-normal{color:#16a34a;}.status-warning{color:#ef4444;}
@keyframes flash{0%{background:#fff5f5}50%{background:#fca5a5}100%{background:#fff5f5}}
.flash{animation:flash 1s ease-in-out 3;}
.alert-item{display:flex;align-items:flex-start;gap:14px;background:#fff5f5;
    border:1px solid #fecaca;border-radius:10px;padding:14px 18px;margin-bottom:10px;}
.alert-title{font-weight:600;color:#b91c1c;font-size:15px;}
.alert-time{font-size:12px;color:#94a3b8;margin-top:2px;}
.badge{display:inline-block;background:#ef4444;color:#fff;border-radius:999px;
    font-size:11px;font-weight:700;padding:2px 8px;margin-left:6px;vertical-align:middle;}
.header-bar{display:flex;align-items:center;gap:14px;margin-bottom:24px;
    padding-bottom:16px;border-bottom:1px solid #e2e8f0;}
.header-logo{font-size:32px;}.header-title{font-size:26px;font-weight:800;color:#0f172a;}
.header-sub{font-size:14px;color:#64748b;}
.chart-box{background:#fff;border-radius:12px;padding:16px;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:16px;}
.patient-card{background:#fff;border-radius:12px;padding:18px 22px;
    box-shadow:0 2px 8px rgba(0,0,0,0.07);margin-bottom:14px;border-left:5px solid #8b5cf6;}
.patient-name{font-size:18px;font-weight:700;color:#0f172a;}
.patient-meta{font-size:13px;color:#64748b;margin-top:2px;}
.pill{display:inline-block;border-radius:999px;font-size:12px;font-weight:600;padding:3px 10px;}
.pill-green{background:#dcfce7;color:#16a34a;}.pill-yellow{background:#fef9c3;color:#ca8a04;}
.profile-chip{display:flex;align-items:center;gap:10px;background:#1e293b;
    border-radius:10px;padding:10px 14px;margin-bottom:12px;}
.pc-name{font-size:14px;font-weight:600;}.pc-post{font-size:12px;color:#94a3b8 !important;}
.photo-preview{border-radius:12px;object-fit:cover;width:110px;height:110px;
    border:3px solid #3b82f6;display:block;margin:8px auto;}
.admin-table{width:100%;border-collapse:collapse;font-size:14px;}
.admin-table th{background:#f1f5f9;padding:10px 14px;text-align:left;font-weight:600;color:#475569;}
.admin-table td{padding:10px 14px;border-bottom:1px solid #f1f5f9;}
.role-badge{display:inline-block;border-radius:6px;font-size:11px;font-weight:700;padding:2px 8px;margin-left:6px;}
.role-developer{background:#7c3aed;color:#fff;}.role-admin{background:#0f172a;color:#fff;}
.role-doctor{background:#1d4ed8;color:#fff;}.role-nurse{background:#0891b2;color:#fff;}
.role-other{background:#475569;color:#fff;}
</style>
""", unsafe_allow_html=True)

# Login, Signup pages
def render_login():
    _, col, _ = st.columns([1,2,1])
    with col:
        st.markdown("""
        <div style='text-align:center;padding:40px 0 20px'>
            <div style='font-size:56px'>🩺</div>
            <div style='font-size:30px;font-weight:800;color:#0f172a'>VitaTrack</div>
            <div style='font-size:15px;color:#64748b;margin-top:4px'>Patient Monitoring System</div>
        </div>""", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### Sign In")
            email    = st.text_input("Email address", placeholder="you@hospital.com")
            password = st.text_input("Password", type="password")
            if st.button("Sign In →", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Signing in..."):
                        user, err = login_user(email, password)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user      = user
                        st.session_state.nav_page  = allowed_pages(user)[0]
                        st.rerun()
            st.markdown("<hr style='margin:16px 0'>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;font-size:14px;color:#64748b'>New staff member?</div>",
                        unsafe_allow_html=True)
            if st.button("Create Account", use_container_width=True):
                st.session_state.auth_page = "signup"; st.rerun()

def render_signup():
    _, col, _ = st.columns([1,2,1])
    with col:
        st.markdown("""
        <div style='text-align:center;padding:28px 0 14px'>
            <div style='font-size:44px'>🩺</div>
            <div style='font-size:26px;font-weight:800;color:#0f172a'>Create Account</div>
            <div style='font-size:14px;color:#64748b;margin-top:4px'>Medical Personnel Registration</div>
        </div>""", unsafe_allow_html=True)
        with st.container(border=True):
            c1, c2    = st.columns(2)
            full_name = c1.text_input("Full Name *")
            post      = c2.selectbox("Role / Post *", POSTS)
            email     = st.text_input("Email Address *")
            c3, c4    = st.columns(2)
            pw        = c3.text_input("Password *", type="password")
            pw2       = c4.text_input("Confirm Password *", type="password")
            st.markdown("**Passport Photo** *(required)*")
            photo_file = st.file_uploader("Upload passport-style photo",
                                          type=["jpg","jpeg","png"],
                                          label_visibility="collapsed")
            if photo_file:
                raw = photo_file.read()
                b64p = base64.b64encode(raw).decode()
                st.markdown(f'<div style="text-align:center"><img src="data:image/jpeg;base64,{b64p}" class="photo-preview"/><div style="font-size:12px;color:#16a34a;margin-top:4px">✓ Photo ready</div></div>',
                            unsafe_allow_html=True)
                photo_file.seek(0)
            if st.button("Register →", use_container_width=True, type="primary"):
                if not all([full_name, email, pw, pw2]):
                    st.error("Please fill in all required fields.")
                elif pw != pw2:
                    st.error("Passwords do not match.")
                elif len(pw) < 6:
                    st.error("Password must be at least 6 characters.")
                elif not photo_file:
                    st.error("Please upload a passport photo.")
                else:
                    photo_b64 = base64.b64encode(photo_file.read()).decode()
                    with st.spinner("Creating account..."):
                        uid, err = signup_user(full_name, email, pw, post, photo_b64)
                    if err:
                        st.error(err)
                    else:
                        st.success("✅ Account created! Awaiting admin approval.")
                        time.sleep(2)
                        st.session_state.auth_page = "login"; st.rerun()
            st.markdown("<hr style='margin:14px 0'>", unsafe_allow_html=True)
            if st.button("← Back to Sign In", use_container_width=True):
                st.session_state.auth_page = "login"; st.rerun()

# Homepage
def page_home():
    st.markdown('<div class="header-bar"><div class="header-logo">🩺</div><div><div class="header-title">VitaTrack</div><div class="header-sub">Real-time Patient Vital Signs Monitoring</div></div></div>',
                unsafe_allow_html=True)
    patients    = db_get("/vitatrack/patients") or {}
    pat_list    = [{"id":k,**v} for k,v in patients.items() if isinstance(v,dict)]
    device_id   = None
    if pat_list:
        names    = {p["name"]: p for p in pat_list}
        selected = st.selectbox("Viewing patient:", list(names.keys())) if len(names)>1 else list(names.keys())[0]
        pat      = names[selected]
        device_id = pat.get("device_id")
        dev_tag  = f'<span class="pill pill-green">📡 {device_id}</span>' if device_id else '<span class="pill pill-yellow">No device</span>'
        assigned = pat.get("assigned_to",[])
        all_u    = db_get("/vitatrack/users") or {}
        staff_names = [all_u.get(uid,{}).get("full_name","?") for uid in assigned if isinstance(assigned,list)]
        st.markdown(f'<div class="patient-card"><div class="patient-name">🧑‍⚕️ {pat["name"]}</div><div class="patient-meta">Age: {pat.get("age","—")} &nbsp;·&nbsp; Gender: {pat.get("gender","—")} &nbsp;·&nbsp; Diagnosis: {pat.get("diagnosis","—")} &nbsp;{dev_tag}</div><div style="font-size:12px;color:#94a3b8;margin-top:6px">👩‍⚕️ {", ".join(staff_names) if staff_names else "No staff assigned"}</div></div>',
                    unsafe_allow_html=True)
    if not device_id:
        st.warning("No device assigned. Configure in Admin Panel.")
        return
    latest = load_latest(device_id)
    df     = load_vitals(device_id)
    if not latest:
        st.warning("No vitals data yet. Waiting for sensor readings...")
    else:
        st.markdown(f'<div class="last-updated">Last updated: {datetime.now().strftime("%d %b %Y, %H:%M:%S")}</div>',
                    unsafe_allow_html=True)
        vitals_cfg = [
            ("heart_rate","bpm",60.0,100.0,"❤️","Heart Rate"),
            ("blood_oxygen","%",90.0,100.0,"🫁","Blood Oxygen"),
            ("temperature","°C",36.0,38.0,"🌡️","Temperature"),
            ("respiration_rate","breaths/min",12.0,20.0,"🌬️","Respiration Rate"),
        ]
        cols = st.columns(4)
        for i,(key,unit,lo,hi,icon,label) in enumerate(vitals_cfg):
            val      = latest.get(key)
            is_alert = val is not None and (float(val)<lo or float(val)>hi)
            if is_alert: save_alert(device_id, f"{label} out of range ({val} {unit})")
            card_cls = "metric-card alert-card flash" if (is_alert and st.session_state.flash_active) else "metric-card"
            status   = f"⚠️ Out of range [{lo}–{hi}]" if is_alert else f"✓ Normal [{lo}–{hi}]"
            scls     = "status-warning" if is_alert else "status-normal"
            val_str  = f"{float(val):.1f}" if val is not None else "—"
            with cols[i]:
                st.markdown(f'<div class="{card_cls}"><div class="label">{icon} {label}</div><div class="value">{val_str} <span style="font-size:18px;color:#64748b">{unit}</span></div><div class="status {scls}">{status}</div></div>',
                            unsafe_allow_html=True)
        st.session_state.flash_active = False
        if not df.empty:
            st.markdown('<div class="section-title">Trend Charts</div><div class="section-sub">Last 10 readings</div>',
                        unsafe_allow_html=True)
            display_df = df.tail(10)
            c1, c2 = st.columns(2)
            for col_name, col_widget in [("heart_rate",c1),("blood_oxygen",c2),("temperature",c1),("respiration_rate",c2)]:
                fig = make_chart(display_df, col_name)
                if fig:
                    with col_widget:
                        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
                        st.pyplot(fig)
                        st.markdown('</div>', unsafe_allow_html=True)
    with st.spinner("⏱ Refreshing in 10s..."):
        time.sleep(10)
    st.rerun()

# Alerts, BP Download, Profile, Admin, Router
def page_alerts():
    st.markdown('<div class="header-bar"><div class="header-logo">🔔</div><div><div class="header-title">Alerts & Notifications</div><div class="header-sub">Triggered vital sign alerts</div></div></div>',
                unsafe_allow_html=True)
    all_alerts = load_alerts()
    active     = [a for a in all_alerts if not a.get("dismissed")]
    c1,c2 = st.columns([3,1])
    c1.markdown(f"**{len(active)} active** · {len(all_alerts)-len(active)} dismissed")
    with c2:
        if st.button("🗑️ Clear All", use_container_width=True):
            clear_all_alerts(); st.rerun()
    st.markdown("---")
    if not active:
        st.markdown('<div style="text-align:center;padding:50px;color:#64748b"><div style="font-size:48px">✅</div><div style="font-size:18px;font-weight:600;margin-top:12px">No active alerts</div></div>',
                    unsafe_allow_html=True)
        return
    icons = {"Heart Rate":"❤️","Blood Oxygen":"🫁","Temperature":"🌡️","Respiration":"🌬️","BP":"💓"}
    for a in active:
        icon = next((v for k,v in icons.items() if k in a.get("message","")), "⚠️")
        ts   = a.get("timestamp","")
        try: ts = datetime.fromisoformat(ts).strftime("%d %b %Y, %H:%M:%S")
        except Exception: pass
        cm,cb = st.columns([5,1])
        with cm:
            st.markdown(f'<div class="alert-item"><div style="font-size:22px">{icon}</div><div><div class="alert-title">{a.get("message","Alert")}</div><div class="alert-time">{ts} · {a.get("device_id","")}</div></div></div>',
                        unsafe_allow_html=True)
        with cb:
            if st.button("Dismiss", key=f"d_{a.get('_key','')}_{a.get('device_id','')}"):
                dismiss_alert(a.get("device_id",""), a.get("_key","")); st.rerun()


def page_bp():
    st.markdown('<div class="header-bar"><div class="header-logo">💉</div><div><div class="header-title">Blood Pressure Measurement</div><div class="header-sub">Manually log a BP reading</div></div></div>',
                unsafe_allow_html=True)
    patients  = db_get("/vitatrack/patients") or {}
    pat_names = {p.get("name","?"): {"id":k,**p} for k,p in patients.items() if isinstance(p,dict)}
    def classify_bp(s,d):
        if s<120 and d<80: return "Normal","#16a34a"
        elif s<130 and d<80: return "Elevated","#ca8a04"
        elif s<140 or d<90: return "High Stage 1","#ea580c"
        else: return "High Stage 2","#dc2626"
    cf,ci = st.columns(2)
    with cf:
        st.markdown("#### Enter Reading")
        if not pat_names: st.warning("No patients found."); return
        sel_pat   = st.selectbox("Patient", list(pat_names.keys()))
        device_id = pat_names[sel_pat].get("device_id","")
        systolic  = st.number_input("Systolic (mmHg)",  50, 200, 120)
        diastolic = st.number_input("Diastolic (mmHg)", 30, 150, 80)
        cat,color = classify_bp(systolic, diastolic)
        st.markdown(f'<div style="background:#f8fafc;border-radius:8px;padding:10px 16px;margin:8px 0;border-left:4px solid {color};font-size:14px"><strong>Classification:</strong> <span style="color:{color};font-weight:700">{cat}</span></div>',
                    unsafe_allow_html=True)
        if st.button("💾 Save BP", use_container_width=True, type="primary"):
            if device_id:
                bp = f"{systolic}/{diastolic}"
                db_update(f"/vitatrack/devices/{device_id}/vitals/latest", {"blood_pressure":bp,"timestamp":datetime.now().isoformat()})
                db_push(f"/vitatrack/devices/{device_id}/vitals/history", {"blood_pressure":bp,"timestamp":datetime.now().isoformat()})
                st.success(f"✅ BP {bp} mmHg saved!")
                if systolic>=140 or diastolic>=90:
                    save_alert(device_id, f"High BP: {bp} mmHg"); play_alert_sound(); st.error("⚠️ High BP alert saved.")
            else: st.error("No device assigned to this patient.")
    with ci:
        st.markdown("#### BP Reference Guide")
        st.markdown('<table class="admin-table"><tr><th>Category</th><th>Systolic</th><th>Diastolic</th></tr><tr><td style="color:#16a34a;font-weight:600">Normal</td><td>&lt;120</td><td>&lt;80</td></tr><tr><td style="color:#ca8a04;font-weight:600">Elevated</td><td>120–129</td><td>&lt;80</td></tr><tr><td style="color:#ea580c;font-weight:600">High Stage 1</td><td>130–139</td><td>80–89</td></tr><tr><td style="color:#dc2626;font-weight:600">High Stage 2</td><td>≥140</td><td>≥90</td></tr></table>',
                    unsafe_allow_html=True)


def page_download():
    st.markdown('<div class="header-bar"><div class="header-logo">📥</div><div><div class="header-title">Download Patient Data</div><div class="header-sub">Export vitals from Firebase as CSV</div></div></div>',
                unsafe_allow_html=True)
    patients  = db_get("/vitatrack/patients") or {}
    pat_names = {p.get("name","?"): {"id":k,**p} for k,p in patients.items() if isinstance(p,dict)}
    if not pat_names: st.warning("No patients configured."); return
    sel = st.selectbox("Select patient", list(pat_names.keys()))
    did = pat_names[sel].get("device_id","")
    if not did: st.warning("No device assigned."); return
    df = load_vitals(did)
    if df.empty: st.warning("No data available."); return
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("Total Readings", len(df))
    if "Timestamp" in df.columns and not df["Timestamp"].isna().all():
        s2.metric("From", df["Timestamp"].min().strftime("%d %b %Y"))
        s3.metric("To",   df["Timestamp"].max().strftime("%d %b %Y"))
    s4.metric("Columns", len(df.columns))
    st.markdown("---")
    st.dataframe(df.tail(10), use_container_width=True, hide_index=True)
    st.markdown("---")
    st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode(),
                       f"vitatrack_{did}_{datetime.now().strftime('%Y%m%d')}.csv",
                       "text/csv", use_container_width=True)


def page_profile():
    user = st.session_state.user
    uid  = user.get("uid","")
    st.markdown('<div class="header-bar"><div class="header-logo">⚙️</div><div><div class="header-title">My Profile</div><div class="header-sub">Update your password and profile photo</div></div></div>',
                unsafe_allow_html=True)
    col_photo, col_details = st.columns([1,2])
    with col_photo:
        st.markdown("#### Current Photo")
        pb64 = user.get("photo_b64","")
        if pb64:
            st.markdown(f'<div style="text-align:center"><img src="data:image/jpeg;base64,{pb64}" class="photo-preview"/></div>', unsafe_allow_html=True)
        else:
            ini = "".join([n[0] for n in user.get("full_name","?").split()[:2]]).upper()
            st.markdown(f'<div style="text-align:center;padding:20px"><div style="width:110px;height:110px;border-radius:12px;background:#3b82f6;display:inline-flex;align-items:center;justify-content:center;font-size:40px;font-weight:700;color:#fff">{ini}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center"><div style="font-size:16px;font-weight:700">{user.get("full_name","")}</div><div style="font-size:13px;color:#64748b">{user.get("post","")}</div><div style="font-size:12px;color:#94a3b8">{user.get("email","")}</div></div>', unsafe_allow_html=True)
    with col_details:
        with st.container(border=True):
            st.markdown("#### 📷 Change Profile Photo")
            new_photo = st.file_uploader("Upload new photo", type=["jpg","jpeg","png"], label_visibility="collapsed")
            if new_photo:
                raw = new_photo.read()
                b64p = base64.b64encode(raw).decode()
                st.markdown(f'<div style="text-align:center"><img src="data:image/jpeg;base64,{b64p}" style="width:100px;height:100px;border-radius:12px;object-fit:cover;border:3px solid #3b82f6"/></div>', unsafe_allow_html=True)
                new_photo.seek(0)
                if st.button("💾 Save Photo", use_container_width=True, type="primary"):
                    photo_b64 = base64.b64encode(new_photo.read()).decode()
                    if db_update(f"/vitatrack/users/{uid}", {"photo_b64": photo_b64}):
                        st.session_state.user["photo_b64"] = photo_b64
                        st.success("✅ Photo updated!")
        st.markdown("")
        with st.container(border=True):
            st.markdown("#### 🔒 Change Password")
            new_pw  = st.text_input("New Password", type="password", key="np")
            conf_pw = st.text_input("Confirm New Password", type="password", key="cp")
            if new_pw:
                s = sum([len(new_pw)>=8, any(c.isupper() for c in new_pw), any(c.isdigit() for c in new_pw), any(c in "!@#$%^&*" for c in new_pw)])
                colors = ["#ef4444","#f59e0b","#3b82f6","#16a34a"]
                labels = ["Weak","Fair","Good","Strong"]
                st.markdown(f'<div style="margin:8px 0"><div style="background:#f1f5f9;border-radius:4px;height:6px"><div style="width:{s*25}%;height:100%;background:{colors[s-1]};border-radius:4px"></div></div><div style="font-size:12px;color:{colors[s-1]};font-weight:600;margin-top:4px">{labels[s-1]}</div></div>', unsafe_allow_html=True)
            if st.button("🔒 Update Password", use_container_width=True, type="primary"):
                if not new_pw or not conf_pw: st.error("Fill in both fields.")
                elif new_pw != conf_pw: st.error("Passwords do not match.")
                elif len(new_pw) < 6: st.error("Min 6 characters.")
                else:
                    try:
                        fb_auth.update_user(uid, password=new_pw)
                        st.success("✅ Password updated!")
                    except Exception as e:
                        st.error(f"Failed: {e}")


def page_admin():
    st.markdown('<div class="header-bar"><div class="header-logo">👥</div><div><div class="header-title">Admin Panel</div><div class="header-sub">Manage staff, patients & devices</div></div></div>',
                unsafe_allow_html=True)
    tab1,tab2,tab3 = st.tabs(["👤 Staff Management","🧑‍⚕️ Patients","📡 Devices"])

    with tab1:
        all_users = db_get("/vitatrack/users") or {}
        staff     = [(uid,u) for uid,u in all_users.items() if isinstance(u,dict) and u.get("role") not in ("admin","developer")]
        pending   = [(uid,u) for uid,u in staff if not u.get("approved")]
        approved  = [(uid,u) for uid,u in staff if u.get("approved")]
        if pending:
            st.markdown(f"#### 🟡 Pending Approval ({len(pending)})")
            for uid,u in pending:
                with st.container(border=True):
                    ci,cn,ca = st.columns([1,4,2])
                    with ci:
                        pb64 = u.get("photo_b64","")
                        if pb64: st.markdown(f'<img src="data:image/jpeg;base64,{pb64}" style="width:60px;height:60px;border-radius:50%;object-fit:cover;border:2px solid #f59e0b"/>', unsafe_allow_html=True)
                        else:
                            ini = "".join([n[0] for n in u.get("full_name","?").split()[:2]]).upper()
                            st.markdown(f'<div style="width:60px;height:60px;border-radius:50%;background:#f59e0b;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;color:#fff">{ini}</div>', unsafe_allow_html=True)
                    with cn:
                        st.markdown(f"**{u.get('full_name','')}** · {u.get('post','')}")
                        st.caption(u.get("email",""))
                        st.caption(f"Registered: {str(u.get('created_at',''))[:10]}")
                    with ca:
                        if st.button("✅ Approve", key=f"app_{uid}", use_container_width=True):
                            db_update(f"/vitatrack/users/{uid}", {"approved":True}); st.rerun()
                        if st.button("❌ Reject", key=f"rej_{uid}", use_container_width=True):
                            db_delete(f"/vitatrack/users/{uid}")
                            try: fb_auth.delete_user(uid)
                            except Exception: pass
                            st.rerun()
        else:
            st.info("No pending approvals.")
        st.markdown(f"#### ✅ Approved Staff ({len(approved)})")
        for uid,u in approved:
            with st.container(border=True):
                ci2,cn2 = st.columns([1,5])
                with ci2:
                    pb64 = u.get("photo_b64","")
                    if pb64: st.markdown(f'<img src="data:image/jpeg;base64,{pb64}" style="width:54px;height:54px;border-radius:50%;object-fit:cover;border:2px solid #10b981"/>', unsafe_allow_html=True)
                    else:
                        ini = "".join([n[0] for n in u.get("full_name","?").split()[:2]]).upper()
                        st.markdown(f'<div style="width:54px;height:54px;border-radius:50%;background:#10b981;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:700;color:#fff">{ini}</div>', unsafe_allow_html=True)
                with cn2:
                    st.markdown(f"**{u.get('full_name','')}** &nbsp;<span class='pill pill-green'>{u.get('post','')}</span>", unsafe_allow_html=True)
                    st.caption(u.get("email",""))

    with tab2:
        patients = db_get("/vitatrack/patients") or {}
        all_u    = db_get("/vitatrack/users") or {}
        approved_staff = {uid:u for uid,u in all_u.items() if isinstance(u,dict) and u.get("approved") and u.get("role") not in ("admin","developer")}
        st.markdown("#### ➕ Add New Patient")
        with st.expander("Create patient profile", expanded=not bool(patients)):
            pc1,pc2 = st.columns(2)
            p_name  = pc1.text_input("Patient Name *")
            p_age   = pc2.number_input("Age *",0,120,30)
            pc3,pc4 = st.columns(2)
            p_gender = pc3.selectbox("Gender *",["Male","Female","Other"])
            p_diag   = pc4.text_input("Diagnosis *")
            p_notes  = st.text_area("Notes",height=70)
            if st.button("Create Patient", type="primary"):
                if not all([p_name,p_diag]): st.error("Name and diagnosis required.")
                else:
                    import uuid; pid = str(uuid.uuid4())[:8]
                    db_set(f"/vitatrack/patients/{pid}", {"name":p_name,"age":p_age,"gender":p_gender,"diagnosis":p_diag,"notes":p_notes,"device_id":"","assigned_to":[],"created_at":datetime.now().isoformat()})
                    st.success(f"✅ Patient '{p_name}' created!"); st.rerun()
        st.markdown(f"#### 🧑‍⚕️ Patients ({len(patients)})")
        for pid,pat in patients.items():
            if not isinstance(pat,dict): continue
            with st.container(border=True):
                ph1,ph2 = st.columns([3,2])
                with ph1:
                    did     = pat.get("device_id","")
                    dev_tag = f'<span class="pill pill-green">📡 {did}</span>' if did else '<span class="pill pill-yellow">No device</span>'
                    assigned_ids   = pat.get("assigned_to",[])
                    assigned_names = [all_u.get(uid,{}).get("full_name","?") for uid in assigned_ids]
                    st.markdown(f'<div class="patient-name">{pat.get("name","")}</div><div class="patient-meta">{pat.get("age","—")} yrs · {pat.get("gender","—")} · {pat.get("diagnosis","—")} &nbsp;{dev_tag}</div>', unsafe_allow_html=True)
                    if pat.get("notes"): st.caption(f"📝 {pat['notes']}")
                    if assigned_names:   st.caption(f"👩‍⚕️ {', '.join(assigned_names)}")
                with ph2:
                    staff_opt = {u.get("full_name","?"): uid for uid,u in approved_staff.items()}
                    defaults  = [u.get("full_name","?") for uid,u in approved_staff.items() if uid in assigned_ids]
                    sel = st.multiselect("Assign staff", list(staff_opt.keys()), default=defaults, key=f"ms_{pid}")
                    if st.button("💾 Save", key=f"sv_{pid}", use_container_width=True):
                        db_update(f"/vitatrack/patients/{pid}", {"assigned_to":[staff_opt[n] for n in sel]})
                        st.success("Saved!"); st.rerun()

    with tab3:
        devices  = db_get("/vitatrack/device_registry") or {}
        patients = db_get("/vitatrack/patients") or {}
        st.markdown("#### ➕ Register New Device")
        with st.expander("Add a device", expanded=not bool(devices)):
            dc1,dc2 = st.columns(2)
            dev_id_in = dc1.text_input("Device ID *", placeholder="e.g. ESP32-001")
            dev_lbl   = dc2.text_input("Label", placeholder="e.g. Bed 3 Sensor")
            if st.button("Register Device", type="primary"):
                if not dev_id_in: st.error("Device ID required.")
                elif dev_id_in in devices: st.error("Device ID already exists.")
                else:
                    db_set(f"/vitatrack/device_registry/{dev_id_in}", {"label":dev_lbl,"patient_id":"","active":True,"created_at":datetime.now().isoformat()})
                    st.success(f"✅ '{dev_id_in}' registered!"); st.rerun()
        st.markdown(f"#### 📡 Registered Devices ({len(devices)})")
        p_id2name = {pid:p.get("name","?") for pid,p in patients.items() if isinstance(p,dict)}
        p_name2id = {v:k for k,v in p_id2name.items()}; p_name2id["— Unassigned —"] = ""
        for dev_id,dev in devices.items():
            if not isinstance(dev,dict): continue
            with st.container(border=True):
                dh1,dh2 = st.columns([3,2])
                with dh1:
                    cur_pid  = dev.get("patient_id","")
                    cur_name = p_id2name.get(cur_pid,"Unassigned")
                    pill_cls = "pill-green" if cur_pid else "pill-yellow"
                    st.markdown(f'<div style="font-size:16px;font-weight:700">📡 {dev_id}</div><div style="font-size:13px;color:#64748b;margin-top:2px">{dev.get("label","No label")} &nbsp;<span class="pill {pill_cls}">{cur_name}</span></div>', unsafe_allow_html=True)
                    st.caption(f"Registered: {str(dev.get('created_at',''))[:10]}")
                with dh2:
                    all_p = list(p_name2id.keys())
                    cur_i = all_p.index(cur_name) if cur_name in all_p else 0
                    sel_p = st.selectbox("Assign to patient", all_p, index=cur_i, key=f"dp_{dev_id}")
                    if st.button("💾 Assign", key=f"da_{dev_id}", use_container_width=True):
                        new_pid = p_name2id[sel_p]
                        db_update(f"/vitatrack/device_registry/{dev_id}", {"patient_id":new_pid})
                        if new_pid: db_update(f"/vitatrack/patients/{new_pid}", {"device_id":dev_id})
                        if cur_pid and cur_pid != new_pid: db_update(f"/vitatrack/patients/{cur_pid}", {"device_id":""})
                        st.success("Assigned!"); st.rerun()

def render_sidebar(pages):
    with st.sidebar:
        user = st.session_state.user
        pb64 = user.get("photo_b64", "")
        ini  = "".join([n[0] for n in user.get("full_name", "?").split()[:2]]).upper()

        if pb64:
            st.markdown(
                f'<div class="profile-chip">'
                f'<img src="data:image/jpeg;base64,{pb64}" '
                f'style="width:40px;height:40px;border-radius:50%;object-fit:cover;border:2px solid #3b82f6"/>'
                f'<div><div class="pc-name">{user.get("full_name","")}</div>'
                f'<div class="pc-post">{user.get("post","")}</div></div></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="profile-chip">'
                f'<div style="width:40px;height:40px;border-radius:50%;background:#3b82f6;'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-size:16px;font-weight:700;color:#fff;flex-shrink:0">{ini}</div>'
                f'<div><div class="pc-name">{user.get("full_name","")}</div>'
                f'<div class="pc-post">{user.get("post","")}</div></div></div>',
                unsafe_allow_html=True
            )

        st.markdown(
            f'<div style="font-size:11px;color:#94a3b8;padding:0 4px 12px">'
            f'{user.get("email","")}</div>',
            unsafe_allow_html=True
        )
        st.markdown("---")

        # Alert badge count
        all_alerts = load_alerts()
        active_count = len([a for a in all_alerts if not a.get("dismissed")])
        if active_count != st.session_state.last_alert_count:
            if active_count > st.session_state.last_alert_count:
                st.session_state.flash_active = True
                play_alert_sound()
            st.session_state.last_alert_count = active_count

        selected = None
        for p in pages:
            label = p
            if p == "🔔 Alerts" and active_count > 0:
                label = f"{p}  🔴 {active_count}"
            if st.button(label, key=f"nav_{p}", use_container_width=True):
                st.session_state.nav_page = p
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            for k in ["logged_in", "user", "nav_page", "last_alert_count", "flash_active"]:
                st.session_state[k] = False if k == "logged_in" else None if k in ["user","nav_page"] else 0
            st.session_state.auth_page = "login"
            st.rerun()

    return st.session_state.nav_page
# ── Main router ───────────────────────────────────────────────
if not st.session_state.logged_in:
    if st.session_state.auth_page == "login": render_login()
    else: render_signup()
else:
    pages = allowed_pages(st.session_state.user)
    if st.session_state.nav_page not in pages:
        st.session_state.nav_page = pages[0]
    page = render_sidebar(pages)
    if   page == "🏠 Home":           page_home()
    elif page == "🔔 Alerts":         page_alerts()
    elif page == "💉 BP Measurement": page_bp()
    elif page == "📥 Data Download":  page_download()
    elif page == "👥 Admin Panel":    page_admin()
    elif page == "⚙️ My Profile":    page_profile()
