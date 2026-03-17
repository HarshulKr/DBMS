# =========================
# IMPORTS + DB CONNECTION
# =========================
import mysql.connector
import random   # ✅ FIXED

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="harshul",
    database="minito_db"
)

cursor = conn.cursor(dictionary=True)

# =========================
# GLOBALS
# =========================
cart = []

# =========================
# PRODUCT FUNCTIONS
# =========================
def search_products(keyword):
    query = """
        SELECT ProductID, ProductName, Brand, Price, Quantity
        FROM Product
        WHERE ProductName LIKE %s OR Brand LIKE %s
    """
    cursor.execute(query, (f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()

    print("\n--- Search Results ---")
    for row in results:
        print(row)


def add_to_cart(product_id, qty):
    cart.append({"product_id": product_id, "qty": qty})
    print("✅ Added to cart")


# =========================
# ORDER FUNCTIONS
# =========================
def checkout(customer_id):
    try:
        total = 0   # ❌ removed start_transaction()

        for item in cart:
            cursor.execute(
                "SELECT Price FROM Product WHERE ProductID=%s",
                (item['product_id'],)
            )
            price = cursor.fetchone()['Price']
            total += price * item['qty']

        store_id = random.randint(1, 10)
        delivery_partner_id = random.randint(1, 10)

        # ✅ FIXED column names
        cursor.execute("""
            INSERT INTO Orders 
            (OrderDateTime, OrderStatus, TotalBillAmount, CustomerID, StoreID, DeliveryPartnerID)
            VALUES (NOW(), 'Placed', %s, %s, %s, %s)
        """, (total, customer_id, store_id, delivery_partner_id))

        order_id = cursor.lastrowid

        # 🔥 THIS triggers stock reduction automatically
        for item in cart:
            cursor.execute("""
                INSERT INTO OrderItem (OrderID, ProductID, QuantityOrdered)
                VALUES (%s, %s, %s)
            """, (order_id, item['product_id'], item['qty']))

        conn.commit()
        cart.clear()

        print(f"✅ Order placed successfully! Order ID: {order_id}")

    except Exception as e:
        conn.rollback()
        print("❌ Error:", e)


def cancel_order(order_id):
    try:
        cursor.execute("SELECT OrderStatus FROM Orders WHERE OrderID=%s", (order_id,))
        result = cursor.fetchone()

        if not result:
            raise Exception("Order not found")

        if result['OrderStatus'] == 'Delivered':
            raise Exception("Cannot cancel delivered order")

        # Update order status
        cursor.execute("""
            UPDATE Orders
            SET OrderStatus = 'Cancelled'
            WHERE OrderID = %s
        """, (order_id,))

        # Restore stock (manual — correct)
        cursor.execute("""
            SELECT ProductID, QuantityOrdered
            FROM OrderItem
            WHERE OrderID = %s
        """, (order_id,))

        items = cursor.fetchall()

        for item in items:
            cursor.execute("""
                UPDATE Product
                SET Quantity = Quantity + %s
                WHERE ProductID = %s
            """, (item['QuantityOrdered'], item['ProductID']))

        conn.commit()
        print("✅ Order cancelled successfully")

    except Exception as e:
        conn.rollback()
        print("❌ Error:", e)


# =========================
# USER / ANALYTICS
# =========================
def get_order_history(customer_id):
    cursor.execute("""
        SELECT OrderID, OrderDateTime, OrderStatus, TotalBillAmount
        FROM Orders
        WHERE CustomerID = %s
        ORDER BY OrderDateTime DESC
    """, (customer_id,))

    orders = cursor.fetchall()

    print("\n--- Order History ---")
    for order in orders:
        print(order)


# 🔥 FIXED USING JOIN
def get_delivery_partner(order_id):
    cursor.execute("""
        SELECT dp.PartnerID, dp.Name, dp.PhoneNumber, dp.VehicleDetails
        FROM Orders o
        JOIN DeliveryPartner dp ON o.DeliveryPartnerID = dp.PartnerID
        WHERE o.OrderID = %s
    """, (order_id,))

    result = cursor.fetchone()

    if result:
        print("\n--- Delivery Partner ---")
        print(result)
    else:
        print("❌ Partner not found")


# =========================
# MAIN MENU
# =========================
def menu():
    while True:
        print("\n========= MENU =========")
        print("1. Search Products")
        print("2. Add to Cart")
        print("3. Checkout")
        print("4. Cancel Order")
        print("5. View Order History")
        print("6. Delivery Partner Info")
        print("7. Exit")

        choice = input("Enter choice: ")

        if choice == '1':
            keyword = input("Enter keyword: ")
            search_products(keyword)

        elif choice == '2':
            pid = int(input("Product ID: "))
            qty = int(input("Quantity: "))
            add_to_cart(pid, qty)

        elif choice == '3':
            cid = int(input("Customer ID: "))
            checkout(cid)

        elif choice == '4':
            oid = int(input("Order ID: "))
            cancel_order(oid)

        elif choice == '5':
            cid = int(input("Customer ID: "))
            get_order_history(cid)

        elif choice == '6':
            oid = int(input("Order ID: "))
            get_delivery_partner(oid)

        elif choice == '7':
            print("Exiting...")
            break

        else:
            print("Invalid choice")


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    menu()
