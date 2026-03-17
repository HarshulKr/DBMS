import mysql.connector
import random

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="harshul",
    database="minito_db"
)

cursor = conn.cursor(dictionary=True)

# =========================
# SAFE INPUT
# =========================
def safe_int(prompt):
    try:
        return int(input(prompt))
    except:
        print("❌ Invalid input")
        return None

# =========================
# LOGIN
# =========================
def login():
    while True:
        email = input("Enter email (or exit): ")

        if email.lower() == "exit":
            return None

        cursor.execute("SELECT CustomerID, Name FROM Customer WHERE Email=%s", (email,))
        user = cursor.fetchone()

        if user:
            print(f"✅ Welcome {user['Name']}")
            return user['CustomerID']
        else:
            print("❌ User not found")

# =========================
# SHOW PRODUCTS
# =========================
def show_products():
    cursor.execute("""
        SELECT ProductID, ProductName, Price, Quantity
        FROM Product
        ORDER BY RAND()
        LIMIT 15
    """)

    for p in cursor.fetchall():
        print(f"{p['ProductID']} | {p['ProductName']} | ₹{p['Price']} | Stock: {p['Quantity']}")

# =========================
# ADD TO CART (DB)
# =========================
def add_to_cart(user):
    show_products()

    pid = safe_int("Product ID: ")
    qty = safe_int("Quantity: ")

    if not pid or not qty:
        return

    cursor.execute("""
        INSERT INTO Cart (CustomerID, ProductID, Quantity)
        VALUES (%s, %s, %s)
    """, (user, pid, qty))

    conn.commit()
    print("✅ Added to cart")

# =========================
# VIEW CART
# =========================
def view_cart(user):
    cursor.execute("""
        SELECT c.ProductID, p.ProductName, c.Quantity
        FROM Cart c
        JOIN Product p ON c.ProductID = p.ProductID
        WHERE c.CustomerID = %s
    """, (user,))

    items = cursor.fetchall()

    if not items:
        print("❌ Cart empty")
        return []

    print("\n--- Your Cart ---")
    for i, item in enumerate(items, 1):
        print(f"{i}. {item['ProductName']} x{item['Quantity']}")

    return items

# =========================
# CHECKOUT
# =========================
def checkout(user):
    try:
        cursor.execute("""
            SELECT c.ProductID, c.Quantity, p.Price
            FROM Cart c
            JOIN Product p ON c.ProductID = p.ProductID
            WHERE c.CustomerID = %s
        """, (user,))

        items = cursor.fetchall()

        if not items:
            print("❌ Cart empty")
            return

        total = sum(i['Quantity'] * i['Price'] for i in items)

        store_id = random.randint(1, 10)
        partner_id = random.randint(1, 10)

        cursor.execute("""
            INSERT INTO Orders 
            (OrderDateTime, OrderStatus, TotalBillAmount, CustomerID, StoreID, DeliveryPartnerID)
            VALUES (NOW(), 'Placed', %s, %s, %s, %s)
        """, (total, user, store_id, partner_id))

        order_id = cursor.lastrowid

        for item in items:
            cursor.execute("""
                INSERT INTO OrderItem (OrderID, ProductID, QuantityOrdered)
                VALUES (%s, %s, %s)
            """, (order_id, item['ProductID'], item['Quantity']))

        # clear cart
        cursor.execute("DELETE FROM Cart WHERE CustomerID=%s", (user,))

        conn.commit()
        print(f"✅ Order placed! ID: {order_id}")

    except Exception as e:
        conn.rollback()
        print("❌ Error:", e)

# =========================
# SHOW ORDERS
# =========================
def show_orders(user):
    cursor.execute("""
        SELECT OrderID, OrderStatus, TotalBillAmount
        FROM Orders
        WHERE CustomerID = %s
    """, (user,))

    orders = cursor.fetchall()

    for i, o in enumerate(orders, 1):
        print(f"{i}. Order {o['OrderID']} | {o['OrderStatus']} | ₹{o['TotalBillAmount']}")

    return orders

# =========================
# CANCEL ORDER
# =========================
def cancel_order(user):
    orders = show_orders(user)
    if not orders:
        return

    choice = safe_int("Select order: ")
    if not choice or choice > len(orders):
        return

    oid = orders[choice-1]['OrderID']

    cursor.execute("UPDATE Orders SET OrderStatus='Cancelled' WHERE OrderID=%s", (oid,))
    conn.commit()

    print("✅ Order cancelled")

# =========================
# ORDER HISTORY
# =========================
def order_history(user):
    cursor.execute("""
        SELECT o.OrderID, o.OrderStatus, p.ProductName, oi.QuantityOrdered
        FROM Orders o
        JOIN OrderItem oi ON o.OrderID = oi.OrderID
        JOIN Product p ON oi.ProductID = p.ProductID
        WHERE o.CustomerID = %s
        ORDER BY o.OrderID DESC
    """, (user,))

    rows = cursor.fetchall()

    current = None
    for r in rows:
        if current != r['OrderID']:
            current = r['OrderID']
            print(f"\nOrder {r['OrderID']} ({r['OrderStatus']})")

        print(f"  - {r['ProductName']} x{r['QuantityOrdered']}")

# =========================
# MENU
# =========================
def menu(user):
    while True:
        print("\n1.View Products\n2.Add to Cart\n3.View Cart\n4.Checkout\n5.Cancel Order\n6.Order History\n7.Exit")

        choice = safe_int("Choice: ")

        if choice == 1:
            show_products()
        elif choice == 2:
            add_to_cart(user)
        elif choice == 3:
            view_cart(user)
        elif choice == 4:
            checkout(user)
        elif choice == 5:
            cancel_order(user)
        elif choice == 6:
            order_history(user)
        elif choice == 7:
            break
        else:
            print("❌ Invalid")

# =========================
# RUN
# =========================
user = login()
if user:
    menu(user)
