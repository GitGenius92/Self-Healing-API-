# ============================================================
#  API SECURITY HEALER — STREAMLIT FRONTEND v3
#  pip install streamlit requests pyyaml plotly
#  streamlit run app.py
# ============================================================

import streamlit as st
import requests, json, time
import plotly.graph_objects as go

BACKEND = "http://localhost:8000"

st.set_page_config(
    page_title="API Healer — Security Scanner",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ════════════════════════════════════════════════════════════
#  MEGA CSS
# ════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }
#MainMenu, header, footer { visibility: hidden; }

html, body, [class*="css"], .stApp {
  font-family: 'Space Grotesk', sans-serif !important;
  background: #060612 !important;
  color: #ddd8f5 !important;
}

.block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

/* ══ ANIMATED BACKGROUND ══ */
.bg-grid {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-image:
    linear-gradient(rgba(100,80,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(100,80,255,0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none; z-index: 0;
}
.bg-orb1 {
  position: fixed; width: 600px; height: 600px; border-radius: 50%;
  background: radial-gradient(circle, rgba(100,60,255,0.08) 0%, transparent 65%);
  top: -200px; right: -100px; pointer-events: none; z-index: 0;
  animation: orbFloat 8s ease-in-out infinite;
}
.bg-orb2 {
  position: fixed; width: 400px; height: 400px; border-radius: 50%;
  background: radial-gradient(circle, rgba(0,200,150,0.06) 0%, transparent 65%);
  bottom: -100px; left: -100px; pointer-events: none; z-index: 0;
  animation: orbFloat 10s ease-in-out infinite reverse;
}
@keyframes orbFloat {
  0%,100% { transform: translateY(0px) scale(1); }
  50% { transform: translateY(-30px) scale(1.05); }
}

/* ══ TOPBAR ══ */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem 2.5rem;
  border-bottom: 1px solid rgba(100,80,255,0.12);
  background: rgba(6,6,18,0.9);
  backdrop-filter: blur(12px);
  position: sticky; top: 0; z-index: 100;
}
.topbar-logo {
  display: flex; align-items: center; gap: 10px;
}
.logo-icon {
  width: 34px; height: 34px; border-radius: 9px;
  background: linear-gradient(135deg, #6440ff, #00c896);
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
}
.logo-text {
  font-size: 15px; font-weight: 700; letter-spacing: -0.3px;
  background: linear-gradient(90deg, #b8a8ff, #00c896);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.status-pill {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 14px; border-radius: 20px;
  font-size: 12px; font-weight: 500;
}
.status-online {
  background: rgba(0,200,150,0.1);
  border: 1px solid rgba(0,200,150,0.25);
  color: #00c896;
}
.status-offline {
  background: rgba(255,80,80,0.1);
  border: 1px solid rgba(255,80,80,0.25);
  color: #ff5050;
}
.status-dot {
  width: 7px; height: 7px; border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}
.dot-green { background: #00c896; }
.dot-red   { background: #ff5050; }
@keyframes pulse {
  0%,100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.85); }
}

/* ══ HERO ══ */
.hero-wrap {
  padding: 4rem 2.5rem 3rem;
  max-width: 1300px; margin: 0 auto;
}
.hero-eyebrow {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 5px 14px; border-radius: 20px;
  background: rgba(100,64,255,0.12);
  border: 1px solid rgba(100,64,255,0.25);
  font-size: 12px; font-weight: 600; color: #9080ee;
  letter-spacing: .06em; text-transform: uppercase;
  margin-bottom: 1.2rem;
}
.hero-title {
  font-size: clamp(2.4rem, 5vw, 3.8rem);
  font-weight: 700; line-height: 1.08;
  letter-spacing: -1.5px;
  margin: 0 0 1rem 0;
}
.hero-title span {
  background: linear-gradient(135deg, #a090ff 0%, #6440ff 40%, #00c896 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-desc {
  font-size: 1.1rem; color: rgba(210,205,240,0.55);
  max-width: 540px; line-height: 1.7; margin: 0 0 2.5rem 0;
}
.hero-stats {
  display: flex; gap: 2.5rem; margin-bottom: 3rem;
}
.hstat { }
.hstat-num {
  font-size: 1.8rem; font-weight: 700;
  background: linear-gradient(135deg, #a090ff, #6440ff);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  line-height: 1;
}
.hstat-label {
  font-size: 12px; color: rgba(200,195,230,0.4);
  margin-top: 2px; letter-spacing: .04em;
}

/* ══ INPUT CARD ══ */
.input-card {
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(100,80,255,0.14);
  border-radius: 20px;
  padding: 2rem 2.2rem;
  max-width: 1300px; margin: 0 auto 2rem auto;
}
.input-card-title {
  font-size: 13px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .1em;
  color: rgba(180,170,220,0.4);
  margin: 0 0 1.2rem 0;
}

/* ══ TABS ══ */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(100,80,255,0.12) !important;
  border-radius: 12px !important;
  padding: 3px !important; gap: 2px !important;
  margin-bottom: 1.5rem !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 9px !important;
  color: rgba(200,195,230,0.45) !important;
  font-family: 'Space Grotesk', sans-serif !important;
  font-weight: 500 !important; font-size: 13px !important;
  padding: 7px 20px !important;
}
.stTabs [aria-selected="true"] {
  background: rgba(100,64,255,0.2) !important;
  color: #b0a0ff !important;
}

/* ══ FILE UPLOADER ══ */
[data-testid="stFileUploader"] {
  background: rgba(100,64,255,0.04) !important;
  border: 1.5px dashed rgba(100,64,255,0.3) !important;
  border-radius: 14px !important;
  transition: all .2s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: rgba(100,64,255,0.6) !important;
  background: rgba(100,64,255,0.08) !important;
}

/* ══ TEXT AREA ══ */
.stTextArea textarea {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(100,80,255,0.18) !important;
  border-radius: 12px !important;
  color: #ddd8f5 !important;
  font-family: 'Fira Code', monospace !important;
  font-size: 13px !important;
}
.stTextArea textarea:focus {
  border-color: rgba(100,64,255,0.5) !important;
  box-shadow: 0 0 0 3px rgba(100,64,255,0.08) !important;
}

/* ══ SELECT + TEXT INPUT ══ */
.stSelectbox > div > div, .stTextInput > div > div > input {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(100,80,255,0.18) !important;
  border-radius: 10px !important;
  color: #ddd8f5 !important;
  font-family: 'Space Grotesk', sans-serif !important;
}

/* ══ BUTTONS ══ */
.stButton > button {
  background: linear-gradient(135deg, rgba(100,64,255,0.3), rgba(60,40,180,0.2)) !important;
  border: 1px solid rgba(100,64,255,0.4) !important;
  border-radius: 10px !important;
  color: #b0a0ff !important;
  font-family: 'Space Grotesk', sans-serif !important;
  font-weight: 600 !important; font-size: 13px !important;
  padding: 0.55rem 1.6rem !important;
  transition: all .2s !important;
  letter-spacing: .01em !important;
}
.stButton > button:hover {
  border-color: rgba(100,64,255,0.75) !important;
  background: rgba(100,64,255,0.35) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ══ PROGRESS BAR ══ */
.stProgress > div > div {
  background: linear-gradient(90deg, #6440ff, #00c896) !important;
  border-radius: 6px !important;
}
.stProgress > div {
  background: rgba(100,80,255,0.1) !important;
  border-radius: 6px !important;
}

/* ══ RESULTS WRAP ══ */
.results-wrap {
  max-width: 1300px; margin: 0 auto;
  padding: 0 2.5rem 3rem;
}

/* ══ SCORE HERO ══ */
.score-hero {
  display: flex; align-items: center; gap: 2rem;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(100,80,255,0.12);
  border-radius: 20px; padding: 1.8rem 2.2rem;
  margin-bottom: 1.2rem;
}
.score-circle {
  width: 90px; height: 90px; border-radius: 50%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  flex-shrink: 0;
  border: 3px solid;
}
.score-circle-num { font-size: 1.8rem; font-weight: 700; line-height: 1; }
.score-circle-label { font-size: 9px; color: rgba(200,195,230,0.5); letter-spacing:.06em; text-transform:uppercase; margin-top:2px; }
.score-grade { font-size: 2.8rem; font-weight: 700; }
.score-summary-text { color: rgba(200,195,230,0.55); font-size: 13px; line-height: 1.6; margin-top: 4px; }

/* ══ METRIC GRID ══ */
.metric-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 10px; margin-bottom: 1.5rem;
}
.mcard {
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(100,80,255,0.1);
  border-radius: 14px; padding: 1.1rem 1.3rem;
  position: relative; overflow: hidden;
}
.mcard::before {
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
}
.mcard-c::before { background: linear-gradient(90deg,#ff4545,#ff7070); }
.mcard-h::before { background: linear-gradient(90deg,#ff8c00,#ffb060); }
.mcard-m::before { background: linear-gradient(90deg,#3a8dff,#80b0ff); }
.mcard-s::before { background: linear-gradient(90deg,#00c896,#60dc90); }
.mcard-num {
  font-size: 2rem; font-weight: 700; line-height: 1; margin-bottom: 3px;
}
.mcard-label {
  font-size: 11px; font-weight: 500;
  text-transform: uppercase; letter-spacing: .08em;
  color: rgba(200,195,230,0.4);
}

/* ══ SECTION LABEL ══ */
.sec-label {
  font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .12em;
  color: rgba(170,160,210,0.4);
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(100,80,255,0.1);
  margin: 1.6rem 0 1rem 0;
}

/* ══ VULN CARD ══ */
.vcard {
  border-radius: 14px; padding: 1rem 1.25rem;
  margin-bottom: 8px;
  border: 1px solid rgba(100,80,255,0.1);
  background: rgba(255,255,255,0.02);
  border-left: 3px solid;
  transition: transform .15s;
}
.vcard:hover { transform: translateX(3px); }
.vcard-critical { border-left-color: #ff4545; background: rgba(255,69,69,0.04); }
.vcard-high     { border-left-color: #ff8c00; background: rgba(255,140,0,0.04); }
.vcard-medium   { border-left-color: #3a8dff; background: rgba(58,141,255,0.04); }
.vcard-safe     { border-left-color: #00c896; background: rgba(0,200,150,0.04); }
.vcard-top { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:6px; }
.vcard-title { font-size:13px; font-weight:600; color:#ddd8f5; margin:2px 0; }
.vcard-desc  { font-size:12px; color:rgba(200,195,230,0.55); line-height:1.5; }
.vcard-meta  { font-size:11px; color:rgba(170,160,210,0.35); margin-top:5px; }

/* ══ BADGES ══ */
.badge {
  display:inline-flex; align-items:center;
  font-size:10px; font-weight:700;
  padding:2px 9px; border-radius:20px;
  text-transform:uppercase; letter-spacing:.07em;
  font-family:'Space Grotesk',sans-serif;
}
.bc { background:rgba(255,69,69,0.15);   color:#ff6060; border:1px solid rgba(255,69,69,0.3);   }
.bh { background:rgba(255,140,0,0.12);   color:#ffaa40; border:1px solid rgba(255,140,0,0.3);   }
.bm { background:rgba(58,141,255,0.12);  color:#70a8ff; border:1px solid rgba(58,141,255,0.3);  }
.bs { background:rgba(0,200,150,0.1);    color:#00c896; border:1px solid rgba(0,200,150,0.25);  }
.bi { background:rgba(160,160,190,0.1);  color:#9090b0; border:1px solid rgba(160,160,190,0.2); }

/* ══ METHOD PILLS ══ */
.mp {
  font-family:'Fira Code',monospace; font-size:10px; font-weight:500;
  padding:2px 7px; border-radius:5px;
}
.mg { background:rgba(0,200,150,0.1);   color:#00c896; }
.mp2{ background:rgba(58,141,255,0.1);  color:#70a8ff; }
.mu { background:rgba(255,140,0,0.1);   color:#ffaa40; }
.md { background:rgba(255,69,69,0.1);   color:#ff6060; }
.mpa{ background:rgba(180,100,255,0.1); color:#c080ff; }

/* ══ PATH PILL ══ */
.ppill {
  font-family:'Fira Code',monospace; font-size:11px;
  padding:2px 8px; border-radius:6px;
  background:rgba(100,64,255,0.1); color:#9080ee;
  border:1px solid rgba(100,64,255,0.18);
}

/* ══ ENDPOINT ROW ══ */
.ep-row {
  display:flex; align-items:center; gap:10px;
  padding:8px 14px; border-radius:10px; margin-bottom:4px;
  border:1px solid rgba(100,80,255,0.07);
  background:rgba(255,255,255,0.015);
  transition:background .15s;
}
.ep-row:hover { background:rgba(100,64,255,0.06); }
.ep-path { font-family:'Fira Code',monospace; font-size:12px; flex:1; color:#c0b8e0; }
.ep-conf { font-size:11px; color:rgba(170,160,210,0.35); margin-left:auto; }

/* ══ HEAL SECTION ══ */
.heal-header {
  display:flex; align-items:center; gap:8px;
  margin-bottom:6px;
}
.heal-icon {
  width:28px; height:28px; border-radius:8px;
  background:rgba(0,200,150,0.12);
  display:flex; align-items:center; justify-content:center;
  font-size:13px; color:#00c896;
  border:1px solid rgba(0,200,150,0.2);
}
.heal-title { font-size:13px; font-weight:600; color:#00c896; }
.heal-sub   { font-size:12px; color:rgba(170,210,190,0.55); line-height:1.5; margin-bottom:10px; }

/* ══ CODE BLOCK ══ */
.stCodeBlock { border-radius:10px !important; }
pre { border-radius:10px !important; }

/* ══ EXPANDER ══ */
.streamlit-expanderHeader {
  background:rgba(255,255,255,0.025) !important;
  border:1px solid rgba(100,80,255,0.12) !important;
  border-radius:12px !important;
  font-family:'Space Grotesk',sans-serif !important;
  font-size:13px !important;
  color:#c0b8e0 !important;
}
.streamlit-expanderContent {
  background:rgba(255,255,255,0.015) !important;
  border:1px solid rgba(100,80,255,0.1) !important;
  border-radius:0 0 12px 12px !important;
}

/* ══ DOWNLOAD BUTTON ══ */
[data-testid="stDownloadButton"] button {
  background:rgba(0,200,150,0.08) !important;
  border:1px solid rgba(0,200,150,0.25) !important;
  color:#00c896 !important;
  border-radius:10px !important;
  font-family:'Space Grotesk',sans-serif !important;
  font-weight:600 !important;
}
[data-testid="stDownloadButton"] button:hover {
  background:rgba(0,200,150,0.15) !important;
  border-color:rgba(0,200,150,0.5) !important;
}

/* ══ DIVIDER ══ */
hr { border:none; border-top:1px solid rgba(100,80,255,0.1) !important; margin:2rem 0 !important; }

/* ══ SPINNER ══ */
.stSpinner > div { border-top-color: #6440ff !important; }

/* ══ SCAN ANIMATION ══ */
.scan-line {
  height:2px;
  background:linear-gradient(90deg,transparent,#6440ff,#00c896,transparent);
  border-radius:2px; margin:8px 0;
  animation:scanAnim 1.5s ease-in-out infinite;
}
@keyframes scanAnim {
  0%   { opacity:0; transform:scaleX(0.3); }
  50%  { opacity:1; transform:scaleX(1); }
  100% { opacity:0; transform:scaleX(0.3); }
}

/* ══ EMPTY STATE ══ */
.empty-state {
  text-align:center; padding:3rem 2rem;
  color:rgba(200,195,230,0.3); font-size:14px;
}
</style>

<div class="bg-grid"></div>
<div class="bg-orb1"></div>
<div class="bg-orb2"></div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════

def sev_badge(s):
    m = {"Critical":"bc Critical","High":"bh High","Medium":"bm Medium",
         "Safe":"bs Safe","Info":"bi Info"}
    c,t = m.get(s,"bi "+s).split(" ",1)
    return f'<span class="badge {c}">{t}</span>'

def method_pill(m):
    mc = {"GET":"mg","POST":"mp2","PUT":"mu","DELETE":"md","PATCH":"mpa"}
    return f'<span class="mp {mc.get(m.upper(),"mg")}">{m.upper()}</span>'

def score_color(s):
    if s >= 80: return "#00c896"
    if s >= 55: return "#ffaa40"
    return "#ff5050"

def score_grade(s):
    if s >= 90: return "A+", "Excellent security posture"
    if s >= 80: return "A",  "Strong security posture"
    if s >= 65: return "B",  "Good, some improvements needed"
    if s >= 50: return "C",  "Moderate risk, action recommended"
    if s >= 30: return "D",  "High risk, immediate action needed"
    return "F", "Critical vulnerabilities detected"

def call_backend(endpoint, **kwargs):
    try:
        r = requests.post(f"{BACKEND}{endpoint}", timeout=30, **kwargs)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("Backend offline. Run: `python main.py` in your backend folder.")
        st.stop()
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail","Unknown error")
        except:
            detail = str(e)
        st.error(f"Error: {detail}")
        st.stop()
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

# ════════════════════════════════════════════════════════════
#  TOPBAR
# ════════════════════════════════════════════════════════════

try:
    health = requests.get(f"{BACKEND}/health", timeout=2).json()
    engine = health.get("engine","Rule Engine")
    online = True
except:
    online = False
    engine = "Offline"

status_cls  = "status-online" if online else "status-offline"
dot_cls     = "dot-green"     if online else "dot-red"
status_text = f"● {engine}" if online else "● Backend offline"

st.markdown(f"""
<div class="topbar">
  <div class="topbar-logo">
    <div class="logo-icon">🛡</div>
    <div class="logo-text">API Security Healer</div>
  </div>
  <div class="status-pill {status_cls}">
    <div class="status-dot {dot_cls}"></div>
    {status_text}
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
#  HERO
# ════════════════════════════════════════════════════════════

if "results" not in st.session_state:
    st.markdown("""
    <div class="hero-wrap">
      <div class="hero-eyebrow">⚡ ML-Powered Security Analysis</div>
      <h1 class="hero-title">Scan. Detect.<br><span>Auto-Heal.</span></h1>
      <p class="hero-desc">
        Upload your API spec and get instant vulnerability detection
        with production-ready healing code — powered by trained ML models.
      </p>
      <div class="hero-stats">
        <div class="hstat">
          <div class="hstat-num">16+</div>
          <div class="hstat-label">Vulnerability types</div>
        </div>
        <div class="hstat">
          <div class="hstat-num">OWASP</div>
          <div class="hstat-label">Top-10 coverage</div>
        </div>
        <div class="hstat">
          <div class="hstat-num">100%</div>
          <div class="hstat-label">Auto-fix code</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
#  INPUT PANEL
# ════════════════════════════════════════════════════════════

if "results" not in st.session_state:
    with st.container():
        st.markdown('<div style="max-width:1300px;margin:0 auto;padding:0 2.5rem">', unsafe_allow_html=True)
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.markdown('<div class="input-card-title">Choose input method</div>', unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["  📁  Upload File  ", "  📋  Paste Content  ", "  ✏️  Manual Entry  "])

        # ── TAB 1: File Upload ────────────────────────────────
        with tab1:
            uploaded = st.file_uploader(
                "Drop OpenAPI 3.0, Swagger, or Postman Collection",
                type=["json","yaml","yml"],
                label_visibility="visible",
                help="Supports OpenAPI 3.0 JSON/YAML and Postman Collection v2.1"
            )
            if uploaded:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;
                            padding:10px 14px;border-radius:10px;margin:8px 0;
                            background:rgba(0,200,150,0.06);
                            border:1px solid rgba(0,200,150,0.2)">
                  <span style="color:#00c896;font-size:13px">✓</span>
                  <span style="font-size:13px;color:#00c896;font-weight:500">{uploaded.name}</span>
                  <span style="font-size:11px;color:rgba(0,200,150,0.5);margin-left:auto">{round(len(uploaded.getvalue())/1024,1)} KB</span>
                </div>""", unsafe_allow_html=True)

            c1, c2 = st.columns([3,1])
            with c2:
                analyze_file = st.button("Scan API →", key="btn_file",
                                          disabled=uploaded is None, use_container_width=True)
            if analyze_file:
                prog = st.progress(0)
                steps = [(15,"Parsing spec..."),(35,"OWASP Top-10 scan..."),(58,"Auth pattern analysis..."),
                         (78,"Injection point detection..."),(92,"Generating heal code..."),(100,"Complete!")]
                for p, msg in steps:
                    prog.progress(p, text=f"⚡ {msg}")
                    time.sleep(0.38)
                st.session_state["results"] = call_backend(
                    "/analyze/file",
                    files={"file":(uploaded.name, uploaded.getvalue(), uploaded.type)}
                )
                st.rerun()

        # ── TAB 2: Paste ──────────────────────────────────────
        with tab2:
            paste = st.text_area(
                "Paste OpenAPI JSON/YAML or plain endpoint list",
                height=180,
                placeholder='Paste OpenAPI JSON:\n{"openapi":"3.0.0","paths":{"/users":{"get":{}},"/admin/delete":{"delete":{}}}}\n\nOr plain list:\nGET /api/v1/users\nPOST /api/v1/login\nDELETE /api/v1/admin\nGET /api/v1/users/{id}',
                label_visibility="collapsed"
            )
            c1, c2 = st.columns([3,1])
            with c2:
                analyze_paste = st.button("Scan API →", key="btn_paste",
                                           disabled=not paste.strip(), use_container_width=True)
            if analyze_paste:
                prog = st.progress(0)
                for p, msg in [(20,"Parsing..."),(55,"Scanning..."),(85,"Healing..."),(100,"Done!")]:
                    prog.progress(p, text=f"⚡ {msg}")
                    time.sleep(0.32)
                st.session_state["results"] = call_backend("/analyze/text", json={"content": paste})
                st.rerun()

        # ── TAB 3: Manual ─────────────────────────────────────
        with tab3:
            if "manual_eps" not in st.session_state:
                st.session_state.manual_eps = []

            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                meth = st.selectbox("Method", ["GET","POST","PUT","DELETE","PATCH"],
                                    label_visibility="collapsed")
            with col2:
                mpath = st.text_input("Path", placeholder="/api/v1/resource/{id}",
                                      label_visibility="collapsed")
            with col3:
                if st.button("Add +", key="add_ep", use_container_width=True):
                    if mpath.strip():
                        st.session_state.manual_eps.append(
                            {"method": meth, "path": mpath.strip(), "summary": ""})
                        st.rerun()

            if st.session_state.manual_eps:
                st.markdown('<div class="sec-label">Endpoints queued</div>', unsafe_allow_html=True)
                to_del = None
                for i, ep in enumerate(st.session_state.manual_eps):
                    cr = st.columns([1, 6, 1])
                    with cr[0]: st.markdown(method_pill(ep["method"]), unsafe_allow_html=True)
                    with cr[1]: st.markdown(f'<span class="ep-path">{ep["path"]}</span>', unsafe_allow_html=True)
                    with cr[2]:
                        if st.button("✕", key=f"del_{i}"):
                            to_del = i
                if to_del is not None:
                    st.session_state.manual_eps.pop(to_del)
                    st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)

            c1, c2 = st.columns([3,1])
            with c2:
                analyze_manual = st.button(
                    "Scan API →", key="btn_manual",
                    disabled=not st.session_state.manual_eps,
                    use_container_width=True
                )
            if analyze_manual:
                prog = st.progress(0)
                for p, msg in [(25,"Scanning..."),(65,"ML inference..."),(100,"Done!")]:
                    prog.progress(p, text=f"⚡ {msg}")
                    time.sleep(0.35)
                st.session_state["results"] = call_backend(
                    "/analyze/manual",
                    json={"endpoints": st.session_state.manual_eps}
                )
                st.rerun()

        st.markdown('</div></div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
#  RESULTS DASHBOARD
# ════════════════════════════════════════════════════════════

if "results" in st.session_state:
    data    = st.session_state["results"]
    results = data["results"]
    score   = data["security_score"]
    sc      = score_color(score)
    grade, grade_desc = score_grade(score)

    st.markdown('<div class="results-wrap">', unsafe_allow_html=True)

    # ── Score Hero ──────────────────────────────────────────
    st.markdown(f"""
    <div class="score-hero">
      <div class="score-circle" style="border-color:{sc}">
        <div class="score-circle-num" style="color:{sc}">{score}</div>
        <div class="score-circle-label">/ 100</div>
      </div>
      <div>
        <div style="display:flex;align-items:baseline;gap:12px">
          <span class="score-grade" style="color:{sc}">{grade}</span>
          <span style="font-size:14px;font-weight:600;color:#ddd8f5">{grade_desc}</span>
        </div>
        <div class="score-summary-text">
          Scanned <b style="color:#ddd8f5">{data['total_endpoints']}</b> endpoints ·
          Found <b style="color:#ff6060">{data['vulnerabilities']}</b> issues ·
          Engine: <b style="color:#9080ee">{data.get('engine','Rule Engine')}</b>
        </div>
        <div class="scan-line" style="max-width:380px;margin-top:10px"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metric Grid ─────────────────────────────────────────
    st.markdown(f"""
    <div class="metric-grid">
      <div class="mcard mcard-c">
        <div class="mcard-num" style="color:#ff5050">{data['critical']}</div>
        <div class="mcard-label">Critical</div>
      </div>
      <div class="mcard mcard-h">
        <div class="mcard-num" style="color:#ffaa40">{data['high']}</div>
        <div class="mcard-label">High</div>
      </div>
      <div class="mcard mcard-m">
        <div class="mcard-num" style="color:#70a8ff">{data['medium']}</div>
        <div class="mcard-label">Medium</div>
      </div>
      <div class="mcard mcard-s">
        <div class="mcard-num" style="color:#00c896">{sum(1 for r in results if r['severity']=='Safe')}</div>
        <div class="mcard-label">Clean</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Two Column Layout ────────────────────────────────────
    col_chart, col_vulns = st.columns([1, 1], gap="large")

    # ── Chart column ────────────────────────────────────────
    with col_chart:
        st.markdown('<div class="sec-label">Severity breakdown</div>', unsafe_allow_html=True)

        sev_counts = {}
        for r in results:
            sev_counts[r["severity"]] = sev_counts.get(r["severity"], 0) + 1

        clr = {"Critical":"#ff4545","High":"#ff8c00","Medium":"#3a8dff","Safe":"#00c896","Info":"#7070a0"}
        labels = list(sev_counts.keys())
        values = list(sev_counts.values())
        colors = [clr.get(l,"#555") for l in labels]

        fig = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.65,
            marker=dict(colors=colors, line=dict(color="#060612", width=3)),
            textinfo="percent", textfont=dict(size=12, family="Space Grotesk", color="#ddd8f5"),
            hovertemplate="<b>%{label}</b><br>%{value} endpoints<extra></extra>",
            pull=[0.04 if l in ("Critical","High") else 0 for l in labels],
        ))
        fig.update_layout(
            showlegend=True, height=260,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=0,b=0,l=0,r=0),
            legend=dict(font=dict(family="Space Grotesk",size=12,color="#a0a0c0"),
                        bgcolor="rgba(0,0,0,0)", x=1, y=0.5),
            annotations=[dict(
                text=f'<b>{score}</b><br><span style="font-size:11px">Score</span>',
                x=0.5, y=0.5, font=dict(size=22, color=sc, family="Space Grotesk"),
                showarrow=False
            )]
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

        # Confidence bars
        vuln_results = [r for r in results if r["severity"] != "Safe"]
        if vuln_results:
            st.markdown('<div class="sec-label">Detection confidence</div>', unsafe_allow_html=True)
            confs = [round(r["confidence"]*100) for r in vuln_results]
            paths = [r["path"][:30] for r in vuln_results]
            bar_colors = [clr.get(r["severity"],"#555") for r in vuln_results]

            fig2 = go.Figure(go.Bar(
                x=confs, y=paths, orientation="h",
                marker=dict(color=bar_colors, opacity=0.75, line=dict(width=0)),
                hovertemplate="<b>%{y}</b><br>%{x}%<extra></extra>",
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=0,b=0,l=0,r=10),
                height=max(160, len(confs)*30),
                xaxis=dict(showgrid=False, color="rgba(160,150,200,0.3)",
                           range=[0,100], ticksuffix="%", tickfont=dict(size=11)),
                yaxis=dict(color="#a090c0", tickfont=dict(family="Fira Code",size=11)),
                font=dict(family="Space Grotesk"),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    # ── Vulnerabilities column ───────────────────────────────
    with col_vulns:
        st.markdown('<div class="sec-label">Vulnerabilities detected</div>', unsafe_allow_html=True)
        vulns = [r for r in results if r["severity"] != "Safe"]
        if not vulns:
            st.markdown("""
            <div style="text-align:center;padding:2rem;
                        background:rgba(0,200,150,0.04);
                        border:1px solid rgba(0,200,150,0.15);
                        border-radius:14px;color:#00c896;font-size:14px">
              All endpoints passed security checks
            </div>""", unsafe_allow_html=True)
        for r in vulns:
            sev_cls = r["severity"].lower()
            st.markdown(f"""
            <div class="vcard vcard-{sev_cls}">
              <div class="vcard-top">
                {sev_badge(r['severity'])}
                {method_pill(r['method'])}
                <span class="ppill">{r['path']}</span>
              </div>
              <div class="vcard-title">{r['heal_title']}</div>
              <div class="vcard-desc">{r['heal_desc']}</div>
              <div class="vcard-meta">
                {r['category']} · {round(r['confidence']*100)}% confidence · {r['mode']}
              </div>
            </div>""", unsafe_allow_html=True)

    # ── Self-Healing Code Fixes ──────────────────────────────
    st.markdown('<div class="sec-label">Self-healing fixes</div>', unsafe_allow_html=True)

    heals = [r for r in results if r["severity"] != "Safe" and r["fix_type"] != "none"]
    if not heals:
        st.markdown('<div class="empty-state">No fixes needed — all endpoints look secure.</div>', unsafe_allow_html=True)

    for r in heals:
        sev_cls = r["severity"].lower()
        badge_html = sev_badge(r["severity"])
        with st.expander(f"{r['heal_title']}   ·   {r['path']}", expanded=False):
            st.markdown(f"""
            <div class="heal-header">
              <div class="heal-icon">⚕</div>
              <div>
                <div class="heal-title">{r['heal_title']}</div>
              </div>
              {badge_html}
            </div>
            <div class="heal-sub">{r['heal_desc']}</div>
            """, unsafe_allow_html=True)
            st.code(r["heal_code"], language="python")

    # ── All Endpoints Table ──────────────────────────────────
    st.markdown('<div class="sec-label">All endpoints scanned</div>', unsafe_allow_html=True)
    for r in results:
        st.markdown(f"""
        <div class="ep-row">
          {method_pill(r['method'])}
          <span class="ep-path">{r['path']}</span>
          {sev_badge(r['severity'])}
          <span class="ep-conf">{round(r['confidence']*100)}%</span>
        </div>""", unsafe_allow_html=True)

    # ── Actions row ─────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2, a3 = st.columns([1,1,2])
    with a1:
        st.download_button(
            "⬇ Download Report (JSON)",
            data=json.dumps(data, indent=2),
            file_name="api_security_report.json",
            mime="application/json",
            use_container_width=True
        )
    with a2:
        if st.button("⟳ Scan Another API", use_container_width=True):
            del st.session_state["results"]
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)