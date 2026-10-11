from decimal import Decimal
from database.connection import get_connection

class MenuRepository:
    def list_items(self, available_only=False):
        with get_connection() as conn:
            sql = "SELECT * FROM menu_items"
            if available_only:
                sql += " WHERE is_available = 1"
            sql += " ORDER BY category, name"
            return [dict(r) for r in conn.execute(sql).fetchall()]

    def save_item(self, name, category, price, item_id=None):
        name, category = name.strip(), category.strip()
        if not name or not category:
            raise ValueError("Name and category are required.")
        if price < 0:
            raise ValueError("Price cannot be negative.")
        with get_connection() as conn:
            if item_id:
                conn.execute(
                    "UPDATE menu_items SET name=?, category=?, price=? WHERE id=?",
                    (name, category, str(price), item_id),
                )
            else:
                conn.execute(
                    "INSERT INTO menu_items(name, category, price) VALUES(?,?,?)",
                    (name, category, str(price)),
                )

    def set_available(self, item_id, available):
        with get_connection() as conn:
            conn.execute(
                "UPDATE menu_items SET is_available=? WHERE id=?",
                (1 if available else 0, item_id),
            )
