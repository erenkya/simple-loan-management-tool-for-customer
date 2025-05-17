import streamlit as st
from DatabaseConnector.mysqlConnector import get_all_acik_hesap, pay_acik_hesap, delete_acik_hesap

st.set_page_config(page_title="Açık Hesap Ödeme", page_icon="💸", layout="wide")
st.title("💼 Açık Hesaplar")
st.write("Açık hesaplara borç ödeme yapabilir veya hesabı silebilirsiniz.")

def para_birimi_simgesi(currency_code):
    if currency_code == "USD":
        return "$"
    elif currency_code == "EUR":
        return "€"
    elif currency_code in ("TRY", "TL"):
        return "₺"
    else:
        return ""

# Tüm açık hesapları al
acik_hesaplar = get_all_acik_hesap()

# 🔍 Filtreleme
filter_text = st.text_input("🔍 İsimle Filtrele", placeholder="Müşteri adı girin...").strip().lower()

if filter_text:
    acik_hesaplar = [h for h in acik_hesaplar if filter_text in h['name'].lower()]

# Listeleme
if not acik_hesaplar:
    st.info("🔎 Eşleşen açık hesap bulunamadı.")
else:
    for hesap in acik_hesaplar:
        with st.container():
            birim_simgesi = para_birimi_simgesi(hesap.get('kur'))
            
            st.subheader(f"👤 {hesap['name']} - {hesap['number']}")
            st.markdown(f"""
            - 📦 Ürünler: `{hesap['products']}`
            - 💰 Başlangıç Tutarı: `{hesap['start_price']} {birim_simgesi}`
            - 🔻 Kalan Borç: `{hesap['remaining_price']} {birim_simgesi}`
            - 💱 Kur: `{hesap['kur']}`
            - 🕒 Oluşturulma: `{hesap['created_at']}`
            """)

            col1, col2, col3 = st.columns([1.5, 1.5, 1])

            if hesap['remaining_price'] == 0:
                col1.success("✅ Borç tamamen ödenmiş.")
            else:
                with col1:
                    payment = st.number_input(
                        f"💵 Ödeme Tutarı ({birim_simgesi})", 
                        min_value=1, 
                        max_value=hesap['remaining_price'], 
                        step=1, 
                        key=f"odeme_{hesap['id']}"
                    )
                with col2:
                    payment_type = st.selectbox(
                        "💳 Ödeme Türü", 
                        ["Nakit", "Kredi Kartı", "Havale", "Havale->E"],
                        key=f"payment_type_{hesap['id']}"
                    )
                with col3:
                    if st.button("✅ Ödeme Yap", key=f"pay_button_{hesap['id']}"):
                        success = pay_acik_hesap(hesap['id'], payment, payment_type)
                        if success:
                            st.success(f"💰 {payment} {birim_simgesi} ödeme başarıyla yapıldı.")
                            st.rerun()

            if st.button("🗑️ Hesabı Sil", key=f"delete_button_{hesap['id']}"):
                delete_acik_hesap(hesap['id'])
                st.warning("❌ Hesap silindi.")
                st.rerun()
