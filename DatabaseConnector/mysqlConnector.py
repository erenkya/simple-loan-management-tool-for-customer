import pymysql
import streamlit as st
import json
from collections import Counter
from datetime import datetime

config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'StockManagement',
    'cursorclass': pymysql.cursors.DictCursor
}

def connect_to_database():
    try:
        connection = pymysql.connect(**config)
        return connection
    except pymysql.MySQLError as e:
        st.error(f"🔌 Veritabanına bağlanırken hata oluştu: {e}")
        return None

def insert_acik_hesap(name, number, products, start_price, remaining_price, kur="TRY"):
    conn = connect_to_database()
    cursor = conn.cursor()
    try:
        sql = """
            INSERT INTO acik_hesap (name, number, products, start_price, remaining_price, kur)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (name, number, products, start_price, remaining_price, kur))
        conn.commit()
        return True
    except Exception as e:
        print("DB Error:", e)
        return False
    finally:
        cursor.close()
        conn.close()
def get_product_name_and_price_by_barcode(barcode):
    connection = connect_to_database()
    if connection is None:
        return None

    try:
        with connection.cursor() as cursor:
            sql = "SELECT name, price, stock_quantity  FROM products WHERE barcode = %s"
            cursor.execute(sql, (barcode,))
            result = cursor.fetchone()
            return result
    except pymysql.MySQLError as e:
        st.error(f"🧨 Ürün bilgisi alınırken hata oluştu: {e}")
        return None
    finally:
        connection.close()

def reduce_stock_quantity_by_barcode(barcode, quantity):
    connection = connect_to_database()
    if connection is None:
        return False

    try:
        with connection.cursor() as cursor:
            sql = """
            UPDATE products
            SET stock_quantity = stock_quantity - %s
            WHERE barcode = %s AND stock_quantity >= %s
            """
            cursor.execute(sql, (quantity, barcode, quantity))
            connection.commit()

            if cursor.rowcount == 0:
                st.warning("🚫 Yetersiz stok veya barkod bulunamadı.")
                return False

            return True
    except pymysql.MySQLError as e:
        st.error(f"📉 Stok güncellenirken hata oluştu: {e}")
        return False
    finally:
        connection.close()

def get_all_acik_hesap():
    connection = connect_to_database()
    if connection is None:
        return None

    try:
        with connection.cursor() as cursor:
            sql = "SELECT id, name, number, products, start_price, remaining_price, kur, created_at FROM acik_hesap"
            cursor.execute(sql)
            result = cursor.fetchall()  # Tüm kayıtları al
            return result
    except pymysql.MySQLError as e:
        st.error(f"🧨 Veriler alınırken hata oluştu: {e}")
        return None
    finally:
        connection.close()
#--------------------------------------------------------------------------------------------------------------------------------------
def pay_acik_hesap(hesap_id, payment_amount, payment_type):
    connection = connect_to_database()
    if connection is None:
        return False

    try:
        with connection.cursor() as cursor:
            # Önce mevcut remaining_price ve start_price alınır
            cursor.execute("SELECT remaining_price, start_price, kur FROM acik_hesap WHERE id = %s", (hesap_id,))
            hesap = cursor.fetchone()
            if not hesap:
                st.warning("Hesap bulunamadı.")
                return False

            remaining_price = hesap["remaining_price"]
            start_price = hesap["start_price"]

            if payment_amount > remaining_price:
                st.warning("🧾 Ödeme tutarı kalan borçtan fazla olamaz.")
                return False

            new_remaining = remaining_price - payment_amount

            # Güncelleme ve ödeme kaydı
            cursor.execute("UPDATE acik_hesap SET remaining_price = %s WHERE id = %s", (new_remaining, hesap_id))
            cursor.execute("""
                INSERT INTO acik_hesap_odeme (hesap_id, payment, payment_type, start_price, remaining_price, kur)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (hesap_id, payment_amount, payment_type, start_price, new_remaining, hesap['kur']))

            connection.commit()
            st.success("💸 Ödeme başarıyla kaydedildi.")
            return True
    except pymysql.MySQLError as e:
        st.error(f"💥 Ödeme yapılırken hata oluştu: {e}")
        return False
    finally:
        connection.close()

def delete_acik_hesap(hesap_id):
    connection = connect_to_database()
    if connection is None:
        return False

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM acik_hesap WHERE id = %s", (hesap_id,))
            connection.commit()
            st.success("🗑️ Açık hesap silindi.")
            return True
    except pymysql.MySQLError as e:
        st.error(f"❌ Silme işlemi sırasında hata oluştu: {e}")
        return False
    finally:
        connection.close()


def get_all_acik_hesap_odemeleri():
    connection = connect_to_database()
    if connection is None:
        return []

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT o.hesap_id, o.payment, o.kur ,o.payment_type, o.created_at,  
                       h.name AS customer_name, h.number AS customer_number
                FROM acik_hesap_odeme o
                JOIN acik_hesap h ON o.hesap_id = h.id
                ORDER BY o.created_at DESC
            """)
            return cursor.fetchall()
    except pymysql.MySQLError as e:
        st.error(f"📥 Ödeme verileri alınırken hata oluştu: {e}")
        return []
    finally:
        connection.close()


def insert_sales_from_acik_hesap_products(products_json_string, type_of_sale="Açık Hesap", user_id=1):
    connection = connect_to_database()
    if connection is None:
        return False

    try:
        products = json.loads(products_json_string)  # JSON string'i listeye çeviriyoruz

        with connection.cursor() as cursor:
            for product in products:
                barcode = product["barcode"]
                quantity = product["quantity"]
                price = product["price"]
                gain = product.get("gain", 0.0)

                # Önce barcode'dan product_id alalım
                cursor.execute("SELECT product_id FROM products WHERE barcode = %s", (barcode,))
                result = cursor.fetchone()

                if not result:
                    st.warning(f"🚫 Barkod bulunamadı: {barcode}")
                    continue

                product_id = result["product_id"]
                total_price = quantity * price

                # sales tablosuna insert
                cursor.execute("""
                    INSERT INTO sales (product_id, quantity, total_price, gain, type_of_sale, user_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'COMPLETED')
                """, (product_id, quantity, total_price, gain, type_of_sale, user_id))

        connection.commit()
        st.success("📦 Tüm ürünler için satış kayıtları eklendi.")
        return True
    except Exception as e:
        st.error(f"💥 Satış kayıtları eklenirken hata oluştu: {e}")
        return False
    finally:
        connection.close()

def increase_acik_hesap_borc(hesap_id, ek_tutar):
    connection = connect_to_database()
    if connection is None:
        return False

    try:
        with connection.cursor() as cursor:
            # Mevcut değerleri al
            cursor.execute("SELECT remaining_price, start_price FROM acik_hesap WHERE id = %s", (hesap_id,))
            hesap = cursor.fetchone()

            if not hesap:
                st.warning("❌ Hesap bulunamadı.")
                return False

            new_remaining = hesap["remaining_price"] + ek_tutar
            new_start = hesap["start_price"] + ek_tutar

            # Güncelle
            cursor.execute("""
                UPDATE acik_hesap 
                SET remaining_price = %s, start_price = %s 
                WHERE id = %s
            """, (new_remaining, new_start, hesap_id))

            connection.commit()
            st.success("📈 Borç başarılı şekilde artırıldı.")
            return True
    except pymysql.MySQLError as e:
        st.error(f"⚠️ Borç artırılırken hata oluştu: {e}")
        return False
    finally:
        connection.close()
