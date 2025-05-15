import pymysql
import streamlit as st

config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'E1r2e3n4',
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


def insert_acik_hesap(name, number, products, start_price, remaining_price):
    connection = connect_to_database()
    if connection is None:
        return False

    try:
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO acik_hesap (name, number, products, start_price, remaining_price)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (name, number, products, start_price, remaining_price))
            connection.commit()
            st.success("✅ Açık hesap başarıyla eklendi.")
            return True
    except pymysql.MySQLError as e:
        st.error(f"🧨 Kayıt eklenirken hata oluştu: {e}")
        return False
    finally:
        connection.close()

def get_product_name_and_price_by_barcode(barcode):
    connection = connect_to_database()
    if connection is None:
        return None

    try:
        with connection.cursor() as cursor:
            sql = "SELECT name, price, stock_quantity FROM products WHERE barcode = %s"
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
            sql = "SELECT id, name, number, products, start_price, remaining_price, created_at FROM acik_hesap"
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
            cursor.execute("SELECT remaining_price, start_price FROM acik_hesap WHERE id = %s", (hesap_id,))
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
                INSERT INTO acik_hesap_odeme (hesap_id, payment, payment_type, start_price, remaining_price)
                VALUES (%s, %s, %s, %s, %s)
            """, (hesap_id, payment_amount, payment_type, start_price, new_remaining))

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




