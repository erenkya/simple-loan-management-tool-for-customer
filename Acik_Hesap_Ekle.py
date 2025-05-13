import streamlit as st
import DatabaseConnector.mysqlConnector as db

st.set_page_config(page_title="Açık Hesap Yönetim Sistemi", page_icon=":guardsman:", layout="wide", initial_sidebar_state="expanded")

# Session state init
if "selected_products" not in st.session_state:
    st.session_state.selected_products = []
if "total_price" not in st.session_state:
    st.session_state.total_price = 0.0
if "input_key1" not in st.session_state:
    st.session_state.input_key1 = 1
if "input_key2" not in st.session_state:
    st.session_state.input_key2 = 2
if "input_key3" not in st.session_state:
    st.session_state.input_key3 = 3

def update_input_key():
    st.session_state.input_key1 += 3
    st.session_state.input_key2 += 3
    st.session_state.input_key3 += 3

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.title("➕ Açık Hesap Ekle")

    name = st.text_input("👤 Müşteri İsmi", placeholder="Örn: Ahmet Yılmaz (Zorunlu)", key=st.session_state.input_key1)
    number = st.text_input("📞 Telefon Numarası", placeholder="Örn: 0555 123 4567 (Zorunlu)", key=st.session_state.input_key2)
    barcode = st.text_input("📦 Barkod Giriniz",placeholder="Örn: 3348901250146", key=st.session_state.input_key3)

    quantity = st.number_input("🔢 Adet", min_value=1, step=1)

    if st.button("🔍 Ürün Ekle"):
        if barcode:
            product = db.get_product_name_and_price_by_barcode(barcode)
            if product:
                if quantity > product['stock_quantity']:
                    st.warning(f"🚫 Stokta yalnızca {product['stock_quantity']} adet var!")
                else:
                    already_added = any(p['barcode'] == barcode for p in st.session_state.selected_products)
                    if not already_added:
                        total_price_for_product = float(product['price']) * quantity
                        st.session_state.selected_products.append({
                            "name": product['name'],
                            "price": float(product['price']),
                            "quantity": quantity,
                            "barcode": barcode
                        })
                        st.session_state.total_price += total_price_for_product
                        st.success(f"✅ {quantity} x {product['name']} eklendi! Toplam: {st.session_state.total_price:.2f}₺")
                    else:
                        st.info("ℹ️ Bu ürün zaten eklendi. Lütfen ürünü silip tekrar ekleyin.")
            else:
                st.warning("❗ Bu barkodla eşleşen ürün bulunamadı.")
        else:
            st.warning("❗ Barkod alanı boş bırakılamaz.")

    # Listeleme
    selected_names = [f"{p['quantity']} x {p['name']}" for p in st.session_state.selected_products]
    name_only = [p['name'] for p in st.session_state.selected_products]

    updated_selection = st.multiselect("🧾 Eklenen Ürünler", options=selected_names, default=selected_names)

    removed_names = []
    for old_display, name in zip(selected_names, name_only):
        if old_display not in updated_selection:
            removed_names.append(name)

    for removed_name in removed_names:
        removed_product = next(p for p in st.session_state.selected_products if p['name'] == removed_name)
        st.session_state.total_price -= removed_product['price'] * removed_product['quantity']

    st.session_state.selected_products = [
        p for p in st.session_state.selected_products if f"{p['quantity']} x {p['name']}" in updated_selection
    ]

    # Başlangıç borcunu al
    start_debt_input = st.text_input("💰 Başlangıç Borcu", value=f"{st.session_state.total_price:.2f}", placeholder=0 ,disabled=False)

    products_text = ", ".join([f"{p['quantity']}x {p['name']}" for p in st.session_state.selected_products])

    if st.button("💾 Kaydet"):
        # Sayısal kontrol
        try:
            start_debt_value = float(start_debt_input)
        except ValueError:
            st.error("❗ Lütfen geçerli bir sayısal başlangıç borcu girin.")
        else:
            if name and number :
                success = db.insert_acik_hesap(name, number, products_text, start_debt_value, remaining_price=start_debt_value)
                if success:
                    # Stokları düşür
                    for product in st.session_state.selected_products:
                        db.reduce_stock_quantity_by_barcode(product['barcode'], product['quantity'])

                    # Temizle
                    st.session_state.selected_products = []
                    st.session_state.total_price = 0.0
                    update_input_key()
                    st.success("✅ Açık hesap başarıyla eklendi ve stoklar güncellendi!")
                    st.rerun()
                else:
                    st.error("❌ Kayıt sırasında bir hata oluştu.")
            else:
                st.warning("❌ Gerekli tüm boşlukları doldurduğunuzdan emin olun.")
