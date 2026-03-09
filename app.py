import streamlit as st
import google.generativeai as genai
import requests
import base64
from PIL import Image

st.set_page_config(page_title="Matematiksel Söylem Koçu", page_icon="🧮")

st.title("Yapay Zekâ Söylem Koçu")
st.markdown("Öğretmen adaylarının matematiksel söylemlerini 5 temel boyutta analiz eden araştırma aracıdır.")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    WEBHOOK_URL = st.secrets["WEBHOOK_URL"]
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error(f"Sistem Hatası: Gerekli anahtarlar bulunamadı. Detay: {e}")
    st.stop()

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

ogrenci_no = st.text_input("Öğrenci No veya Rumuz (Araştırma Kaydı İçin):")

st.markdown("---")
st.markdown("**Analiz Edilecek Veriyi Girin (Metin yazabilir, fotoğraf yükleyebilir veya her ikisini de yapabilirsiniz):**")

ogrenci_metni = st.text_area("Yazılı Yanıtınız (İsteğe bağlı):", height=150)

# Görsel Yükleme Alanları
col1, col2 = st.columns(2)
with col1:
    yuklenen_gorsel = st.file_uploader("Kağıttaki Yanıtı Yükle", type=["png", "jpg", "jpeg"])
with col2:
    kamera_gorsel = st.camera_input("Veya Kameradan Çek")

if st.button("Analiz Et"):
    # Hangi görselin kullanıldığını belirliyoruz (Kamera öncelikli)
    aktif_gorsel = kamera_gorsel if kamera_gorsel else yuklenen_gorsel
    
    if not ogrenci_no:
        st.warning("Lütfen araştırma kaydı için öğrenci numaranızı/rumuzunuzu giriniz.")
    elif not ogrenci_metni and not aktif_gorsel:
        st.warning("Lütfen analiz için bir metin yazın veya bir fotoğraf ekleyin.")
    else:
        with st.spinner("Söylem (ve varsa görsel) 5 boyutta analiz ediliyor..."):
            try:
                # Yapay zekaya gidecek paketi hazırlıyoruz
                icerik = []
                if ogrenci_metni:
                    icerik.append(ogrenci_metni)
                if aktif_gorsel:
                    img = Image.open(aktif_gorsel)
                    icerik.append(img)
                    
                response = model.generate_content(icerik)
                analiz_sonucu = response.text
                
                st.subheader("Analiz Sonucu:")
                st.write(analiz_sonucu)
                
                # Tabloya kaydedilecek metni ayarlıyoruz
                kaydedilecek_metin = ogrenci_metni
                if aktif_gorsel and not ogrenci_metni:
                    kaydedilecek_metin = "[Sadece Görsel Yüklendi]"
                elif aktif_gorsel and ogrenci_metni:
                    kaydedilecek_metin = ogrenci_metni + " [+Görsel Yüklendi]"
                    
                # Görseli Google Drive'a göndermek için şifreliyoruz (Base64)
                gorsel_base64 = ""
                gorsel_adi = ""
                gorsel_mimeType = ""
                
                if aktif_gorsel:
                    aktif_gorsel.seek(0) # Dosyayı baştan okumak için
                    gorsel_bytes = aktif_gorsel.getvalue()
                    gorsel_base64 = base64.b64encode(gorsel_bytes).decode('utf-8')
                    gorsel_adi = f"{ogrenci_no}_gorsel.jpg"
                    gorsel_mimeType = "image/jpeg"

                try:
                    # Kuryeye verileri teslim ediyoruz
                    veri = {
                        "ogrenci_no": ogrenci_no,
                        "ogrenci_metni": kaydedilecek_metin,
                        "analiz_sonucu": analiz_sonucu,
                        "gorsel_base64": gorsel_base64,
                        "gorsel_adi": gorsel_adi,
                        "gorsel_mimeType": gorsel_mimeType
                    }
                    kayit = requests.post(WEBHOOK_URL, data=veri)
                    
                    if kayit.status_code == 200:
                        st.success("Analiz başarıyla tamamlandı ve veriler (görsel dahil) araştırma tablosuna kaydedildi! 📝")
                    else:
                        st.warning(f"Kayıt Hatası! Kod: {kayit.status_code} | Detay: {kayit.text}")
                except Exception as kayit_hatasi:
                    st.warning(f"Tabloya bağlantı kurulamadı: {kayit_hatasi}")
                    
            except Exception as e:
                st.error(f"Sistem yoğunluğu nedeniyle bir hata oluştu: {e}")
