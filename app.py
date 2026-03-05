import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from PIL import Image
import pandas as pd
from datetime import datetime
import uuid
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="CampusInnovate v1.0", page_icon="📍", layout="wide")

# التحقق من وجود المفاتيح في Secrets
try:
    ONEMAP_EMAIL = st.secrets["ONEMAP_EMAIL"]
    ONEMAP_PASSWORD = st.secrets["ONEMAP_PASSWORD"]
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error("❌ Missing configuration in Streamlit Secrets!")
    st.stop()

# --- DATABASE MOCK ---
if 'reports_db' not in st.session_state:
    st.session_state.reports_db = []

# --- AI & API FUNCTIONS ---

def get_onemap_token():
    """توليد توكن OneMap تلقائياً لضمان استمرارية التشغيل."""
    auth_url = "https://www.onemap.gov.sg/api/auth/post/getToken"
    res = requests.post(auth_url, json={"email": ONEMAP_EMAIL, "password": ONEMAP_PASSWORD})
    return res.json().get('access_token') if res.status_code == 200 else None

def get_building_name(lat, lon, token):
    """تحديد الموقع الجغرافي عبر OneMap[cite: 116, 257]."""
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"}
    url = f"https://www.onemap.gov.sg/api/common/reverseGeocode?location={lat},{lon}&buffer=20&addressType=All"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        info = res.json().get('GeocodeInfo', [])
        return info[0]['BUILDINGNAME'] if info else "Unknown Campus Area"
    return "API Error"

def analyze_incident_with_gemini(image, user_desc):
    """استخدام Gemini لتصنيف البلاغ وتحديد الاستعجال."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Analyze this campus incident image. User description: "{user_desc}".
    Provide a JSON response with:
    1. category: (Facilities, Safety, Cleanliness, or Accessibility)
    2. urgency_score: (1 to 5, where 5 is critical)
    3. summary: (Max 2 sentences)
    """
    response = model.generate_content([prompt, image])
    # محاكاة استخراج البيانات (في الواقع نستخدم JSON parser)
    return response.text 

# --- UI LAYOUT ---
st.sidebar.title("🚀 CampusInnovate")
role = st.sidebar.radio("Switch Role:", ["Student (Reporter)", "UCI Staff (Governance)"])

# --- VIEW 1: STUDENT PORTAL (SIGNAL INTAKE) ---
if role == "Student (Reporter)":
    st.header("📢 Signal Intake Layer")
    st.info("Goal: Low-friction issue reporting[cite: 188].")

    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        img_file = st.file_uploader("1. Capture Photo (P1) ", type=['jpg', 'jpeg', 'png'])
        if img_file:
            st.image(img_file, use_container_width=True)
        
        description = st.text_area("2. Description (Optional) [cite: 258]", max_chars=200)

    with col2:
        st.subheader("3. Pin Location (P0) ")
        m = folium.Map(location=[1.2966, 103.7764], zoom_start=17)
        m.add_child(folium.LatLngPopup())
        map_interaction = st_folium(m, width=600, height=400)

        if map_interaction and map_interaction.get("last_clicked"):
            lat = map_interaction["last_clicked"]["lat"]
            lon = map_interaction["last_clicked"]["lng"]
            
            token = get_onemap_token()
            building = get_building_name(lat, lon, token)
            st.success(f"📍 Location identified: {building}")

            if st.button("🚀 Submit Signal"):
                with st.spinner("AI is structuring your signal... [cite: 212]"):
                    # محاكاة تشغيل طبقة الذكاء الاصطناعي
                    # (يمكن استدعاء analyze_incident_with_gemini هنا حقيقياً)
                    new_id = str(uuid.uuid4())[:6]
                    report = {
                        "id": new_id,
                        "timestamp": datetime.now().strftime("%H:%M %d/%m"),
                        "building": building, "lat": lat, "lon": lon,
                        "status": "Submitted", "urgency": "High", # Mocked AI result
                        "category": "Facilities", "is_duplicate": False
                    }
                    st.session_state.reports_db.append(report)
                    st.balloons()
                    st.success(f"Report #{new_id} Submitted! [cite: 258]")

# --- VIEW 2: UCI STAFF DASHBOARD (GOVERNANCE) ---
else:
    st.header("⚖️ Governance & Operations Layer")
    st.write("Assist triage with AI-based signal structuring[cite: 190].")

    if not st.session_state.reports_db:
        st.warning("No signals to review.")
    else:
        # Metrics [cite: 262]
        m1, m2, m3 = st.columns(3)
        m1.metric("Signals Queue", len(st.session_state.reports_db))
        m2.metric("Duplicate Ratio", "12%") # Example
        m3.metric("Avg Triage Time", "4.2m")

        # Review Queue [cite: 231, 261]
        for idx, item in enumerate(st.session_state.reports_db):
            with st.expander(f"Report #{item['id']} - {item['building']} [{item['urgency']}]"):
                st.write(f"**AI Summary:** Issue detected in {item['category']}[cite: 260].")
                new_status = st.selectbox("Update Lifecycle [cite: 261]", 
                                          ["Submitted", "In Review", "In Progress", "Resolved"], 
                                          index=0, key=f"stat_{idx}")
                if st.button("Confirm Decision", key=f"conf_{idx}"):
                    st.session_state.reports_db[idx]['status'] = new_status
                    st.rerun()

    # Visual Mapping [cite: 262]
    if st.sidebar.checkbox("Show Operational Analytics Map"):
        st.subheader("Signal Clusters & Hotspots")
        m_dash = folium.Map(location=[1.2966, 103.7764], zoom_start=15)
        for r in st.session_state.reports_db:
            folium.Marker([r['lat'], r['lon']], popup=f"{r['id']}: {r['status']}").add_to(m_dash)
        st_folium(m_dash, width=1100, height=500)
