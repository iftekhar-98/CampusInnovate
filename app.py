import streamlit as st
import requests
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

st.title("📍 CampusInnovate: OneMap PoC")

# 1. إدخال التوكن (للخصوصية يفضل وضعه في Secrets)
token = st.secrets["ONEMAP_TOKEN"]

# 2. رفع الصورة
uploaded_file = st.file_uploader("Upload a campus incident photo", type=['jpg', 'jpeg', 'png'])

def get_geocoordinates(image):
    """استخراج الإحداثيات من بيانات EXIF الخاصة بالصورة"""
    exif_data = image._getexif()
    if not exif_data:
        return None, None
    
    # منطق استخراج خطوط الطول والعرض (تبسيط للمثال)
    # ملاحظة: الصور من الجوال غالباً تحتوي على هذه البيانات
    return 1.2966, 103.7764  # إحداثيات افتراضية لـ NUS SDE4 للتجربة

if uploaded_file and token:
    img = Image.open(uploaded_file)
    st.image(img, caption="Uploaded Image", use_column_width=True)
    
    # استخراج الإحداثيات (في الواقع سنستخدم الدالة أعلاه)
    lat, lon = 1.2966, 103.7764 
    
    st.write(f"Raw Coordinates: {lat}, {lon}")

    # 3. ربط OneMap API (Reverse Geocode)
    url = f"https://www.onemap.gov.sg/api/common/reverseGeocode?location={lat},{lon}&buffer=10&addressType=All"
    headers = {"Authorization": token}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if 'GeocodeInfo' in data:
            address = data['GeocodeInfo'][0]['BUILDINGNAME']
            st.success(f"✅ Location Identified: {address}")
            
            # عرض الموقع على الخريطة
            map_data = [{"lat": lat, "lon": lon}]
            st.map(map_data)
        else:
            st.warning("No building found at these coordinates.")
    else:
        st.error(f"API Error: {response.status_code}")
