from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "restaurant.db"
RECEIPTS_DIR = PROJECT_ROOT / "receipts"

APP_NAME = "Restaurant Billing & Management System"
CURRENCY = "₹"
DEFAULT_TAX_RATE = "0.05"  # Illustrative only; configure for your jurisdiction.
