# Restaurant Billing & Management System

A lightweight desktop restaurant billing application built with Python, Tkinter, and SQLite. It is designed as a one-day technical-assessment project and demonstrates the basic restaurant flow: menu → order → bill → payment → receipt.

## Features

- Dashboard with today's paid sales, order count, and unpaid-order count
- Create dine-in and takeaway orders
- Add menu items to an order and increase/decrease/remove quantities
- Subtotal, discount, tax, and total calculations using `Decimal`
- Menu management: add, edit, activate/deactivate items
- Record cash, UPI, or card payments
- Prevent duplicate payment for already-paid orders
- Order history and order detail view
- PDF receipt generation (ReportLab)
- SQLite persistence and automatic first-run database/schema initialization
- Basic automated billing tests

## Technology

- Python 3.10+
- Tkinter/ttk (Python GUI)
- SQLite via the standard-library `sqlite3`
- ReportLab for PDF receipts
- `unittest` for tests

## Project structure

```text
restaurant_billing/
├── app/                 # Entry point and configuration
├── database/            # SQLite connection, schema initialization, seed data
├── models/              # Data models
├── repositories/        # Database access
├── services/            # Order, menu, and billing logic
├── ui/                  # Tkinter screens
├── utils/               # Receipt generation
├── tests/               # Automated tests
├── data/                # Runtime database (created automatically)
├── receipts/            # Generated PDF receipts (created on demand)
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10 or later
- Tkinter installed/enabled for your Python distribution
- `pip`

On some Linux distributions, Tkinter may need a separate OS package (for example, `python3-tk`).

## Run locally

Open a terminal in the project root.

### 1. Create and activate a virtual environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Start the app

```bash
python -m app.main
```

The database is created at `data/restaurant.db` on first run and is seeded with sample menu items.

## Run tests

From the project root:

```bash
python -m unittest discover -s tests -v
```

## Billing and tax

The default tax rate is `0.05` (5%) solely as an illustrative demo value. Change `DEFAULT_TAX_RATE` in `app/config.py` to a rate and tax model appropriate to the restaurant and jurisdiction. Confirm whether menu prices are tax-inclusive or tax-exclusive before real-world use. Discounts are currently a fixed currency amount.

The application uses Python `Decimal` for bill calculations and stores monetary values as decimal strings in SQLite. For a production system, consider integer paise storage, explicit tax components, invoice numbering policy, audit logs, and stronger migration/versioning.

## Database

SQLite is local to the machine; a separate database server is not required. Foreign keys are enabled for each connection. The app creates tables and sample menu data automatically.

To reset the demo database, close the application and delete `data/restaurant.db`, then launch the app again. This permanently removes local orders, payments, and menu edits.

## Architecture

Layered modular monolith:

1. **UI (`ui/`)** — collects staff input and renders data.
2. **Services (`services/`)** — validates requests, calculates bills, and coordinates order/payment workflows.
3. **Repositories (`repositories/`)** — perform SQL operations.
4. **Database (`database/`)** — creates connections, tables, indexes, and seed data.

The UI does not contain SQL queries. Order creation and payment writes use database transactions.

## Known limitations

- Single-machine, single-restaurant demo; no user login or roles.
- No live payment gateway integration; payment method is recorded by staff.
- No kitchen ticketing, inventory, refunds, split payments, or printer integration.
- Tax configuration is intentionally basic and should be reviewed before real use.
- Dashboard sales uses SQLite date functions and the machine's local date.
- No automated schema migration framework beyond the initial schema version.
- PDF receipts use a basic layout and default fonts.

## Potential future improvements

- Authentication and role-based permissions
- Restaurant profile, invoice settings, and tax breakdown configuration
- Refunds, split payments, and payment audit trail
- Kitchen order tickets and order status workflow
- Inventory and ingredient stock
- CSV/Excel reports, date filters, and backup/restore
- Packaging as a Windows executable
- More integration/UI and database transaction tests
