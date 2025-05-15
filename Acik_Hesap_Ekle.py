import streamlit as st
import DatabaseConnector.mysqlConnector as db
from collections import Counter

st.set_page_config(page_title="Açık Hesap Yönetim Sistemi", page_icon=":guardsman:", layout="wide", initial_sidebar_state="expanded")

if "barcodes_list" not in st.session_state:
    st.session_state.barcodes_list = []
if "selected_products" not in st.session_state:
    st.session_state.selected_products = []
if "total_price" not in st.session_state:
    st.session_state.total_price = 0.0
if "discount_percent" not in st.session_state:
    st.session_state.discount_percent = 0.0

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.title("➕ Açık Hesap Ekle")

    name = st.text_input("👤 Müşteri İsmi", placeholder="Örn: Ahmet Yılmaz (Zorunlu)")
    number = st.text_input("📞 Telefon Numarası", placeholder="Örn: 0555 123 4567 (Zorunlu)")

    def add_barcode(barcode_input):
        if barcode_input.strip():
            st.session_state.barcodes_list.append(barcode_input.strip())
            st.rerun()
        else:
            st.warning("❗ Barkod alanı boş bırakılamaz.")

    with st.form(key="barcode_form", clear_on_submit=True):
        barcode_input = st.text_input("📦 Barkod Giriniz", placeholder="Örn: 3348901250146", key="barcode_input_key")
        submitted = st.form_submit_button("➕ Ekle")
        if submitted:
            add_barcode(barcode_input)

    st.write("📋 Girilen Barkodlar:")
    for i, bc in enumerate(st.session_state.barcodes_list):
        col1_, col2_ = st.columns([8, 1])
        with col1_:
            st.write(f"{i+1}. {bc}")
        with col2_:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.barcodes_list.pop(i)
                st.rerun()

    if st.button("🧹 Tüm Barkodları Temizle"):
        st.session_state.barcodes_list = []
        st.rerun()

    if st.button("🔍 Ürünleri Ekle"):
        st.session_state.selected_products = []
        st.session_state.total_price = 0.0

        if not st.session_state.barcodes_list:
            st.warning("❗ En az bir barkod eklemelisiniz.")
        else:
            for barcode in st.session_state.barcodes_list:
                product = db.get_product_name_and_price_by_barcode(barcode)
                if product:
                    st.session_state.selected_products.append({
                        "name": product['name'],
                        "price": float(product['price']),
                        "barcode": barcode
                    })
                    st.session_state.total_price += float(product['price'])
                else:
                    st.warning(f"❗ Barkod ile ürün bulunamadı: {barcode}")

    # İndirim yüzdesi inputu
    discount_percent_str = st.text_input("🤑 İndirim Yüzdesi (%)", value=str(st.session_state.discount_percent), help="0 ile 100 arasında bir sayı girin")
    try:
        discount_percent = float(discount_percent_str)
        if discount_percent < 0 or discount_percent > 100:
            st.warning("❗ İndirim yüzdesi 0 ile 100 arasında olmalı.")
            discount_percent = 0.0
    except:
        st.warning("❗ İndirim yüzdesi geçerli bir sayı olmalı.")
        discount_percent = 0.0
    st.session_state.discount_percent = discount_percent

    if st.session_state.selected_products:
        st.subheader("🧾 Eklenen Ürünler (Barkod tekrar sayısına göre):")

        barcode_counts = Counter([p['barcode'] for p in st.session_state.selected_products])

        product_display_list = []
        total_price_after_discount = 0.0

        for barcode, count in barcode_counts.items():
            product = next(p for p in st.session_state.selected_products if p['barcode'] == barcode)
            original_price = product['price']
            discounted_price = original_price * (1 - discount_percent / 100)
            total_line_price = discounted_price * count
            total_price_after_discount += total_line_price
            product_display_list.append(
                f"{count} x {product['name']} (Barkod: {barcode}) - "
                f"Fiyat: {original_price:.2f}₺, İndirimli: {discounted_price:.2f}₺"
            )

        updated_selection = st.multiselect("Ürünleri seçip çıkarabilirsiniz:", options=product_display_list, default=product_display_list)

        removed_barcodes = []
        for display_str in product_display_list:
            if display_str not in updated_selection:
                bc_start = display_str.find("Barkod: ") + len("Barkod: ")
                bc = display_str[bc_start:bc_start+13]  # Barkod uzunluğuna göre kes (örn 13 karakter)
                removed_barcodes.append(bc)

        if removed_barcodes:
            new_selected_products = []
            for p in st.session_state.selected_products:
                if p['barcode'] not in removed_barcodes:
                    new_selected_products.append(p)
            st.session_state.selected_products = new_selected_products
            st.session_state.total_price = sum(p['price'] for p in new_selected_products)
            st.rerun()

        start_debt_default = f"{total_price_after_discount:.2f}" if total_price_after_discount else "0"
    else:
        start_debt_default = "0"

    start_debt_input = st.text_input("💰 Başlangıç Borcu", value=start_debt_default, placeholder="0")

    if st.button("💾 Kaydet"):
        try:
            start_debt_value = float(start_debt_input)
        except ValueError:
            st.error("❗ Lütfen geçerli bir sayısal başlangıç borcu girin.")
        else:
            if not name or not number:
                st.warning("❌ Lütfen müşteri ismi ve telefon numarasını girin.")
            elif not st.session_state.selected_products:
                st.warning("❌ En az bir ürün eklemelisiniz.")
            else:
                products_text = ", ".join([p['name'] for p in st.session_state.selected_products])
                success = db.insert_acik_hesap(name, number, products_text, start_debt_value, remaining_price=start_debt_value)
                if success:
                    for product in st.session_state.selected_products:
                        db.reduce_stock_quantity_by_barcode(product['barcode'], 1)
                    st.session_state.barcodes_list = []
                    st.session_state.selected_products = []
                    st.session_state.total_price = 0.0
                    st.session_state.discount_percent = 0.0
                    st.success("✅ Açık hesap başarıyla eklendi ve stoklar güncellendi!")
                    st.rerun()
                else:
                    st.error("❌ Kayıt sırasında bir hata oluştu.")
