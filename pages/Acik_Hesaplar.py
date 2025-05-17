import streamlit as st
import pandas as pd
import io
import DatabaseConnector.mysqlConnector as db

st.set_page_config(page_title="Açık Hesaplar", page_icon="📊", layout="wide")

# Başlık
st.title("💳 Açık Hesaplar Tablosu")

# Verileri çek
acik_hesaplar = db.get_all_acik_hesap()

if acik_hesaplar:
    # Verileri DataFrame'e çevir
    df = pd.DataFrame(acik_hesaplar, columns=[
        'id', 'name', 'number', 'products',
        'start_price', 'remaining_price', 'kur', 'created_at'
    ])
    
    # Kolon adlarını Türkçeye çevir
    df.columns = [
        'ID', 'Müşteri Adı', 'Telefon Numarası', 'Ürünler',
        'Başlangıç Fiyatı', 'Kalan Ücret', 'Kur', 'Oluşturulma Tarihi'
    ]
    
    # Tarih formatını düzenle
    df['Oluşturulma Tarihi'] = pd.to_datetime(df['Oluşturulma Tarihi']).dt.strftime('%d-%m-%Y')

    # Filtreleme seçenekleri
    filter_option = st.selectbox("Filtreleme Seçeneği", ["Hepsi", "İsim", "Numara", "Tarih", "Kur"])

    if filter_option == "İsim":
        name_filter = st.text_input("Müşteri İsmi ile Filtrele")
        if name_filter:
            df = df[df['Müşteri Adı'].str.contains(name_filter, case=False, na=False)]
            if df.empty:
                st.warning("Bu isim ile eşleşen kayıt bulunmamaktadır.")

    elif filter_option == "Numara":
        number_filter = st.text_input("Telefon Numarası ile Filtrele")
        if number_filter:
            df = df[df['Telefon Numarası'].str.contains(number_filter, case=False, na=False)]
            if df.empty:
                st.warning("Bu numara ile eşleşen kayıt bulunmamaktadır.")

    elif filter_option == "Tarih":
        date_filter = st.date_input("Tarih Aralığı Seç", [])
        if len(date_filter) == 2:  # Başlangıç ve bitiş tarihi seçilmişse
            start_date = pd.to_datetime(date_filter[0])
            end_date = pd.to_datetime(date_filter[1])
            date_column = pd.to_datetime(df['Oluşturulma Tarihi'], format='%d-%m-%Y')
            df = df[(date_column >= start_date) & (date_column <= end_date)]
            if df.empty:
                st.warning("Bu tarihler arasında kayıt bulunmamaktadır.")

    elif filter_option == "Kur":
        currency_options = df['Kur'].dropna().unique().tolist()
        selected_currency = st.selectbox("Kur Seçiniz", ["Hepsi"] + sorted(currency_options))
        if selected_currency != "Hepsi":
            df = df[df['Kur'] == selected_currency]
            if df.empty:
                st.warning("Bu kura ait kayıt bulunmamaktadır.")

    # Görüntüleme
    st.dataframe(df, use_container_width=True)

    # Excel İndirme
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)

    st.download_button(
        label="📩 Excel Olarak İndir",
        data=excel_buffer,
        file_name="acik_hesaplar.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.warning("❌ Açık hesap verileri alınamadı.")
