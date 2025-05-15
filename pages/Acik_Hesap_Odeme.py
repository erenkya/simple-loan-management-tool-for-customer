import streamlit as st
from DatabaseConnector.mysqlConnector import get_all_acik_hesap, pay_acik_hesap, delete_acik_hesap

st.set_page_config(page_title="Açık Hesap Ödeme", page_icon="💸", layout="wide")
st.title("💼 Açık Hesaplar")
st.write("Açık hesaplara borç ödeme yapabilir veya hesabı silebilirsiniz.")

acik_hesaplar = get_all_acik_hesap()

if not acik_hesaplar:
    st.info("🔎 Henüz açık hesap yok.")
else:
    for hesap in acik_hesaplar:
        with st.container():
            st.subheader(f"👤 {hesap['name']} - {hesap['number']}")
            st.markdown(f"""
            - 📦 Ürünler: `{hesap['products']}`
            - 💰 Başlangıç Tutarı: `{hesap['start_price']} ₺`
            - 🔻 Kalan Borç: `{hesap['remaining_price']} ₺`
            - 🕒 Oluşturulma: `{hesap['created_at']}`
            """)

            col1, col2, col3 = st.columns([1.5, 1.5, 1])

            if hesap['remaining_price'] == 0:
                col1.success("✅ Borç tamamen ödenmiş.")
            else:
                with col1:
                    payment = st.number_input(
                        "💵 Ödeme Tutarı", 
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
                            st.success("💰 Ödeme başarıyla yapıldı.")
                            st.rerun()

            if st.button("🗑️ Hesabı Sil", key=f"delete_button_{hesap['id']}"):
                delete_acik_hesap(hesap['id'])
                st.warning("❌ Hesap silindi.")
                st.rerun()
