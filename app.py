"""
VitaTrack Streamlit Frontend
Role-based page access:
  developer   -> All pages + Admin Panel
  admin       -> Admin Panel only
  doctor      -> Home, Alerts, Data Download
  nurse/paramedic/lab technician/other -> Home, Alerts, BP Measurement, Data Download
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import io, time, base64, json
import requests
from streamlit_cookies_controller import CookieController

st.set_page_config(page_title="VitaTrack", page_icon="🩺",
                   layout="wide", initial_sidebar_state="expanded")

# ─── Cookie-based session persistence ────────────────────────────────────────────
# CookieController must be instantiated ONCE at the very top, before any st.* calls
_cookies = CookieController()

COOKIE_NAME = "vitatrack_session"

def save_session_cookie(user: dict):
    """Persist the user dict in a browser cookie (7-day expiry)."""
    payload = json.dumps(user)
    _cookies.set(COOKIE_NAME, payload)

def clear_session_cookie():
    """Delete the session cookie on sign-out."""
    _cookies.remove(COOKIE_NAME)

def restore_session_from_cookie():
    """
    Called once per page load (including refresh).
    If a valid cookie exists and the session is not already active,
    re-authenticate silently via the Flask /auth/verify endpoint.
    Returns the restored user dict or None.
    """
    if st.session_state.get("logged_in"):
        return None                          # already logged in, nothing to do
    raw = _cookies.get(COOKIE_NAME)
    if not raw:
        return None
    try:
        user = json.loads(raw)
        # Quick server-side verification so a stale/tampered cookie doesn't work
        r = requests.post(
            f"{FLASK_API_URL}/auth/verify",
            json={"user_id": user.get("id")},
            timeout=6
        )
        if r and r.status_code == 200:
            return r.json().get("user")
    except Exception:
        pass
    # Cookie invalid/expired — remove it
    clear_session_cookie()
    return None

FLASK_API_URL    = "https://flask-vitals.onrender.com"
REFRESH_INTERVAL = 10
POSTS = ["Doctor","Nurse","Paramedic","Lab Technician","Physiotherapist","Other"]

ROLE_PAGES = {
    "developer":       ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download","👥 Admin Panel"],
    "admin":           ["👥 Admin Panel"],
    "doctor":          ["🏠 Home","🔔 Alerts","📥 Data Download"],
    "nurse":           ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download"],
    "paramedic":       ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download"],
    "lab technician":  ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download"],
    "physiotherapist": ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download"],
    "other":           ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download"],
    "staff":           ["🏠 Home","🔔 Alerts","💉 BP Measurement","📥 Data Download"],
}

def allowed_pages(user):
    role = (user.get("role") or "staff").lower()
    post = (user.get("post") or "").lower()
    return ROLE_PAGES.get(role, ROLE_PAGES.get(post, ROLE_PAGES["staff"]))

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
section[data-testid="stSidebar"]{background:#0f172a;}
section[data-testid="stSidebar"] *{color:#f8fafc !important;}
section[data-testid="stSidebar"] hr{border-color:#1e293b !important;}
.profile-chip{display:flex;align-items:center;gap:10px;background:#1e293b;
    border-radius:10px;padding:10px 14px;margin-bottom:12px;}
.profile-chip img{width:42px;height:42px;border-radius:50%;object-fit:cover;border:2px solid #3b82f6;}
.pc-name{font-size:14px;font-weight:600;}
.pc-post{font-size:12px;color:#94a3b8 !important;}
.metric-card{background:#fff;border-radius:12px;padding:20px 24px;
    box-shadow:0 2px 8px rgba(0,0,0,0.07);margin-bottom:16px;border-left:5px solid #3b82f6;}
.metric-card.alert-card{border-left-color:#ef4444;background:#fff5f5;}
.metric-card .label{font-size:12px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:.5px;}
.metric-card .value{font-size:34px;font-weight:800;color:#0f172a;line-height:1.1;}
.metric-card .status{font-size:13px;font-weight:600;margin-top:4px;}
.status-normal{color:#16a34a;}.status-warning{color:#ef4444;}
@keyframes flash{0%{background:#fff5f5}50%{background:#fca5a5}100%{background:#fff5f5}}
.flash{animation:flash 1s ease-in-out 3;}
.header-bar{display:flex;align-items:center;gap:14px;margin-bottom:24px;
    padding-bottom:16px;border-bottom:1px solid #e2e8f0;}
.header-logo{font-size:32px;}.header-title{font-size:26px;font-weight:800;color:#0f172a;}
.header-sub{font-size:14px;color:#64748b;}
.chart-box{background:#fff;border-radius:12px;padding:16px;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:16px;}
.alert-item{display:flex;align-items:flex-start;gap:14px;background:#fff5f5;
    border:1px solid #fecaca;border-radius:10px;padding:14px 18px;margin-bottom:10px;}
.alert-title{font-weight:600;color:#b91c1c;font-size:15px;}
.alert-time{font-size:12px;color:#94a3b8;margin-top:2px;}
.badge{display:inline-block;background:#ef4444;color:#fff;border-radius:999px;
    font-size:11px;font-weight:700;padding:2px 8px;margin-left:6px;vertical-align:middle;}
.patient-card{background:#fff;border-radius:12px;padding:18px 22px;
    box-shadow:0 2px 8px rgba(0,0,0,0.07);margin-bottom:14px;border-left:5px solid #8b5cf6;}
.patient-name{font-size:18px;font-weight:700;color:#0f172a;}
.patient-meta{font-size:13px;color:#64748b;margin-top:2px;}
.pill{display:inline-block;border-radius:999px;font-size:12px;font-weight:600;padding:3px 10px;}
.pill-green{background:#dcfce7;color:#16a34a;}.pill-yellow{background:#fef9c3;color:#ca8a04;}
.last-updated{font-size:12px;color:#94a3b8;text-align:right;margin-bottom:8px;}
.photo-preview{border-radius:12px;object-fit:cover;width:110px;height:110px;
    border:3px solid #3b82f6;display:block;margin:8px auto;}
.admin-table{width:100%;border-collapse:collapse;font-size:14px;}
.admin-table th{background:#f1f5f9;padding:10px 14px;text-align:left;font-weight:600;color:#475569;}
.admin-table td{padding:10px 14px;border-bottom:1px solid #f1f5f9;}
.role-badge{display:inline-block;background:#e0f2fe;color:#0369a1;border-radius:6px;
    font-size:11px;font-weight:700;padding:2px 8px;margin-left:6px;}
</style>
""", unsafe_allow_html=True)

BEEP_JS = """<script>
(function(){var c=new(window.AudioContext||window.webkitAudioContext)();
function b(f,d){var o=c.createOscillator(),g=c.createGain();
o.connect(g);g.connect(c.destination);o.frequency.value=f;g.gain.value=0.3;
o.start();o.stop(c.currentTime+d);}
b(880,0.18);setTimeout(function(){b(660,0.18);},220);setTimeout(function(){b(880,0.35);},440);
})();</script>"""

def play_beep():
    st.components.v1.html(BEEP_JS, height=0)

for k,v in {"logged_in":False,"user":None,"auth_page":"login",
             "last_alert_count":0,"flash_active":False,"nav_page":None,
             "_session_restored":False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Restore session from cookie on every page load (survives browser refresh) ────
if not st.session_state._session_restored:
    st.session_state._session_restored = True
    restored = restore_session_from_cookie()
    if restored:
        st.session_state.logged_in = True
        st.session_state.user      = restored
        st.session_state.nav_page  = allowed_pages(restored)[0]
        st.rerun()

def api(method, path, **kw):
    try:
        return requests.request(method, f"{FLASK_API_URL}{path}", timeout=10, **kw)
    except Exception:
        return None

def load_vitals(device_id=None):
    url = f"{FLASK_API_URL}/vitals" + (f"?device_id={device_id}" if device_id else "")
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text))
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            for c in ["Temperature","Blood Oxygen","Heart Rate","Respiration Rate"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["Timestamp","Temperature","Blood Oxygen",
                                   "Heart Rate","Respiration Rate","Blood Pressure","Device ID"])

def fetch_alerts():
    r = api("GET", "/alerts")
    return r.json() if r and r.status_code == 200 else []

def active_alerts():
    return [a for a in fetch_alerts() if not a.get("dismissed")]

def save_alert_remote(msg):
    api("POST", "/alerts", json={"message": msg})

def dismiss_alert_remote(aid):
    api("POST", f"/alerts/{aid}/dismiss")

def clear_alerts_remote():
    api("POST", "/alerts/clear")

CHART_CFG = {
    "Temperature":      ("#ef4444","#fff5f5"),
    "Blood Oxygen":     ("#3b82f6","#eff6ff"),
    "Heart Rate":       ("#10b981","#f0fdf4"),
    "Respiration Rate": ("#f59e0b","#fffbeb"),
}

def make_chart(df, col):
    color, bg = CHART_CFG[col]
    fig, ax = plt.subplots(figsize=(5.5, 2.8))
    fig.patch.set_facecolor(bg); ax.set_facecolor(bg)
    ax.plot(df["Timestamp"], df[col], color=color, lw=2.2,
            marker="o", markersize=4, markerfacecolor=color)
    ax.fill_between(df["Timestamp"], df[col], alpha=0.15, color=color)
    ax.set_xlabel("Time", fontsize=9, color="#64748b")
    ax.set_ylabel(col,    fontsize=9, color="#64748b")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.tick_params(colors="#64748b", labelsize=8)
    for s in ax.spines.values(): s.set_edgecolor("#e2e8f0")
    ax.grid(True, linestyle="--", alpha=0.4, color="#e2e8f0")
    fig.tight_layout(); return fig

def get_photo_html(uid, size=54, border="#3b82f6", name=""):
    try:
        r = requests.get(f"{FLASK_API_URL}/auth/photo/{uid}", timeout=5)
        if r.status_code == 200:
            b64 = base64.b64encode(r.content).decode()
            return (f'<img src="data:image/jpeg;base64,{b64}" '
                    f'style="width:{size}px;height:{size}px;border-radius:50%;'
                    f'object-fit:cover;border:2px solid {border}"/>')
    except Exception:
        pass
    ini = "".join(n[0] for n in (name or "?").split()[:2]).upper()
    return (f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{border};'
            f'display:inline-flex;align-items:center;justify-content:center;'
            f'font-size:{size//3}px;font-weight:700;color:#fff">{ini}</div>')

def render_login():
    _,col,_ = st.columns([1,2,1])
    with col:
        st.markdown("""<div style='text-align:center;padding:40px 0 20px'>
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
                    r = api("POST", "/auth/login", json={"email":email,"password":password})
                    if r is None:
                        st.error("Could not reach server.")
                    elif r.status_code == 200:
                        try:
                            user = r.json()["user"]
                            st.session_state.logged_in = True
                            st.session_state.user      = user
                            st.session_state.nav_page  = allowed_pages(user)[0]
                            save_session_cookie(user)
                            st.rerun()
                        except Exception:
                            st.error(f"Unexpected server response: {r.text[:200]}")
                    else:
                        try:
                            st.error(r.json().get("error", "Login failed."))
                        except Exception:
                            st.error(f"Server error ({r.status_code}): {r.text[:200]}")
            st.markdown("<hr style='margin:14px 0'>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;font-size:14px;color:#64748b'>New staff member?</div>",
                        unsafe_allow_html=True)
            if st.button("Create Account", use_container_width=True):
                st.session_state.auth_page = "signup"; st.rerun()
            st.markdown("""<div style='text-align:center;font-size:12px;color:#94a3b8;margin-top:8px'>
            Developer login: dev@vitatrack.com / dev123</div>""", unsafe_allow_html=True)

def render_signup():
    _,col,_ = st.columns([1,2,1])
    with col:
        st.markdown("""<div style='text-align:center;padding:28px 0 14px'>
            <div style='font-size:44px'>🩺</div>
            <div style='font-size:26px;font-weight:800;color:#0f172a'>Create Account</div>
            <div style='font-size:14px;color:#64748b;margin-top:4px'>Medical Personnel Registration</div>
        </div>""", unsafe_allow_html=True)
        with st.container(border=True):
            c1,c2     = st.columns(2)
            full_name = c1.text_input("Full Name *", placeholder="Dr. Jane Smith")
            post      = c2.selectbox("Role / Post *", POSTS)
            email     = st.text_input("Email Address *", placeholder="you@hospital.com")
            c3,c4     = st.columns(2)
            pw        = c3.text_input("Password *", type="password")
            pw2       = c4.text_input("Confirm Password *", type="password")
            st.markdown("**Passport Photo** *(required for staff ID)*")
            pf = st.file_uploader("Upload passport-style photo",
                                   type=["jpg","jpeg","png"], label_visibility="collapsed")
            if pf:
                raw = pf.read()
                st.markdown(f"""<div style='text-align:center;margin:8px 0'>
                    <img src="data:image/jpeg;base64,{base64.b64encode(raw).decode()}"
                         class="photo-preview"/>
                    <div style='font-size:12px;color:#16a34a;margin-top:4px'>Photo ready</div>
                </div>""", unsafe_allow_html=True)
                pf.seek(0)
            else:
                st.markdown("""<div style='text-align:center;padding:20px;background:#f8fafc;
                     border-radius:10px;color:#94a3b8;font-size:13px;margin:8px 0'>
                     No photo uploaded yet</div>""", unsafe_allow_html=True)
            if st.button("Register →", use_container_width=True, type="primary"):
                if not all([full_name, email, pw, pw2]):
                    st.error("Fill in all required fields.")
                elif pw != pw2:
                    st.error("Passwords do not match.")
                elif not pf:
                    st.error("Please upload a passport photo.")
                else:
                    r = api("POST", "/auth/signup", json={
                        "full_name":full_name,"email":email,"password":pw,
                        "post":post,"photo_b64":base64.b64encode(pf.read()).decode()
                    })
                    if r is None:
                        st.error("Could not reach server.")
                    elif r.status_code == 201:
                        st.success("Account created! Awaiting admin approval.")
                        time.sleep(2)
                        st.session_state.auth_page = "login"; st.rerun()
                    else:
                        try:
                            st.error(r.json().get("error", "Signup failed."))
                        except Exception:
                            st.error(f"Server error ({r.status_code}): {r.text[:200]}")
            st.markdown("<hr style='margin:14px 0'>", unsafe_allow_html=True)
            if st.button("Back to Sign In", use_container_width=True):
                st.session_state.auth_page = "login"; st.rerun()

def render_sidebar(pages, active_count):
    user = st.session_state.user
    role = (user.get("role") or "staff").capitalize()
    with st.sidebar:
        ph = get_photo_html(user["id"], 42, "#3b82f6", user["full_name"])
        st.markdown(f"""<div class="profile-chip">{ph}
            <div><div class="pc-name">{user['full_name']}</div>
            <div class="pc-post">{user['post']} <span class="role-badge">{role}</span></div>
            </div></div>""", unsafe_allow_html=True)
        st.markdown("---")
        badge = f'<span class="badge">{active_count}</span>' if active_count > 0 else ""
        st.markdown(f"**Navigation** {badge}", unsafe_allow_html=True)
        cur = st.session_state.nav_page
        idx = pages.index(cur) if cur in pages else 0
        page = st.radio("", pages, index=idx, label_visibility="collapsed")
        st.session_state.nav_page = page
        st.markdown("---")
        st.markdown(f"<span style='font-size:12px;color:#94a3b8'>🔴 {active_count} active alert(s)</span>",
                    unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:12px;color:#94a3b8'>Refresh: {REFRESH_INTERVAL}s</span>",
                    unsafe_allow_html=True)
        st.markdown("")
        if st.button("Sign Out", use_container_width=True):
            clear_session_cookie()
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
    return page

def page_home():
    st.markdown("""<div class="header-bar"><div class="header-logo">🩺</div>
        <div><div class="header-title">VitaTrack</div>
        <div class="header-sub">Real-time Patient Vital Signs Monitoring</div></div>
    </div>""", unsafe_allow_html=True)
    rp = api("GET", "/admin/patients")
    patient_list = rp.json() if rp and rp.status_code == 200 else []
    device_id = None
    if patient_list:
        names    = {p["name"]: p for p in patient_list}
        selected = st.selectbox("Viewing patient:", list(names.keys())) if len(names)>1 else list(names.keys())[0]
        pat      = names[selected]
        device_id = pat.get("device_id")
        dev_tag   = (f'<span class="pill pill-green">📡 {pat["device_id"]}</span>'
                     if pat.get("device_id") else '<span class="pill pill-yellow">No device assigned</span>')
        st.markdown(f"""<div class="patient-card">
            <div class="patient-name">🧑‍⚕️ {pat['name']}</div>
            <div class="patient-meta">Age: {pat.get('age','—')} · Gender: {pat.get('gender','—')}
                · Diagnosis: {pat.get('diagnosis','—')} &nbsp;{dev_tag}</div>
        </div>""", unsafe_allow_html=True)
    df = load_vitals(device_id)
    if df.empty:
        st.warning("No vitals data yet. Waiting for sensor data…")
    else:
        display_df = df.tail(10)
        latest     = display_df.iloc[-1]
        st.markdown(f'<div class="last-updated">Last updated: {datetime.now().strftime("%d %b %Y, %H:%M:%S")}</div>',
                    unsafe_allow_html=True)
        vitals_cfg = [
            ("Temperature","°C",36.0,38.0,"🌡️"),
            ("Blood Oxygen","%",90.0,100.0,"🫁"),
            ("Heart Rate","bpm",60.0,100.0,"❤️"),
            ("Respiration Rate","breaths/min",12.0,20.0,"🌬️"),
        ]
        cols = st.columns(4)
        new_alert = False
        for i,(col_name,unit,lo,hi,icon) in enumerate(vitals_cfg):
            val = latest.get(col_name)
            is_alert = pd.notna(val) and (val < lo or val > hi)
            if is_alert:
                save_alert_remote(f"{col_name} out of range ({val:.1f} {unit})")
                new_alert = True
            card_cls = "metric-card alert-card flash" if is_alert and st.session_state.flash_active else "metric-card"
            status   = f"⚠️ Out of range [{lo}–{hi}]" if is_alert else f"✓ Normal [{lo}–{hi}]"
            scls     = "status-warning" if is_alert else "status-normal"
            with cols[i]:
                st.markdown(f"""<div class="{card_cls}">
                    <div class="label">{icon} {col_name}</div>
                    <div class="value">{f"{val:.1f}" if pd.notna(val) else "—"}
                        <span style="font-size:18px;color:#64748b">{unit}</span></div>
                    <div class="status {scls}">{status}</div>
                </div>""", unsafe_allow_html=True)
        if new_alert: play_beep()
        st.session_state.flash_active = False
        st.markdown('<div style="font-size:20px;font-weight:700;color:#0f172a;margin-top:8px">Trend Charts</div>',
                    unsafe_allow_html=True)
        st.markdown('<div style="font-size:14px;color:#64748b;margin-bottom:16px">Last 10 readings</div>',
                    unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        for col_name,cw in [("Temperature",c1),("Blood Oxygen",c2),("Heart Rate",c1),("Respiration Rate",c2)]:
            with cw:
                st.markdown('<div class="chart-box">', unsafe_allow_html=True)
                st.pyplot(make_chart(display_df, col_name))
                st.markdown('</div>', unsafe_allow_html=True)
        if "Blood Pressure" in df.columns and df["Blood Pressure"].notna().any():
            last_bp = df["Blood Pressure"].dropna().iloc[-1]
            st.markdown(f"""<div class="metric-card" style="border-left-color:#8b5cf6;max-width:340px">
                <div class="label">💓 Last Blood Pressure</div>
                <div class="value">{last_bp} <span style="font-size:18px;color:#64748b">mmHg</span></div>
            </div>""", unsafe_allow_html=True)
    with st.spinner(f"Refreshing in {REFRESH_INTERVAL}s…"):
        time.sleep(REFRESH_INTERVAL)
    st.rerun()

def page_alerts():
    st.markdown("""<div class="header-bar"><div class="header-logo">🔔</div>
        <div><div class="header-title">Alerts & Notifications</div>
        <div class="header-sub">Triggered vital sign alerts</div></div>
    </div>""", unsafe_allow_html=True)
    alerts = fetch_alerts()
    active = [a for a in alerts if not a.get("dismissed")]
    dismissed = len(alerts) - len(active)
    c1,c2 = st.columns([3,1])
    c1.markdown(f"**{len(active)} active** · {dismissed} dismissed")
    with c2:
        if st.button("Clear All", use_container_width=True):
            clear_alerts_remote(); st.rerun()
    st.markdown("---")
    if not active:
        st.markdown("""<div style="text-align:center;padding:50px;color:#64748b">
            <div style="font-size:48px">✅</div>
            <div style="font-size:18px;font-weight:600;margin-top:12px">No active alerts</div>
        </div>""", unsafe_allow_html=True); return
    icons = {"Temperature":"🌡️","Blood Oxygen":"🫁","Heart Rate":"❤️","Respiration Rate":"🌬️","BP":"💓"}
    for a in active:
        icon = next((v for k,v in icons.items() if k in a["message"]), "⚠️")
        try:
            ts = datetime.fromisoformat(a["timestamp"]).strftime("%d %b %Y, %H:%M:%S")
        except Exception:
            ts = a["timestamp"]
        cm,cb = st.columns([5,1])
        with cm:
            st.markdown(f"""<div class="alert-item">
                <div style="font-size:22px">{icon}</div>
                <div><div class="alert-title">{a['message']}</div>
                <div class="alert-time">{ts}</div></div>
            </div>""", unsafe_allow_html=True)
        with cb:
            if st.button("Dismiss", key=f"d_{a['id']}"):
                dismiss_alert_remote(a["id"]); st.rerun()

def page_bp():
    st.markdown("""<div class="header-bar"><div class="header-logo">💉</div>
        <div><div class="header-title">Blood Pressure Measurement</div>
        <div class="header-sub">Manually log a BP reading</div></div>
    </div>""", unsafe_allow_html=True)
    def classify(s,d):
        if s<120 and d<80:   return "Normal","#16a34a"
        elif s<130 and d<80: return "Elevated","#ca8a04"
        elif s<140 or d<90:  return "High Stage 1","#ea580c"
        else:                 return "High Stage 2","#dc2626"
    cf,ci = st.columns(2)
    with cf:
        st.markdown("#### Enter Reading")
        systolic  = st.number_input("Systolic (mmHg)",  50, 200, 120)
        diastolic = st.number_input("Diastolic (mmHg)", 30, 150, 80)
        cat,color = classify(systolic,diastolic)
        st.markdown(f"""<div style="background:#f8fafc;border-radius:8px;padding:10px 16px;
             margin:8px 0;border-left:4px solid {color};font-size:14px">
            <strong>Classification:</strong> <span style="color:{color};font-weight:700"> {cat}</span>
        </div>""", unsafe_allow_html=True)
        if st.button("Save BP", use_container_width=True, type="primary"):
            r = api("POST","/data",json={"temperature":None,"blood_oxygen":None,
                "heart_rate":None,"respiration_rate":None,"blood_pressure":f"{systolic}/{diastolic}"})
            if r and r.status_code==200:
                st.success(f"BP {systolic}/{diastolic} mmHg saved!")
                if systolic>=140 or diastolic>=90:
                    save_alert_remote(f"High BP: {systolic}/{diastolic} mmHg"); play_beep()
                    st.error("High BP alert saved.")
            else:
                st.error("Failed to save.")
    with ci:
        st.markdown("#### BP Reference Guide")
        st.markdown("""<table class="admin-table">
        <tr><th>Category</th><th>Systolic</th><th>Diastolic</th></tr>
        <tr><td style="color:#16a34a;font-weight:600">Normal</td><td>&lt;120</td><td>&lt;80</td></tr>
        <tr><td style="color:#ca8a04;font-weight:600">Elevated</td><td>120-129</td><td>&lt;80</td></tr>
        <tr><td style="color:#ea580c;font-weight:600">High Stage 1</td><td>130-139</td><td>80-89</td></tr>
        <tr><td style="color:#dc2626;font-weight:600">High Stage 2</td><td>>=140</td><td>>=90</td></tr>
        </table>""", unsafe_allow_html=True)
        df = load_vitals()
        if not df.empty and "Blood Pressure" in df.columns and df["Blood Pressure"].notna().any():
            last_bp = df["Blood Pressure"].dropna().iloc[-1]
            st.markdown(f"""<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
                 padding:16px 20px;font-size:16px;font-weight:600;color:#166534;margin-top:20px">
                Last recorded: <span style="font-size:20px">{last_bp}</span> mmHg
            </div>""", unsafe_allow_html=True)

def page_download():
    st.markdown("""<div class="header-bar"><div class="header-logo">📥</div>
        <div><div class="header-title">Download Patient Data</div>
        <div class="header-sub">Export vitals and alerts as CSV</div></div>
    </div>""", unsafe_allow_html=True)
    df = load_vitals()
    if df.empty:
        st.warning("No data available yet."); return
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("Total Readings", len(df))
    s2.metric("From", df["Timestamp"].min().strftime("%d %b %Y"))
    s3.metric("To",   df["Timestamp"].max().strftime("%d %b %Y"))
    s4.metric("Columns", len(df.columns))
    st.markdown("---")
    st.markdown("#### Preview (last 10 rows)")
    st.dataframe(df.tail(10), use_container_width=True, hide_index=True)
    st.markdown("---")
    c1,c2 = st.columns(2)
    c1.download_button("Download Vitals CSV", df.to_csv(index=False).encode(),
                        f"vitatrack_vitals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv", use_container_width=True)
    alerts = fetch_alerts()
    if alerts:
        al_df = pd.DataFrame(alerts)
        c2.download_button("Download Alerts Log", al_df.to_csv(index=False).encode(),
                            f"vitatrack_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv", use_container_width=True)

def page_admin():
    st.markdown("""<div class="header-bar"><div class="header-logo">👥</div>
        <div><div class="header-title">Admin Panel</div>
        <div class="header-sub">Manage staff, patients & devices</div></div>
    </div>""", unsafe_allow_html=True)
    tab1,tab2,tab3 = st.tabs(["👤 Staff Management","🧑‍⚕️ Patients","📡 Devices"])

    with tab1:
        r = api("GET","/admin/users")
        if not r or r.status_code!=200:
            st.error("Could not load users."); return
        users    = r.json()
        pending  = [u for u in users if not u.get("approved")]
        approved = [u for u in users if u.get("approved")]
        if pending:
            st.markdown(f"#### Pending Approval ({len(pending)})")
            for u in pending:
                with st.container(border=True):
                    ci,cn,ca = st.columns([1,4,2])
                    with ci:
                        st.markdown(get_photo_html(u["id"],60,"#f59e0b",u["full_name"]),
                                    unsafe_allow_html=True)
                    with cn:
                        st.markdown(f"**{u['full_name']}** · {u['post']}")
                        st.caption(u["email"])
                        st.caption(f"Registered: {u.get('created_at','')[:10]}")
                    with ca:
                        if st.button("Approve", key=f"app_{u['id']}", use_container_width=True):
                            api("POST",f"/admin/approve/{u['id']}"); st.rerun()
                        if st.button("Reject",  key=f"rej_{u['id']}", use_container_width=True):
                            api("DELETE",f"/admin/reject/{u['id']}"); st.rerun()
        st.markdown(f"#### Approved Staff ({len(approved)})")
        if not approved:
            st.info("No approved staff yet.")
        for u in approved:
            with st.container(border=True):
                ci2,cn2 = st.columns([1,5])
                with ci2:
                    st.markdown(get_photo_html(u["id"],54,"#10b981",u["full_name"]),
                                unsafe_allow_html=True)
                with cn2:
                    role_label = (u.get("role") or "staff").capitalize()
                    st.markdown(f"**{u['full_name']}** &nbsp;"
                                f'<span class="pill pill-green">{u["post"]}</span>'
                                f'<span class="role-badge">{role_label}</span>',
                                unsafe_allow_html=True)
                    st.caption(u["email"])

    with tab2:
        rp = api("GET","/admin/patients")
        patients  = rp.json() if rp and rp.status_code==200 else []
        ru = api("GET","/admin/users")
        all_staff = [u for u in (ru.json() if ru and ru.status_code==200 else []) if u.get("approved")]
        st.markdown("#### Add New Patient")
        with st.expander("Create patient profile", expanded=not bool(patients)):
            pc1,pc2 = st.columns(2)
            p_name  = pc1.text_input("Patient Name *")
            p_age   = pc2.number_input("Age *", 0, 120, 30)
            pc3,pc4 = st.columns(2)
            p_gender= pc3.selectbox("Gender *", ["Male","Female","Other"])
            p_diag  = pc4.text_input("Diagnosis *")
            p_notes = st.text_area("Notes", height=70)
            if st.button("Create Patient", type="primary"):
                if not p_name or not p_diag:
                    st.error("Name and diagnosis are required.")
                else:
                    r2 = api("POST","/admin/patients",json={"name":p_name,"age":p_age,
                             "gender":p_gender,"diagnosis":p_diag,"notes":p_notes})
                    if r2 and r2.status_code==201:
                        st.success(f"Patient '{p_name}' created!"); st.rerun()
                    else:
                        st.error("Failed.")
        st.markdown(f"#### Patient List ({len(patients)})")
        if not patients:
            st.info("No patients yet.")
        staff_map = {u["id"]: u["full_name"] for u in all_staff}
        staff_opt = {u["full_name"]: u["id"] for u in all_staff}
        for pat in patients:
            with st.container(border=True):
                ph1,ph2 = st.columns([3,2])
                with ph1:
                    dev_tag = (f'<span class="pill pill-green">📡 {pat["device_id"]}</span>'
                               if pat.get("device_id") else '<span class="pill pill-yellow">No device</span>')
                    assigned_names = [staff_map[i] for i in pat.get("assigned_to",[]) if i in staff_map]
                    st.markdown(f"""<div class="patient-name">{pat['name']}</div>
                    <div class="patient-meta">{pat.get('age','—')} yrs · {pat.get('gender','—')}
                        · {pat.get('diagnosis','—')} &nbsp;{dev_tag}</div>""", unsafe_allow_html=True)
                    if pat.get("notes"): st.caption(f"📝 {pat['notes']}")
                    if assigned_names:   st.caption(f"👩‍⚕️ Assigned: {', '.join(assigned_names)}")
                with ph2:
                    defaults = [n for n,uid in staff_opt.items() if uid in pat.get("assigned_to",[])]
                    sel = st.multiselect("Assign staff", list(staff_opt.keys()),
                                         default=defaults, key=f"ms_{pat['id']}")
                    if st.button("Save", key=f"sv_{pat['id']}", use_container_width=True):
                        api("POST","/admin/assign_staff",
                            json={"patient_id":pat["id"],"staff_ids":[staff_opt[n] for n in sel]})
                        st.success("Saved!"); st.rerun()

    with tab3:
        rd  = api("GET","/admin/devices")
        devices   = rd.json() if rd and rd.status_code==200 else []
        rp2 = api("GET","/admin/patients")
        patients2 = rp2.json() if rp2 and rp2.status_code==200 else []
        st.markdown("#### Register New Device")
        with st.expander("Add a device", expanded=not bool(devices)):
            dc1,dc2   = st.columns(2)
            dev_id_in = dc1.text_input("Device ID *", placeholder="e.g. ESP32-001")
            dev_lbl   = dc2.text_input("Label", placeholder="e.g. Ward 3 Sensor")
            if st.button("Register Device", type="primary"):
                if not dev_id_in:
                    st.error("Device ID required.")
                else:
                    r3 = api("POST","/admin/devices",json={"device_id":dev_id_in,"label":dev_lbl})
                    if r3 and r3.status_code==201:
                        st.success(f"Device '{dev_id_in}' registered!"); st.rerun()
                    else:
                        err = r3.json().get("error","Failed.") if r3 else "No response."
                        st.error(err)
        st.markdown(f"#### Registered Devices ({len(devices)})")
        if not devices:
            st.info("No devices yet.")
        p_id2name = {p["id"]: p["name"] for p in patients2}
        p_name2id = {p["name"]: p["id"] for p in patients2}
        p_name2id["— Unassigned —"] = None
        for dev in devices:
            with st.container(border=True):
                dh1,dh2 = st.columns([3,2])
                with dh1:
                    assigned_p = p_id2name.get(dev.get("patient_id"), "Unassigned")
                    pill_cls   = "pill-green" if dev.get("patient_id") else "pill-yellow"
                    st.markdown(f"""<div style="font-size:16px;font-weight:700">📡 {dev['device_id']}</div>
                    <div style="font-size:13px;color:#64748b;margin-top:2px">
                        {dev.get('label','') or 'No label'} &nbsp;
                        <span class="pill {pill_cls}">{assigned_p}</span></div>""",
                                unsafe_allow_html=True)
                    st.caption(f"Registered: {dev.get('created_at','')[:10]}")
                with dh2:
                    opts  = list(p_name2id.keys())
                    cur_p = p_id2name.get(dev.get("patient_id"), "— Unassigned —")
                    cur_i = opts.index(cur_p) if cur_p in opts else 0
                    sel_p = st.selectbox("Assign to patient", opts, index=cur_i,
                                         key=f"dp_{dev['device_id']}")
                    if st.button("Assign", key=f"da_{dev['device_id']}", use_container_width=True):
                        pid = p_name2id[sel_p]
                        if pid:
                            r4 = api("POST","/admin/devices/assign",
                                     json={"device_id":dev["device_id"],"patient_id":pid})
                            if r4 and r4.status_code==200:
                                st.success("Assigned!"); st.rerun()
                            else:
                                st.error("Failed.")
                        else:
                            st.info("Select a patient first.")

# ── Router ───────────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    if st.session_state.auth_page == "login": render_login()
    else: render_signup()
else:
    user  = st.session_state.user
    pages = allowed_pages(user)
    if st.session_state.nav_page not in pages:
        st.session_state.nav_page = pages[0]
    active_count = len(active_alerts())
    if active_count > st.session_state.last_alert_count:
        play_beep(); st.session_state.flash_active = True
    st.session_state.last_alert_count = active_count
    page = render_sidebar(pages, active_count)
    if   page == "🏠 Home":           page_home()
    elif page == "🔔 Alerts":         page_alerts()
    elif page == "💉 BP Measurement": page_bp()
    elif page == "📥 Data Download":  page_download()
    elif page == "👥 Admin Panel":    page_admin()
