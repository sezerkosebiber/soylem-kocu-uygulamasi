import streamlit as st
import google.generativeai as genai
import requests
import base64
from PIL import Image

st.set_page_config(page_title="Matematiksel Söylem Koçu", page_icon="🧮")

st.title("Yapay Zekâ Söylem Koçu")
st.markdown("Öğretmen adaylarının matematiksel söylemlerini 5 temel boyutta analiz eden araştırma aracıdır.")

# Güvenli Anahtar Kontrolü
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    WEBHOOK_URL = st.secrets["WEBHOOK_URL"]
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error(f"Sistem Hatası: Secrets (API_KEY veya WEBHOOK_URL) bulunamadı. Detay: {e}")
    st.stop()

# Çoklu Ortam Uyumlu Sistem Talimatı
system_instruction = """
Sen, öğretmen adaylarının matematiksel söylem kalitesini ölçen, duygudan arındırılmış, analitik bir Yapay Zekâ Söylem Koçusun.

KATI KURALLAR:
1. Sadece Türkçe yanıt ver.
2. Sadece şu 5 boyutu analiz et: (1) Doğruluk ve Dil, (2) Kesinlik ve Koşul, (3) Temsil Geçişi, (4) Argümantasyon, (5) Revoicing.
3. Her boyut için formata kesin uy:
   [Boyut Adı]
   - Bulgu: "..."
   - Öneri: "..."
4. Eğer girdi (metin veya görsel) matematiksel bir ifade içermiyorsa sadece şu mesajı ver: "Lütfen analiz edilecek matematiksel bir söylem metni veya görseli giriniz."
5. Asla yeni bir çözüm veya tam metin üretme. Sadece mevcut metindeki/görseldeki eksikliği bul ve iyileştirme rotası çiz.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=system_instruction
)

# Kullanıcı Giriş Alanları
ogrenci_no = st.text_input("Öğrenci No veya Rumuz (Araştırma Kaydı İçin):")

st.markdown("---")
st.markdown("**Analiz Edilecek Veriyi Girin:**")

ogrenci_metni = st.text_area("Yazılı Yanıtınız (İsteğe bağlı):", height=150)

col1, col2 = st.columns(2)
with col1:
    yuklenen_gorsel = st.file_uploader("Kağıttaki Yanıtı Yükle", type=["png", "jpg", "jpeg"])
with col2:
    kamera_gorsel = st.camera_input("Veya Kameradan Çek")

# Analiz ve Kayıt İşlemi
if st.button("Analiz Et"):
    aktif_gorsel = kamera_gorsel if kamera_gorsel else yuklenen_gorsel
    
    if not ogrenci_no:
        st.warning("Lütfen araştırma kaydı için öğrenci numaranızı/rumuzunuzu giriniz.")
    elif not ogrenci_metni and not aktif_gorsel:
        st.warning("Lütfen analiz için bir metin yazın veya bir fotoğraf ekleyin.")
    else:
        with st.spinner("Söylem analiz ediliyor ve veritabanına işleniyor..."):
            try:
                # 1. Yapay Zekâ Analizi
                icerik = []
                if ogrenci_metni:
                    icerik.append(ogrenci_metni)
                if aktif_gorsel:
                    img = Image.open(aktif_gorsel)
                    icerik.append(img)
                    
                response = model.generate_content(icerik)
                analiz_sonucu = response.text
                
                # Sonucu Ekrana Yazdır
                st.subheader("Analiz Sonucu:")
                st.write(analiz_sonucu)
                
                # 2. Veri Hazırlama (Drive ve Tablo için)
                kaydedilecek_metin = ogrenci_metni if ogrenci_metni else "[Sadece Görsel Yüklendi]"
                if aktif_gorsel and ogrenci_metni:
                    kaydedilecek_metin += " [+Görsel Yüklendi]"
                
                gorsel_base64 = ""
                gorsel_adi = ""
                gorsel_mimeType = ""
                
                if aktif_gorsel:
                    aktif_gorsel.seek(0)
                    gorsel_bytes = aktif_gorsel.getvalue()
                    gorsel_base64 = base64.b64encode(gorsel_bytes).decode('utf-8')
                    gorsel_adi = f"{ogrenci_no}_{int(st.session_state.get('counter', 0))}.jpg"
                    gorsel_mimeType = "image/jpeg"

                # 3. Webhook (Google Tablo) Kaydı
                veri = {
                    "ogrenci_no": ogrenci_no,
                    "ogrenci_metni": kaydedilecek_metin,
                    "analiz_sonucu": analiz_sonucu,
                    "gorsel_base64": gorsel_base64,
                    "gorsel_adi": gorsel_adi,
                    "gorsel_mimeType": gorsel_mimeType
                }
                
                kayit_isteği = requests.post(WEBHOOK_URL, data=veri)
                
                # Kritik Kontrol: Google "Başarılı" dedi mi?
                if "Başarılı" in kayit_isteği.text:
                    st.success("Tebrikler! Analiz yapıldı ve tüm veriler araştırma tablonuza güvenle kaydedildi. 📝✅")
                else:
                    st.error(f"Analiz yapıldı ancak TABLOYA KAYDEDİLEMEDİ. Hata: {kayit_isteği.text}")
                    
            except Exception as e:
                st.error(f"Bir hata oluştu: {e}")
