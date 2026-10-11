from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from uuid import uuid4
from database.connection import get_connection

CENT = Decimal("0.01")

def money(value):
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)

class BillingService:
    def __init__(self, tax_rate="0.05"):
        self.tax_rate = Decimal(str(tax_rate))

    def calculate(self, items, discount="0"):
        subtotal = money(sum(
            (Decimal(str(item["price"])) * int(item["quantity"]) for item in items),
            Decimal("0")
        ))
        discount = money(discount)
        if discount < 0 or discount > subtotal:
            raise ValueError("Discount must be between zero and subtotal.")
        if self.tax_rate < 0:
            raise ValueError("Tax rate cannot be negative.")
        tax = money((subtotal - discount) * self.tax_rate)
        return {
            "subtotal": subtotal,
            "discount": discount,
            "tax_rate": self.tax_rate,
            "tax": tax,
            "total": money(subtotal - discount + tax),
        }

    def create_order(self, order_type, table_number, cart, discount="0"):
        if order_type not in ("dine_in", "takeaway"):
            raise ValueError("Select a valid order type.")
        if order_type == "dine_in" and not str(table_number).strip():
            raise ValueError("Table number is required for dine-in orders.")
        if not cart:
            raise ValueError("Add at least one item to the order.")

        # Re-read current prices and availability inside the transaction.
        with get_connection() as conn:
            normalized = []
            for item_id, quantity in cart.items():
                if int(quantity) <= 0:
                    raise ValueError("Quantity must be positive.")
                row = conn.execute(
                    "SELECT id, name, price, is_available FROM menu_items WHERE id=?",
                    (item_id,),
                ).fetchone()
                if not row or not row["is_available"]:
                    raise ValueError("A selected menu item is unavailable.")
                normalized.append({
                    "id": row["id"], "name": row["name"],
                    "price": Decimal(str(row["price"])),
                    "quantity": int(quantity),
                })
            bill = self.calculate(normalized, discount)
            order_number = "ORD-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:4].upper()
            cursor = conn.execute("""
                INSERT INTO orders(
                    order_number, order_type, table_number, status,
                    subtotal, discount_amount, tax_rate, tax_amount, total_amount
                ) VALUES(?,?,?,?,?,?,?,?,?)
            """, (
                order_number, order_type,
                str(table_number).strip() if order_type == "dine_in" else None,
                "placed", str(bill["subtotal"]), str(bill["discount"]),
                str(bill["tax_rate"]), str(bill["tax"]), str(bill["total"]),
            ))
            order_id = cursor.lastrowid
            conn.executemany("""
                INSERT INTO order_items(
                    order_id, menu_item_id, item_name, unit_price, quantity, line_total
                ) VALUES(?,?,?,?,?,?)
            """, [
                (order_id, item["id"], item["name"], str(item["price"]),
                 item["quantity"], str(money(item["price"] * item["quantity"])))
                for item in normalized
            ])
            return {"id": order_id, "order_number": order_number, **bill}

    def record_payment(self, order_id, method, amount):
        if method not in ("cash", "upi", "card"):
            raise ValueError("Select a valid payment method.")
        amount = money(amount)
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        with get_connection() as conn:
            order = conn.execute(
                "SELECT total_amount, status FROM orders WHERE id=?", (order_id,)
            ).fetchone()
            if not order:
                raise ValueError("Order not found.")
            if order["status"] == "paid":
                raise ValueError("This order has already been paid.")
            if order["status"] != "placed":
                raise ValueError("Only placed orders can be paid.")
            total = money(order["total_amount"])
            if amount != total:
                raise ValueError(f"Payment must equal the bill total ({total}).")
            conn.execute("""
                INSERT INTO payments(order_id, method, amount, status)
                VALUES(?,?,?,'completed')
            """, (order_id, method, str(amount)))
            conn.execute("UPDATE orders SET status='paid' WHERE id=?", (order_id,))
