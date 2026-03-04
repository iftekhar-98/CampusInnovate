import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from PIL import Image

# إعداد الصفحة
st.set_page_config(page_title="CampusInnovate - Map Pick", page_icon="📍")
st.title("📍 CampusInnovate: Signal Intake")
st.write("ارفع صورة المشكلة وحدد موقعها بدقة على الخريطة.")

# 1. استدعاء التوكن من الـ Secrets
try:
    token = st.secrets["ONEMAP_TOKEN"]
except Exception:
    st.error("❌ تأكدي من إضافة ONEMAP_TOKEN في إعدادات Streamlit.")
    st.stop()

# 2. رفع الصورة (Image Submission)
uploaded_file = st.file_uploader("1. Upload Incident Photo", type=['jpg', 'jpeg', 'png'])
if uploaded_file:
    st.image(Image.open(uploaded_file), width=300)

st.divider()

# 3. اختيار الموقع على الخريطة (Interactive Map)
st.subheader("2. Select Location on Map")
st.info("اضغطي على الخريطة في مكان المشكلة لوضع علامة (Pin).")

# إحداثيات مركز NUS الافتراضية
nus_center = [1.2966, 103.7764]

# إنشاء الخريطة باستخدام Folium
m = folium.Map(location=nus_center, zoom_start=16)
m.add_child(folium.LatLngPopup()) # يظهر الإحداثيات عند الضغط

# عرض الخريطة واستقبال بيانات الضغط
output = st_folium(m, width=700, height=400)

# 4. معالجة بيانات الضغط والربط مع OneMap
if output and output.get("last_clicked"):
    lat = output["last_clicked"]["lat"]
    lon = output["last_clicked"]["lng"]
    
    st.write(f"Selected Coordinates: `{lat:.6f}, {lon:.6f}`")
    
    # طلب بيانات المبنى من OneMap (Reverse Geocode)
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://www.onemap.gov.sg/api/common/reverseGeocode?location={lat},{lon}&buffer=20&addressType=All"
    
    with st.spinner("جاري تحديد اسم المبنى..."):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'GeocodeInfo' in data and len(data['GeocodeInfo']) > 0:
                building_name = data['GeocodeInfo'][0]['BUILDINGNAME']
                
                # عرض النتيجة النهائية (المخرجات التي يحتاجها فريق UCI)
                st.success(f"✅ Building Identified: **{building_name}**")
                
                # زر إرسال البلاغ (لمحاكاة اكتمال العملية)
                if st.button("Submit Report"):
                    st.balloons()
                    st.success("Report submitted to UCI Governance Layer!")
            else:
                st.warning("لم يتم العثور على مبنى في هذه النقطة، يرجى المحاولة مرة أخرى.")
        else:
            st.error(f"OneMap Error: {response.status_code}. يرجى التحقق من التوكن.")
