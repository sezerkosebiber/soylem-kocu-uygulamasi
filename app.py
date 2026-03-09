import streamlit as st
import google.generativeai as genai
import requests

st.set_page_config(page_title="Matematiksel Söylem Koçu", page_icon="🧮")

st.title("Yapay Zekâ Söylem Koçu")
st.markdown("Öğretmen adaylarının matematiksel söylemlerini 5 temel boyutta analiz eden araştırma aracıdır.")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    WEBHOOK_URL = st.secrets["WEBHOOK_URL"]
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error(f"Sistem Hatası: Gerekli anahtarlar bulunamadı. Lütfen yönetici ile iletişime geçin. Detay: {e}")
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
4. Eğer girdi matematiksel bir ifade içermiyorsa sadece şu mesajı ver: "Lütfen analiz edilecek matematiksel bir söylem metni giriniz."
5. Asla yeni bir çözüm veya tam metin üretme. Sadece mevcut metindeki eksikliği bul ve iyileştirme rotası çiz.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=system_instruction
)

ogrenci_no = st.text_input("Öğrenci No veya Rumuz (Araştırma Kaydı İçin):")
ogrenci_metni = st.text_area("Analiz Edilecek Matematiksel Söylem Metni:", height=200)

if st.button("Analiz Et"):
    if not ogrenci_no or not ogrenci_metni:
        st.warning("Lütfen hem öğrenci numaranızı hem de metninizi giriniz.")
    else:
        with st.spinner("Söylem 5 boyutta analiz ediliyor..."):
            try:
                response = model.generate_content(ogrenci_metni)
                analiz_sonucu = response.text
                
                st.subheader("Analiz Sonucu:")
                st.write(analiz_sonucu)
                
                try:
                    veri = {
                        "ogrenci_no": ogrenci_no,
                        "ogrenci_metni": ogrenci_metni,
                        "analiz_sonucu": analiz_sonucu
                    }
                    kayit = requests.post(WEBHOOK_URL, data=veri)
                    if kayit.status_code == 200:
                        st.success("Analiz başarıyla tamamlandı ve veriler araştırma tablosuna kaydedildi! 📝")
                    else:
                        st.warning(f"Kayıt Hatası! Kod: {kayit.status_code} | Detay: {kayit.text}")
                except Exception as kayit_hatasi:
                    st.warning(f"Tabloya bağlantı kurulamadı: {kayit_hatasi}")
                    
            except Exception as e:
                st.error(f"Sistem yoğunluğu nedeniyle bir hata oluştu: {e}")
