import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from PIL import Image
import pandas as pd
from datetime import datetime
import uuid

# --- CONFIG & STYLES ---
st.set_page_config(page_title="CampusInnovate v1.0", page_icon="🏢", layout="wide")

# جلب بيانات OneMap من Secrets
try:
    ONEMAP_TOKEN = st.secrets["ONEMAP_TOKEN"]
except:
    st.error("Missing OneMap Token in Secrets!")
    st.stop()

# --- MOCK DATABASE ---
# في الواقع نستخدم SQL، هنا نستخدم session_state للمحاكاة
if 'reports_db' not in st.session_state:
    st.session_state.reports_db = []

# --- SHARED FUNCTIONS ---
def get_building_from_onemap(lat, lon):
    headers = {
        "Authorization": f"Bearer {ONEMAP_TOKEN}",
        "User-Agent": "Mozilla/5.0"
    }
    url = f"https://www.onemap.gov.sg/api/common/reverseGeocode?location={lat},{lon}&buffer=20&addressType=All"
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            return data['GeocodeInfo'][0]['BUILDINGNAME'] if data.get('GeocodeInfo') else "Unknown Location"
    except:
        return "Connection Error"
    return "Unknown Location"

def ai_process_signal(description, lat, lon):
    """محاكاة طبقة الذكاء الاصطناعي (AI Intelligence Layer)"""
    # 1. تصنيف بسيط بناءً على كلمات مفتاحية
    desc = description.lower()
    category = "General"
    if any(w in desc for w in ["pipe", "water", "leak"]): category = "Facilities - Plumbing"
    elif any(w in desc for w in ["light", "power", "electricity"]): category = "Facilities - Electrical"
    elif any(w in desc for w in ["trash", "dirty", "clean"]): category = "Cleanliness"
    
    # 2. تحديد الاستعجال (Urgency)
    urgency = "Medium"
    if any(w in desc for w in ["danger", "urgent", "fire", "flood"]): urgency = "High"
    
    # 3. كشف التكرار (Duplicate Detection) - P0
    is_duplicate = False
    cluster_id = str(uuid.uuid4())[:8]
    for report in st.session_state.reports_db:
        # إذا كان البلاغ في نفس الموقع (بفارق بسيط) ونفس الفئة
        if abs(report['lat'] - lat) < 0.0005 and report['ai_category'] == category:
            is_duplicate = True
            cluster_id = report['cluster_id']
            break
            
    return category, urgency, is_duplicate, cluster_id

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🚀 CampusInnovate")
role = st.sidebar.radio("Select View:", ["Student Portal (Reporter)", "UCI Staff Dashboard (Governance)"])

# --- VIEW 1: STUDENT PORTAL ---
if role == "Student Portal (Reporter)":
    st.header("📢 Report a Campus Incident")
    st.info("Reduce friction: Capture photo, select location, and submit. [cite: 188]")
    
    col1, col2 = st.columns(2)
    
    with col1:
        img_file = st.file_uploader("1. Take/Upload Photo (P1) [cite: 257]", type=['jpg', 'png'])
        if img_file:
            st.image(img_file, width=300)
            
        description = st.text_area("2. Describe the issue (Short Description) [cite: 258]", max_chars=200)
        user_cat = st.selectbox("3. Manual Category Selection [cite: 258]", ["Facilities", "Safety", "Cleanliness", "Others"])

    with col2:
        st.write("4. Pin Location on Map (P0) [cite: 257]")
        m = folium.Map(location=[1.2966, 103.7764], zoom_start=16)
        m.add_child(folium.LatLngPopup())
        map_data = st_folium(m, width=500, height=300)
        
        if map_data and map_data.get("last_clicked"):
            lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
            building = get_building_from_onemap(lat, lon)
            st.success(f"📍 Location: {building}")
            
            if st.button("🚀 Submit Signal"):
                # AI Processing
                ai_cat, urgency, is_dup, c_id = ai_process_signal(description, lat, lon)
                
                new_report = {
                    "id": str(uuid.uuid4())[:6],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "building": building,
                    "lat": lat, "lon": lon,
                    "user_desc": description,
                    "ai_category": ai_cat,
                    "urgency": urgency,
                    "is_duplicate": is_dup,
                    "cluster_id": c_id,
                    "status": "Submitted"
                }
                st.session_state.reports_db.append(new_report)
                st.balloons()
                st.success(f"Report Submitted! ID: {new_report['id']} [cite: 258]")

# --- VIEW 2: UCI STAFF DASHBOARD ---
else:
    st.header("⚖️ UCI Signal Governance Queue")
    st.write("AI-assisted triage and human-in-the-loop review. [cite: 191, 231]")
    
    if not st.session_state.reports_db:
        st.warning("No reports in the queue yet.")
    else:
        df = pd.DataFrame(st.session_state.reports_db)
        
        # Dashboard Metrics (Operational Analytics) [cite: 262]
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Signals", len(df))
        m2.metric("Duplicate Ratio", f"{(df['is_duplicate'].sum()/len(df)*100):.1f}%")
        m3.metric("High Urgency", len(df[df['urgency'] == 'High']))

        st.divider()

        # Governance Queue (Review Queue) [cite: 260]
        for idx, row in df.iterrows():
            with st.expander(f"#{row['id']} - {row['building']} ({row['urgency']})"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.write(f"**User Description:** {row['user_desc']}")
                    st.write(f"**AI Classification:** {row['ai_category']} (Conf: 92%) [cite: 259]")
                    if row['is_duplicate']:
                        st.warning(f"⚠️ Potential Duplicate Detected (Cluster: {row['cluster_id']}) [cite: 259]")
                
                with c2:
                    st.write(f"**Status:** {row['status']}")
                    new_status = st.selectbox("Update Lifecycle ", 
                                              ["Submitted", "In Review", "In Progress", "Resolved"], 
                                              key=f"status_{idx}",
                                              index=["Submitted", "In Review", "In Progress", "Resolved"].index(row['status']))
                    if st.button("Update Record", key=f"btn_{idx}"):
                        st.session_state.reports_db[idx]['status'] = new_status
                        st.rerun()

    # Visualizing Hotspots (Operational Analytics) [cite: 262]
    if st.sidebar.checkbox("Show Issue Map (Analytics)"):
        st.subheader("Issue Clustering Map")
        m_dash = folium.Map(location=[1.2966, 103.7764], zoom_start=15)
        for r in st.session_state.reports_db:
            color = "red" if r['urgency'] == "High" else "orange"
            folium.Marker([r['lat'], r['lon']], popup=f"{r['ai_category']} - {r['status']}", icon=folium.Icon(color=color)).add_to(m_dash)
        st_folium(m_dash, width=1000, height=400)
