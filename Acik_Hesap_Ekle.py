import streamlit as st
import json
import DatabaseConnector.mysqlConnector as db

st.set_page_config(
    page_title="Açık Hesap Yönetim Sistemi",
    page_icon=":guardsman:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# State initialization
if "barcodes_list" not in st.session_state:
    st.session_state.barcodes_list = []
if "selected_products" not in st.session_state:
    st.session_state.selected_products = []
if "discount_percent" not in st.session_state:
    st.session_state.discount_percent = 0.0

# Layout
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("➕ Açık Hesap Ekle")

    name = st.text_input("👤 Müşteri İsmi", placeholder="Örn: Ahmet Yılmaz (Zorunlu)")
    number = st.text_input("📞 Telefon Numarası", placeholder="Örn: 0555 123 4567 (Zorunlu)")

    kur_options = ["TRY", "USD", "EUR"]
    selected_kur = st.selectbox("💱 Para Birimi", kur_options, index=0)

    # Barkod ekleme
    def add_barcode(barcode_input):
        if barcode_input.strip():
            product = db.get_product_name_and_price_by_barcode(barcode_input.strip())
            if product:
                st.session_state.barcodes_list.append(barcode_input.strip())
                st.session_state.selected_products.append({
                    "name": product["name"],
                    "price": float(product["price"]),
                    "barcode": barcode_input.strip()
                })
                st.rerun()
            else:
                st.warning(f"❗ Barkod ile ürün bulunamadı: {barcode_input}")
        else:
            st.warning("❗ Barkod alanı boş bırakılamaz.")

    with st.form(key="barcode_form", clear_on_submit=True):
        barcode_input = st.text_input("📦 Barkod Giriniz", placeholder="Örn: 3348901250146", key="barcode_input_key")
        submitted = st.form_submit_button("➕ Ekle")
        if submitted:
            add_barcode(barcode_input)

    st.write("📋 Eklenen Ürünler:")
    total_price = 0.0
    updated_products = []

    for i, product in enumerate(st.session_state.selected_products):
        col1_, col2_, col3_ = st.columns([5, 2, 1])
        with col1_:
            st.write(f"{i+1}. {product['name']} (Barkod: {product['barcode']})")
        with col2_:
            new_price = st.text_input(f"Fiyat ({product['name']})", value=f"{product['price']:.2f}", key=f"price_input_{i}")
            try:
                product["price"] = float(new_price)
            except ValueError:
                st.warning(f"{product['name']} için geçersiz fiyat girdiniz.")
        with col3_:
            if st.button("❌", key=f"del_{i}"):
                del st.session_state.barcodes_list[i]
                del st.session_state.selected_products[i]
                st.rerun()

        updated_products.append(product)
        total_price += product["price"]

    st.session_state.selected_products = updated_products

    if st.button("🧹 Tüm Barkodları Temizle"):
        st.session_state.barcodes_list = []
        st.session_state.selected_products = []
        st.rerun()

    # İndirim yüzdesi
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

    discounted_total = total_price * (1 - discount_percent / 100)
    st.markdown(f"### 💵 Toplam Tutar: {total_price:.2f}₺ → İndirimli: {discounted_total:.2f}₺")

    start_debt_input = st.text_input("💰 Başlangıç Borcu", value=f"{discounted_total:.2f}", placeholder="0")

    # Alt Butonlar
    footercol1, footercol2 = st.columns([1, 1])
    with footercol1:
        if st.session_state.selected_products:
            if st.button("💾 Kaydet"):
                try:
                    start_debt_value = float(start_debt_input)
                except ValueError:
                    st.error("❗ Lütfen geçerli bir sayısal başlangıç borcu girin.")
                else:
                    if not name or not number:
                        st.warning("❌ Lütfen müşteri ismi ve telefon numarasını girin.")
                    else:
                        products_text = ", ".join([p['name'] for p in st.session_state.selected_products])
                        success = db.insert_acik_hesap(
                            name,
                            number,
                            products_text,
                            start_debt_value,
                            remaining_price=start_debt_value,
                            kur=selected_kur
                        )

                        if success:
                            # 1. Stokları düş
                            for product in st.session_state.selected_products:
                                db.reduce_stock_quantity_by_barcode(product['barcode'], 1)

                            # 2. JSON formatına uygun hale getir
                            products_for_sale = []
                            for product in st.session_state.selected_products:
                                products_for_sale.append({
                                    "barcode": product["barcode"],
                                    "quantity": 1,
                                    "price": product["price"],
                                    "gain": 0.0
                                })

                            # 3. JSON string olarak kaydet
                            json_string = json.dumps(products_for_sale)
                            db.insert_sales_from_acik_hesap_products(json_string, type_of_sale="Açık Hesap", user_id=1)

                            # 4. Temizle
                            st.session_state.barcodes_list = []
                            st.session_state.selected_products = []
                            st.session_state.discount_percent = 0.0

                            st.success("✅ Açık hesap başarıyla eklendi, stoklar düşüldü ve satışlar kaydedildi!")
                            st.rerun()
                        else:
                            st.error("❌ Kayıt sırasında bir hata oluştu.")
        else:
            st.warning("📦 Lütfen en az 1 ürün ekleyin.")

    with footercol2:
        if st.button("🔄 Sıfırla"):
            st.session_state.barcodes_list = []
            st.session_state.selected_products = []
            st.session_state.discount_percent = 0.0
            st.rerun()
