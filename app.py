from flask import Flask, render_template, request, jsonify
from db import get_db_connection
from decimal import Decimal, InvalidOperation
import secrets
from flask_wtf.csrf import CSRFProtect
from flask import session, redirect, url_for, flash
from werkzeug.security import check_password_hash
from functools import wraps

app = Flask(__name__)

import os

app.config["SECRET_KEY"] = os.environ.get(
    "BREWCAFE_SECRET_KEY",
    "dev-only-change-this-key"
)

csrf = CSRFProtect(app)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/menu")
def menu():
    return render_template("menu.html")


@app.route("/cart")
def cart():
    return render_template("cart.html")


@app.route("/order")
def order():
    return render_template("order.html")


@app.route("/order-success")
def order_success():
    reference = request.args.get("reference", "").strip()

    if not reference:
        return "Order reference is missing.", 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, order_reference, customer_name, phone,
                   address, total_amount, order_status, created_at
            FROM orders
            WHERE order_reference = %s
            """,
            (reference,)
        )

        order = cursor.fetchone()

        if not order:
            return "Order not found.", 404

        cursor.execute(
            """
            SELECT item_name, price, quantity, subtotal
            FROM order_items
            WHERE order_id = %s
            """,
            (order["id"],)
        )

        items = cursor.fetchall()

        return render_template(
            "order_success.html",
            order=order,
            items=items
        )

    except Exception:
        app.logger.exception("Unable to retrieve order confirmation")
        return "Unable to load your order. Please try again.", 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


@app.route("/place-order", methods=["POST"])
def place_order():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid order data."}), 400

    customer = data.get("customer")
    items = data.get("items")

    if not isinstance(customer, dict) or not isinstance(items, list) or not items:
        return jsonify({"error": "Customer details and cart items are required."}), 400

    name = customer.get("name")
    phone = customer.get("phone")
    address = customer.get("address")

    if not all(isinstance(value, str) and value.strip()
               for value in (name, phone, address)):
        return jsonify({"error": "Please complete all customer details."}), 400

    name = name.strip()
    phone = phone.strip()
    address = address.strip()

    if len(name) > 100 or len(phone) > 15 or len(address) > 500:
        return jsonify({"error": "One or more fields are too long."}), 400

    # These prices are determined by the server, not trusted from the browser.
    menu_prices = {
        "Cappuccino": Decimal("120.00"),
        "Latte": Decimal("130.00"),
        "Americano": Decimal("100.00"),
        "Masala Tea": Decimal("50.00"),
        "Iced Coffee": Decimal("140.00"),
        "Butter Croissant": Decimal("90.00"),
        "Veg Sandwich": Decimal("110.00"),
        "Chocolate Cake": Decimal("160.00")
    }

    validated_items = []
    total = Decimal("0.00")

    for item in items:
        if not isinstance(item, dict):
            return jsonify({"error": "Invalid cart item."}), 400

        item_name = item.get("name")
        quantity = item.get("quantity")

        if item_name not in menu_prices:
            return jsonify({"error": "An item in your cart is unavailable."}), 400

        # Do not accept prices or totals submitted by the browser.
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            return jsonify({"error": "Invalid item quantity."}), 400

        if quantity < 1 or quantity > 50:
            return jsonify({"error": "Item quantity must be between 1 and 50."}), 400

        price = menu_prices[item_name]
        subtotal = price * quantity
        total += subtotal

        validated_items.append({
            "name": item_name,
            "price": price,
            "quantity": quantity,
            "subtotal": subtotal
        })

    connection = None
    cursor = None

    # The reference uses random characters to reduce collisions.
    order_reference = "BC-" + secrets.token_hex(5).upper()

    try:
        connection = get_db_connection()
        connection.start_transaction()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO orders
                (order_reference, customer_name, phone, address,
                 total_amount, order_status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                order_reference,
                name,
                phone,
                address,
                total,
                "Pending"
            )
        )

        order_id = cursor.lastrowid

        for item in validated_items:
            cursor.execute(
                """
                INSERT INTO order_items
                    (order_id, item_name, price, quantity, subtotal)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    item["name"],
                    item["price"],
                    item["quantity"],
                    item["subtotal"]
                )
            )

        connection.commit()

        return jsonify({
            "message": "Order placed successfully!",
            "order_reference": order_reference,
            "total": str(total)
        }), 201

    except Exception:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Failed to save Brew Café order")

        return jsonify({
            "error": "We couldn't save your order. Please try again."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()
        
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, username, password_hash
                FROM admins
                WHERE username = %s
                """,
                (username,)
            )

            admin = cursor.fetchone()

            if admin and check_password_hash(
                admin["password_hash"], password
            ):
                session.clear()
                session["admin_id"] = admin["id"]
                session["admin_username"] = admin["username"]

                return redirect(url_for("admin_dashboard"))

            flash("Invalid username or password.")

        except Exception:
            app.logger.exception("Admin login failed")
            flash("Unable to log in right now. Please try again.")

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    return render_template("admin.html")

def admin_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("admin_login"))

        return view_function(*args, **kwargs)

    return wrapped_view


@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    connection = None
    cursor = None

    search_term = request.args.get("q", "").strip()[:100]

    stats = {
        "total_orders": 0,
        "pending_orders": 0,
        "preparing_orders": 0,
        "completed_orders": 0,
        "total_sales": 0
    }

    orders = []
    dashboard_error = False

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # 1. Total orders
        cursor.execute("SELECT COUNT(*) AS total FROM orders")
        stats["total_orders"] = cursor.fetchone()["total"]

        # 2. Pending orders
        cursor.execute(
            "SELECT COUNT(*) AS total FROM orders WHERE order_status = %s",
            ("Pending",)
        )
        stats["pending_orders"] = cursor.fetchone()["total"]

        # 3. Preparing orders
        cursor.execute(
            "SELECT COUNT(*) AS total FROM orders WHERE order_status = %s",
            ("Preparing",)
        )
        stats["preparing_orders"] = cursor.fetchone()["total"]

        # 4. Completed orders
        cursor.execute(
            "SELECT COUNT(*) AS total FROM orders WHERE order_status = %s",
            ("Completed",)
        )
        stats["completed_orders"] = cursor.fetchone()["total"]

        # 5. Sales from completed orders only
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) AS sales
            FROM orders
            WHERE order_status = %s
        """, ("Completed",))

        stats["total_sales"] = cursor.fetchone()["sales"]

        # 6. Fetch recent orders with their item names
        search_pattern = f"%{search_term}%"

        cursor.execute("""
            SELECT
                o.id,
                o.order_reference,
                o.customer_name,
                o.phone,
                o.total_amount,
                o.order_status,
                o.created_at,
                GROUP_CONCAT(
                    CONCAT(oi.item_name, ' × ', oi.quantity)
                    ORDER BY oi.id
                    SEPARATOR ', '
                ) AS items
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE (
                %s = ''
                OR o.order_reference LIKE %s
                OR o.customer_name LIKE %s
            )
            GROUP BY
                o.id,
                o.order_reference,
                o.customer_name,
                o.phone,
                o.total_amount,
                o.order_status,
                o.created_at
            ORDER BY o.created_at DESC
            LIMIT 100
        """, (search_term, search_pattern, search_pattern))

        orders = cursor.fetchall()

    except Exception:
        app.logger.exception("Unable to load admin dashboard")
        dashboard_error = True

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        orders=orders,
        search_term=search_term,
        dashboard_error=dashboard_error
    )
    
@app.route("/admin-order-status/<int:order_id>", methods=["POST"])
@admin_required
def admin_order_status(order_id):
    new_status = request.form.get("status", "")
    search_term = request.form.get("q", "").strip()[:100]

    allowed_statuses = {"Pending", "Preparing", "Completed"}

    if new_status not in allowed_statuses:
        flash("Invalid order status.")
        return redirect(
            url_for("admin_dashboard", q=search_term)
        )

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE orders
            SET order_status = %s
            WHERE id = %s
            """,
            (new_status, order_id)
        )

        connection.commit()

        if cursor.rowcount:
            flash("Order status updated successfully!")
        else:
            flash("Order not found or its status was unchanged.")

    except Exception:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Unable to update order status")
        flash("Unable to update the order status. Please try again.")

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(
        url_for("admin_dashboard", q=search_term)
    )

@app.route("/admin-logout", methods=["GET", "POST"])
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)