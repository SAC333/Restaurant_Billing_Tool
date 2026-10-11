from database.connection import get_connection

class OrderRepository:
    def list_orders(self, limit=300):
        with get_connection() as conn:
            rows = conn.execute("""
                SELECT o.*,
                       (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id=o.id) AS item_count
                FROM orders o
                ORDER BY o.id DESC LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_order(self, order_id):
        with get_connection() as conn:
            order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
            if not order:
                return None
            items = conn.execute(
                "SELECT * FROM order_items WHERE order_id=? ORDER BY id",
                (order_id,),
            ).fetchall()
            payments = conn.execute(
                "SELECT * FROM payments WHERE order_id=? ORDER BY id",
                (order_id,),
            ).fetchall()
            return {"order": dict(order), "items": [dict(x) for x in items],
                    "payments": [dict(x) for x in payments]}

    def dashboard_stats(self):
        with get_connection() as conn:
            sales = conn.execute("""
                SELECT COALESCE(SUM(CAST(total_amount AS REAL)),0)
                FROM orders
                WHERE status='paid' AND date(created_at)=date('now','localtime')
            """).fetchone()[0]
            count = conn.execute("""
                SELECT COUNT(*) FROM orders
                WHERE date(created_at)=date('now','localtime')
            """).fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM orders WHERE status='placed'"
            ).fetchone()[0]
            return {"sales": sales, "orders_today": count, "pending": pending}
