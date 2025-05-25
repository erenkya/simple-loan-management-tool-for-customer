import streamlit as st
import json
import DatabaseConnector.mysqlConnector as db

st.set_page_config(
    page_title="Açık Hesaba Borç Ekle",
    page_icon="➕",
    layout="wide"
)

# Session state
if "selected_products" not in st.session_state:
    st.session_state.selected_products = []
if "barcodes_list" not in st.session_state:
    st.session_state.barcodes_list = []
if "discount_percent" not in st.session_state:
    st.session_state.discount_percent = 0.0

st.title("➕ Açık Hesaba Barkodla Borç Ekle")

# Hesap seçimi
acik_hesaplar = db.get_all_acik_hesap()

if not acik_hesaplar:
    st.warning("Açık hesap bulunamadı.")
    st.stop()

selected_hesap = st.selectbox(
    "👤 Borç Eklenecek Hesap",
    acik_hesaplar,
    format_func=lambda h: f"{h['name']} - {h['number']} (Borç: {h['remaining_price']} {h['kur']})"
)

selected_kur = selected_hesap["kur"]

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
            st.warning(f"❗ Ürün bulunamadı: {barcode_input}")
    else:
        st.warning("❗ Barkod boş bırakılamaz.")

with st.form(key="barcode_form", clear_on_submit=True):
    barcode_input = st.text_input("📦 Barkod", key="barcode_input_key")
    if st.form_submit_button("➕ Ürün Ekle"):
        add_barcode(barcode_input)

st.write("📋 Eklenen Ürünler:")
total_price = 0.0
updated_products = []

for i, product in enumerate(st.session_state.selected_products):
    col1, col2, col3 = st.columns([5, 2, 1])
    with col1:
        st.write(f"{i+1}. {product['name']} (Barkod: {product['barcode']})")
    with col2:
        new_price = st.text_input("Fiyat", value=f"{product['price']:.2f}", key=f"price_{i}")
        try:
            product["price"] = float(new_price)
        except ValueError:
            st.warning(f"{product['name']} için geçersiz fiyat girdiniz.")
    with col3:
        if st.button("❌", key=f"del_{i}"):
            del st.session_state.barcodes_list[i]
            del st.session_state.selected_products[i]
            st.rerun()
    updated_products.append(product)
    total_price += product["price"]

st.session_state.selected_products = updated_products

if st.button("🧹 Ürünleri Temizle"):
    st.session_state.barcodes_list = []
    st.session_state.selected_products = []
    st.rerun()

# İndirim yüzdesi
discount_percent_str = st.text_input("🤑 İndirim (%)", value=str(st.session_state.discount_percent))
try:
    discount_percent = float(discount_percent_str)
    if discount_percent < 0 or discount_percent > 100:
        st.warning("İndirim 0 ile 100 arasında olmalı.")
        discount_percent = 0.0
except:
    st.warning("Geçerli bir sayı girin.")
    discount_percent = 0.0

payment_type = st.selectbox(
    "💳 Ödeme Türü", 
    ["Nakit", "Kredi Kartı", "Havale", "Havale->E"],
)

st.session_state.discount_percent = discount_percent

discounted_total = total_price * (1 - discount_percent / 100)

# Manuel toplam girişi
custom_total_input = st.text_input(
    f"📝 Manuel Toplam ({selected_kur})", 
    value=f"{discounted_total:.2f}", 
    help="Eğer farklı bir toplam belirlemek istiyorsan buraya yazabilirsin."
)

try:
    final_total = float(custom_total_input)
except ValueError:
    st.warning("Geçerli bir toplam tutarı girin.")
    final_total = discounted_total

st.markdown(f"### 💰 Otomatik Hesaplanan Toplam: {total_price:.2f} {selected_kur} → İndirimli: {discounted_total:.2f} {selected_kur}")
st.markdown(f"### ✏️ Kullanılacak Toplam: {final_total:.2f} {selected_kur}")

# Kaydet
if st.button("💾 Borcu Ekle ve Kaydet"):
    if not st.session_state.selected_products:
        st.warning("Lütfen en az bir ürün ekleyin.")
    else:
        success = db.increase_acik_hesap_borc(selected_hesap["id"], final_total)
        if success:
            # Stok düş
            for product in st.session_state.selected_products:
                db.reduce_stock_quantity_by_barcode(product['barcode'], 1)

            # JSON yapısı
            json_data = json.dumps([
                {
                    "barcode": p["barcode"],
                    "quantity": 1,
                    "price": p["price"],
                    "gain": 0.0
                }
                for p in st.session_state.selected_products
            ])
            db.insert_sales_from_acik_hesap_products(json_data, type_of_sale=payment_type, user_id=1)

            st.success("✅ Borç başarıyla eklendi, stoklar güncellendi.")
            st.session_state.barcodes_list = []
            st.session_state.selected_products = []
            st.session_state.discount_percent = 0.0
            st.rerun()
        else:
            st.error("❌ Borç eklenemedi.")
