import streamlit as st
import google.generativeai as genai
import requests
import base64
from PIL import Image

# Sayfa yapılandırması
st.set_page_config(page_title="Matematiksel Söylem Koçu", page_icon="🧮", layout="centered")

# --- KURUMSAL BANNER VE BAŞLIK BÖLÜMÜ ---
# vertical_alignment="center" sayesinde logo ve metin dikeyde tam ortalanır.
col1, col2 = st.columns([1, 4], vertical_alignment="center")

with col1:
    logo_url = "https://cdn.iuc.edu.tr/FileHandler.ashx?f=SuN_4kHlSEuRLhTvH_RFZA" 
    st.image(logo_url, width=120)

with col2:
    st.markdown("""
        <div style='text-align: left;'>
            <h2 style='color: #003366; margin: 0; font-family: sans-serif; font-size: 1.8em; font-weight: bold;'>İSTANBUL ÜNİVERSİTESİ-CERRAHPAŞA</h2>
            <h3 style='color: #003366; margin: 0; font-family: sans-serif; font-size: 1.4em; font-weight: 500;'>Hasan Âli Yücel Eğitim Fakültesi</h3>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border: 1.5px solid #003366; margin-top: 10px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# Çalışma Başlığı - Mahir Hocamızın İsmiyle Birlikte
st.markdown("""
    <style>
    .study-title {
        text-align: center;
        color: #ffffff;
        background: linear-gradient(90deg, #003366 0%, #00509d 100%);
        padding: 35px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    .study-title h1 {
        margin: 0;
        font-size: 2.1em;
        font-weight: bold;
    }
    .authors {
        margin-top: 15px;
        font-size: 1.4em;
        font-weight: 500;
    }
    .platform-sub {
        margin-top: 8px;
        font-size: 1.1em;
        opacity: 0.9;
        font-weight: 300;
    }
    </style>
    <div class='study-title'>
        <h1>Matematiksel Söylem Analizi ve Geliştirme Portalı</h1>
        <div class='authors'>Doç. Dr. Mahir BİBER & Doç. Dr. Sezer KÖSE BİBER</div>
        <div class='platform-sub'>Yapay Zekâ Destekli Söylem Koçu Araştırma Platformu</div>
    </div>
""", unsafe_allow_html=True)
# --- KURUMSAL BÖLÜM SONU ---



# Güvenli Anahtar Kontrolü
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    WEBHOOK_URL = st.secrets["WEBHOOK_URL"]
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error(f"Sistem Hatası: Secrets (API_KEY veya WEBHOOK_URL) bulunamadı.")
    st.stop()

# Analiz Talimatı
system_instruction = """
Sen, öğretmen adaylarının matematiksel söylem kalitesini ölçen, duygudan arındırılmış, analitik bir Yapay Zekâ Söylem Koçusun.
1. Sadece Türkçe yanıt ver.
2. Sadece şu 5 boyutu analiz et: (1) Doğruluk ve Dil, (2) Kesinlik ve Koşul, (3) Temsil Geçişi, (4) Argümantasyon, (5) Revoicing.
3. Formata kesin uy: [Boyut Adı] - Bulgu: "..." - Öneri: "..."
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=system_instruction
)

# Giriş Alanları
ogrenci_no = st.text_input("Öğrenci No veya Rumuz (Araştırma Kaydı İçin):")
st.markdown("---")
ogrenci_metni = st.text_area("Yazılı Yanıtınız (İsteğe bağlı):", height=150)

# Görsel Seçenekleri (İkisi de aynı anda kullanılabilir)
col1, col2 = st.columns(2)
with col1:
    yuklenen_dosya = st.file_uploader("Kağıttaki Yanıtı Yükle", type=["png", "jpg", "jpeg"])
with col2:
    kamera_cekimi = st.camera_input("Veya Kameradan Çek")

if st.button("Analiz Et"):
    if not ogrenci_no:
        st.warning("Lütfen öğrenci numaranızı/rumuzunuzu giriniz.")
    elif not ogrenci_metni and not yuklenen_dosya and not kamera_cekimi:
        st.warning("Lütfen bir metin yazın, dosya yükleyin veya fotoğraf çekin.")
    else:
        with st.spinner("Tüm veriler analiz ediliyor..."):
            try:
                # 1. YAPAY ZEKA İÇİN İÇERİK HAZIRLAMA
                icerik = []
                if ogrenci_metni:
                    icerik.append(ogrenci_metni)
                if yuklenen_dosya:
                    icerik.append(Image.open(yuklenen_dosya))
                if kamera_cekimi:
                    icerik.append(Image.open(kamera_cekimi))
                
                # Analiz Al
                response = model.generate_content(icerik)
                analiz_sonucu = response.text
                
                st.subheader("Analiz Sonucu:")
                st.write(analiz_sonucu)
                
                # 2. GÖRSELLERİ WEBHOOK İÇİN HAZIRLAMA (Base64)
                def gorsel_kodla(gorsel, sonek):
                    if gorsel is None: return "", "", ""
                    gorsel.seek(0)
                    b64 = base64.b64encode(gorsel.getvalue()).decode('utf-8')
                    return b64, "image/jpeg", f"{ogrenci_no}_{sonek}.jpg"

                g1_base, g1_mime, g1_ad = gorsel_kodla(yuklenen_dosya, "dosya")
                g2_base, g2_mime, g2_ad = gorsel_kodla(kamera_cekimi, "kamera")

                # Kayıt Metni
                kayit_metni = ogrenci_metni if ogrenci_metni else "[Metin Girilmedi]"
                if yuklenen_dosya: kayit_metni += " [+Dosya]"
                if kamera_cekimi: kayit_metni += " [+Kamera]"

                # 3. VERİLERİ TABLOYA GÖNDERME
                veri_paketi = {
                    "ogrenci_no": ogrenci_no,
                    "ogrenci_metni": kayit_metni,
                    "analiz_sonucu": analiz_sonucu,
                    "gorsel1_base64": g1_base, "gorsel1_mime": g1_mime, "gorsel1_adi": g1_ad,
                    "gorsel2_base64": g2_base, "gorsel2_mime": g2_mime, "gorsel2_adi": g2_ad
                }
                
                gonderim = requests.post(WEBHOOK_URL, data=veri_paketi)
                
                if "Başarılı" in gonderim.text:
                    st.success("Analiz bitti ve tüm veriler (Dosya + Kamera + Metin) kaydedildi! 📝✅")
                else:
                    st.error(f"Kayıt Hatası: {gonderim.text}")
                    
            except Exception as e:
                st.error(f"Süreçte bir hata oluştu: {e}")
