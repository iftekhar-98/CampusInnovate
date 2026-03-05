import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from PIL import Image

# إعدادات الصفحة - تعزيز هوية المشروع
st.set_page_config(page_title="CampusInnovate - Map Intake", page_icon="📍", layout="centered")
st.title("📍 CampusInnovate: Signal Intake Layer")
st.markdown("""
بناءً على المرحلة الثانية من المشروع (Design & Build)، هذا النموذج يسمح للمستخدم بتقديم بلاغ مدعوم بالموقع الجغرافي الدقيق.
""")

# 1. جلب التوكن من Secrets (تأكدي أنه بين علامات تنصيص في الإعدادات)
try:
    token = st.secrets["ONEMAP_TOKEN"]
except Exception:
    st.error("❌ خطأ: لم يتم العثور على 'ONEMAP_TOKEN' في إعدادات Streamlit Secrets.")
    st.stop()

# 2. طبقة استلام الإشارات (Signal Intake Layer) - رفع الصورة
st.subheader("1. Upload Incident Image")
uploaded_file = st.file_uploader("ارفع صورة توضح المشكلة (عطل، زحام، إلخ)", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    st.image(Image.open(uploaded_file), caption="المعاينة الأولية للبلاغ", width=400)

st.divider()

# 3. اختيار الموقع (Geospatial Tagging)
st.subheader("2. Pinpoint Location")
st.info("قم بالضغط على الخريطة لتحديد موقع المشكلة بدقة في حرم الجامعة.")

# إحداثيات مركز NUS (تقريبي) للبدء
nus_center = [1.2966, 103.7764]

# إنشاء الخريطة
m = folium.Map(location=nus_center, zoom_start=16)
m.add_child(folium.LatLngPopup()) # لإظهار الإحداثيات عند الضغط

# عرض الخريطة واستقبال البيانات
map_output = st_folium(m, width=700, height=450)

# 4. معالجة البلاغ وربطه مع OneMap API
if map_output and map_output.get("last_clicked"):
    lat = map_output["last_clicked"]["lat"]
    lon = map_output["last_clicked"]["lng"]
    
    st.write(f"Coordinates Selected: `{lat:.6f}, {lon:.6f}`")
    
    # تحديث الـ Headers لتجنب خطأ 403
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.onemap.gov.sg/"
    }
    
    # رابط الـ Reverse Geocode (بدون مسافات في الإحداثيات)
    api_url = f"https://www.onemap.gov.sg/api/common/reverseGeocode?location={lat},{lon}&buffer=20&addressType=All"
    
    with st.spinner("جاري التحقق من الموقع عبر OneMap..."):
        try:
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if 'GeocodeInfo' in data and len(data['GeocodeInfo']) > 0:
                    building_name = data['GeocodeInfo'][0]['BUILDINGNAME']
                    
                    # عرض النتيجة النهائية (Operational intelligence)
                    st.success(f"✅ تم تحديد الموقع: **{building_name}**")
                    
                    # زر إرسال البلاغ لمحاكاة دورة الحياة (Lifecycle Tracking)
                    if st.button("Submit Signal to UCI"):
                        st.balloons()
                        st.info("تم إرسال البلاغ بنجاح إلى فريق UCI للمراجعة.")
                else:
                    st.warning("📍 النقطة المختارة لا تتبع لأي مبنى مسجل حالياً.")
            elif response.status_code == 403:
                st.error("❌ خطأ 403: تم رفض الوصول. يرجى التأكد من تجديد التوكن من بوابة OneMap ووضعه في الـ Secrets.")
            else:
                st.error(f"❌ خطأ في الـ API: {response.status_code}")
                
        except Exception as e:
            st.error(f"⚠️ فشل الاتصال بالخادم: {e}")
