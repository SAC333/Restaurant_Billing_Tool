import sqlite3
from contextlib import contextmanager
from app.config import DB_PATH, DATA_DIR

def initialize_database():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            price TEXT NOT NULL,
            is_available INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0,1))
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT NOT NULL UNIQUE,
            order_type TEXT NOT NULL CHECK (order_type IN ('dine_in','takeaway')),
            table_number TEXT,
            status TEXT NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft','placed','paid','cancelled')),
            subtotal TEXT NOT NULL DEFAULT '0.00',
            discount_amount TEXT NOT NULL DEFAULT '0.00',
            tax_rate TEXT NOT NULL DEFAULT '0.05',
            tax_amount TEXT NOT NULL DEFAULT '0.00',
            total_amount TEXT NOT NULL DEFAULT '0.00',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER,
            item_name TEXT NOT NULL,
            unit_price TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            line_total TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            method TEXT NOT NULL CHECK (method IN ('cash','upi','card')),
            amount TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed'
                CHECK (status IN ('pending','completed','failed')),
            paid_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );

        CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
        CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
        """)
        conn.execute("PRAGMA user_version = 1")
        seed_menu(conn)

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def seed_menu(conn):
    count = conn.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0]
    if count:
        return
    rows = [
        ("Paneer Butter Masala", "Main Course", "240.00", 1),
        ("Veg Biryani", "Main Course", "180.00", 1),
        ("Dal Tadka", "Main Course", "160.00", 1),
        ("Butter Naan", "Bread", "45.00", 1),
        ("Tandoori Roti", "Bread", "25.00", 1),
        ("Masala Dosa", "South Indian", "120.00", 1),
        ("Veg Sandwich", "Snacks", "100.00", 1),
        ("French Fries", "Snacks", "90.00", 1),
        ("Tea", "Beverages", "25.00", 1),
        ("Cold Coffee", "Beverages", "110.00", 1),
    ]
    conn.executemany(
        "INSERT INTO menu_items(name, category, price, is_available) VALUES(?,?,?,?)",
        rows,
    )
