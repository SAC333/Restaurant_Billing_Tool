import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from app.config import APP_NAME, CURRENCY, DEFAULT_TAX_RATE
from database.connection import initialize_database
from services.menu_service import MenuService
from services.billing_service import BillingService, money
from services.order_service import OrderService
from utils.receipt import create_pdf
from ui.styles import BG, NAVY, BLUE, WHITE, TEXT, MUTED, GREEN, RED

class RestaurantApp(tk.Tk):
    def __init__(self):
        super().__init__()
        initialize_database()
        self.menu_service = MenuService()
        self.billing_service = BillingService(DEFAULT_TAX_RATE)
        self.order_service = OrderService()
        self.cart = {}
        self.selected_menu_id = None
        self.last_order_id = None

        self.title(APP_NAME)
        self._fit_to_screen()
        self.minsize(900, 620)
        self.configure(bg=BG)
        self._configure_style()
        self._build_shell()
        self.show_dashboard()

    def _fit_to_screen(self):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(1180, screen_w - 40)
        height = min(780, screen_h - 100)
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 4)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10),
                        background=WHITE, fieldbackground=WHITE, foreground=TEXT)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background="#E8EDF5", foreground=NAVY)
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 7))
        style.configure("Primary.TButton", background=BLUE, foreground=WHITE)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground=NAVY)
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("TEntry", padding=6)

    def _build_shell(self):
        header = tk.Frame(self, bg=NAVY, height=68)
        header.pack(fill="x")
        tk.Label(header, text="🍽  Restaurant Billing", bg=NAVY, fg=WHITE,
                 font=("Segoe UI", 17, "bold")).pack(side="left", padx=22, pady=16)
        tk.Label(header, text="Order • Billing • Management", bg=NAVY, fg="#D7E2F2",
                 font=("Segoe UI", 10)).pack(side="right", padx=22)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)
        self.sidebar = tk.Frame(body, bg="#FFFFFF", width=205)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="WORKSPACE", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(22, 8))
        for label, callback in [
            ("Dashboard", self.show_dashboard),
            ("New Order", self.show_new_order),
            ("Menu Management", self.show_menu),
            ("Order History", self.show_history),
        ]:
            ttk.Button(self.sidebar, text=label, command=callback).pack(
                fill="x", padx=12, pady=4)
        tk.Label(self.sidebar, text="Local SQLite database", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 8)).pack(side="bottom", pady=14)
        self.content = tk.Frame(body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True, padx=18, pady=16)

    def _clear(self):
        for child in self.content.winfo_children():
            child.destroy()

    def _title(self, title, subtitle=None):
        ttk.Label(self.content, text=title, style="Title.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(self.content, text=subtitle, style="Muted.TLabel").pack(
                anchor="w", pady=(4, 16))
        else:
            tk.Frame(self.content, bg=BG, height=16).pack()

    def _button(self, parent, text, command, primary=False):
        return ttk.Button(parent, text=text, command=command,
                          style="Primary.TButton" if primary else "TButton")

    def show_dashboard(self):
        self._clear()
        self._title("Dashboard", "Overview of restaurant activity")
        stats = self.order_service.dashboard_stats()
        cards = tk.Frame(self.content, bg=BG)
        cards.pack(fill="x")
        data = [
            ("Today's sales", f"{CURRENCY}{Decimal(str(stats['sales'])):,.2f}"),
            ("Orders today", str(stats["orders_today"])),
            ("Unpaid orders", str(stats["pending"])),
        ]
        for label, value in data:
            card = tk.Frame(cards, bg=WHITE, highlightbackground="#E1E6EF",
                            highlightthickness=1, padx=20, pady=18)
            card.pack(side="left", fill="x", expand=True, padx=(0, 12))
            tk.Label(card, text=label, bg=WHITE, fg=MUTED,
                     font=("Segoe UI", 10)).pack(anchor="w")
            tk.Label(card, text=value, bg=WHITE, fg=NAVY,
                     font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(8, 0))
        self._button(self.content, "＋  Create New Order", self.show_new_order,
                     primary=True).pack(anchor="w", pady=24)
        ttk.Label(self.content, text="Recent orders", style="Title.TLabel").pack(anchor="w", pady=(4, 10))
        self._orders_tree(self.content, limit=8)

    def _orders_tree(self, parent, limit=300):
        columns = ("number", "date", "type", "status", "total")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=min(limit, 12))
        for col, label, width in [
            ("number", "Order number", 230), ("date", "Created", 170),
            ("type", "Type", 100), ("status", "Status", 100), ("total", "Total", 120)
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width, anchor="w")
        for order in self.order_service.list_orders()[:limit]:
            tree.insert("", "end", iid=str(order["id"]), values=(
                order["order_number"], order["created_at"], order["order_type"],
                order["status"], f"{CURRENCY}{Decimal(order['total_amount']):.2f}"
            ))
        tree.pack(fill="both", expand=True)
        tree.bind("<Double-1>", lambda _e: self._view_selected_order(tree))
        return tree

    def _view_selected_order(self, tree):
        selection = tree.selection()
        if not selection:
            return
        self.show_order_detail(int(selection[0]))

    def show_new_order(self):
        self._clear()
        self.cart = {}
        self._title("Create New Order", "Select menu items and quantities, then save the order.")
        top = tk.Frame(self.content, bg=BG)
        top.pack(fill="x", pady=(0, 12))
        ttk.Label(top, text="Order type").pack(side="left")
        self.order_type_var = tk.StringVar(value="dine_in")
        type_box = ttk.Combobox(top, textvariable=self.order_type_var,
                                values=("dine_in", "takeaway"), state="readonly", width=14)
        type_box.pack(side="left", padx=(8, 18))
        ttk.Label(top, text="Table number").pack(side="left")
        self.table_var = tk.StringVar(value="1")
        self.table_entry = ttk.Entry(top, textvariable=self.table_var, width=10)
        self.table_entry.pack(side="left", padx=8)
        type_box.bind("<<ComboboxSelected>>", self._toggle_table)

        body = tk.Frame(self.content, bg=BG)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))
        right = tk.Frame(body, bg=BG, width=390)
        right.pack(side="left", fill="both")
        right.pack_propagate(False)

        ttk.Label(left, text="Available menu", style="Title.TLabel").pack(anchor="w", pady=(0, 8))
        self._button(left, "Add Selected Item", self._add_selected_to_cart,
                     primary=True).pack(side="bottom", fill="x", pady=(10, 0))
        self.menu_tree = ttk.Treeview(left, columns=("category", "name", "price"),
                                      show="headings", height=12)
        for col, label, width in [
            ("category", "Category", 110), ("name", "Item", 210), ("price", "Price", 90)
        ]:
            self.menu_tree.heading(col, text=label)
            self.menu_tree.column(col, width=width, anchor="w")
        for item in self.menu_service.list_items(available_only=True):
            self.menu_tree.insert("", "end", iid=str(item["id"]),
                values=(item["category"], item["name"], f"{CURRENCY}{Decimal(item['price']):.2f}"))
        self.menu_tree.pack(fill="both", expand=True)
        self.menu_tree.bind("<Double-1>", lambda _e: self._add_selected_to_cart())

        ttk.Label(right, text="Current order", style="Title.TLabel").pack(anchor="w", pady=(0, 8))
        actions = tk.Frame(right, bg=BG)
        actions.pack(side="bottom", fill="x", pady=(6, 0))
        self._button(actions, "Clear", self._clear_cart).pack(side="left")
        self._button(actions, "Save Order & Bill", self._save_order,
                     primary=True).pack(side="right")
        self.total_var = tk.StringVar(value="Subtotal: ₹0.00   Tax: ₹0.00   Total: ₹0.00")
        ttk.Label(right, textvariable=self.total_var, wraplength=370,
                  font=("Segoe UI", 10, "bold")).pack(side="bottom", anchor="w", pady=8)
        discount_row = tk.Frame(right, bg=BG)
        discount_row.pack(side="bottom", fill="x", pady=(8, 4))
        ttk.Label(discount_row, text="Discount (₹)").pack(side="left")
        self.discount_var = tk.StringVar(value="0")
        ttk.Entry(discount_row, textvariable=self.discount_var, width=12).pack(side="right")
        self.discount_var.trace_add("write", lambda *_: self._update_totals())
        qty_row = tk.Frame(right, bg=BG)
        qty_row.pack(side="bottom", fill="x", pady=8)
        self._button(qty_row, "− Qty", lambda: self._change_quantity(-1)).pack(side="left")
        self._button(qty_row, "+ Qty", lambda: self._change_quantity(1)).pack(side="left", padx=5)
        self._button(qty_row, "Remove", self._remove_cart_item).pack(side="left")
        self.cart_tree = ttk.Treeview(right, columns=("item", "qty", "amount"),
                                      show="headings", height=12)
        for col, label, width in [("item", "Item", 180), ("qty", "Qty", 45), ("amount", "Amount", 100)]:
            self.cart_tree.heading(col, text=label)
            self.cart_tree.column(col, width=width, anchor="w")
        self.cart_tree.pack(fill="both", expand=True)

    def _toggle_table(self, _event=None):
        state = "normal" if self.order_type_var.get() == "dine_in" else "disabled"
        self.table_entry.configure(state=state)

    def _add_selected_to_cart(self):
        selected = self.menu_tree.selection()
        if not selected:
            messagebox.showwarning("Select item", "Choose a menu item first.")
            return
        item_id = int(selected[0])
        self.cart[item_id] = self.cart.get(item_id, 0) + 1
        self._refresh_cart()
        if self.cart_tree.exists(str(item_id)):
            self.cart_tree.selection_set(str(item_id))
            self.cart_tree.focus(str(item_id))
            self.cart_tree.see(str(item_id))

    def _cart_items(self):
        available = {int(item["id"]): item for item in self.menu_service.list_items()}
        result = []
        for item_id, qty in self.cart.items():
            item = available.get(item_id)
            if item:
                result.append({"id": item_id, "name": item["name"],
                               "price": Decimal(str(item["price"])), "quantity": qty})
        return result

    def _refresh_cart(self):
        selected = self.cart_tree.selection()
        keep = selected[0] if selected else None
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        items = self._cart_items()
        for item in items:
            self.cart_tree.insert("", "end", iid=str(item["id"]),
                values=(item["name"], item["quantity"],
                        f"{CURRENCY}{money(item['price'] * item['quantity']):.2f}"))
        if keep and self.cart_tree.exists(keep):
            self.cart_tree.selection_set(keep)
            self.cart_tree.focus(keep)
        self._update_totals()

    def _update_totals(self):
        try:
            bill = self.billing_service.calculate(
                self._cart_items(), self.discount_var.get().strip() or "0")
            self.total_var.set(
                f"Subtotal: {CURRENCY}{bill['subtotal']:.2f}   "
                f"Tax: {CURRENCY}{bill['tax']:.2f}\n"
                f"Discount: {CURRENCY}{bill['discount']:.2f}   "
                f"Total: {CURRENCY}{bill['total']:.2f}"
            )
        except (ValueError, InvalidOperation):
            self.total_var.set("Check discount amount.")

    def _change_quantity(self, change):
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showinfo("Select item", "Select an item in the current order.")
            return
        item_id = int(selection[0])
        self.cart[item_id] = self.cart.get(item_id, 0) + change
        if self.cart[item_id] <= 0:
            del self.cart[item_id]
        self._refresh_cart()

    def _remove_cart_item(self):
        selection = self.cart_tree.selection()
        if selection:
            self.cart.pop(int(selection[0]), None)
            self._refresh_cart()

    def _clear_cart(self):
        self.cart.clear()
        self._refresh_cart()

    def _save_order(self):
        try:
            discount = Decimal(self.discount_var.get().strip() or "0")
            result = self.billing_service.create_order(
                self.order_type_var.get(), self.table_var.get(), self.cart, discount
            )
        except (ValueError, InvalidOperation) as exc:
            messagebox.showerror("Cannot save order", str(exc))
            return
        self.last_order_id = result["id"]
        self.show_order_detail(result["id"])

    def show_order_detail(self, order_id):
        data = self.order_service.get_order(order_id)
        if not data:
            messagebox.showerror("Not found", "Order could not be found.")
            return
        self._clear()
        order, items = data["order"], data["items"]
        self._title("Order & Billing", order["order_number"])
        summary = tk.Frame(self.content, bg=WHITE, padx=18, pady=14)
        summary.pack(fill="x", pady=(0, 12))
        tk.Label(summary, text=f"Status: {order['status'].upper()}",
                 bg=WHITE, fg=GREEN if order["status"] == "paid" else BLUE,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(summary, text=f"Type: {order['order_type']}    Table: {order.get('table_number') or '-'}",
                 bg=WHITE, fg=TEXT, font=("Segoe UI", 10)).pack(anchor="w", pady=5)

        # Bottom block is packed first so the totals and action buttons
        # (including "Generate PDF Receipt") are always visible; the item
        # list above absorbs any remaining space and adapts to the window.
        bottom = tk.Frame(self.content, bg=BG)
        bottom.pack(side="bottom", fill="x", pady=(8, 0))
        actions = tk.Frame(bottom, bg=BG)
        actions.pack(side="bottom", anchor="w", pady=(8, 0))
        if order["status"] == "placed":
            self._button(actions, "Record Payment", lambda: self._payment_dialog(order_id),
                         primary=True).pack(side="left", padx=(0, 8))
        self._button(actions, "Print / Save Bill (PDF)", lambda: self._make_receipt(order_id)).pack(side="left", padx=8)
        self._button(actions, "Back to Order History", self.show_history).pack(side="left", padx=8)
        self._button(actions, "New Order", self.show_new_order).pack(side="left", padx=8)
        if data["payments"]:
            payment = data["payments"][-1]
            ttk.Label(bottom, text=f"Payment: {payment['method'].upper()} • {payment['status']}",
                      style="Muted.TLabel").pack(side="bottom", anchor="w", pady=4)
        totals = tk.Frame(bottom, bg=BG)
        totals.pack(side="bottom", anchor="e", pady=4)
        for label, key in [
            ("Subtotal", "subtotal"), ("Discount", "discount_amount"),
            ("Tax", "tax_amount"), ("TOTAL", "total_amount")
        ]:
            tk.Label(totals, text=f"{label}:  {CURRENCY}{Decimal(order[key]):.2f}",
                     bg=BG, fg=NAVY, font=("Segoe UI", 11, "bold" if label == "TOTAL" else "normal")
                     ).pack(anchor="e", pady=1)

        tree = ttk.Treeview(self.content, columns=("item", "price", "qty", "amount"),
                            show="headings", height=8)
        for col, label, width in [
            ("item", "Item", 330), ("price", "Unit price", 130),
            ("qty", "Quantity", 100), ("amount", "Line total", 140)
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width, anchor="w")
        for item in items:
            tree.insert("", "end", values=(
                item["item_name"], f"{CURRENCY}{Decimal(item['unit_price']):.2f}",
                item["quantity"], f"{CURRENCY}{Decimal(item['line_total']):.2f}"
            ))
        tree.pack(fill="both", expand=True, pady=(0, 8))

    def _payment_dialog(self, order_id):
        data = self.order_service.get_order(order_id)
        if not data:
            return
        order = data["order"]
        method = simpledialog.askstring(
            "Payment method", "Enter payment method: cash, upi, or card", parent=self
        )
        if method is None:
            return
        method = method.strip().lower()
        try:
            self.billing_service.record_payment(order_id, method, order["total_amount"])
        except ValueError as exc:
            messagebox.showerror("Payment failed", str(exc))
            return
        messagebox.showinfo("Payment successful", "Payment recorded successfully.")
        self.show_order_detail(order_id)

    def _make_receipt(self, order_id):
        data = self.order_service.get_order(order_id)
        if not data:
            return
        try:
            path = create_pdf(data)
        except Exception as exc:
            messagebox.showerror("Receipt error", str(exc))
            return
        messagebox.showinfo("Receipt generated", f"PDF saved to:\n{path}")

    def show_menu(self):
        self._clear()
        self._title("Menu Management", "Add and edit items, or toggle their availability.")
        form = tk.Frame(self.content, bg=WHITE, padx=14, pady=14)
        form.pack(fill="x", pady=(0, 16))
        self.menu_name = tk.StringVar()
        self.menu_category = tk.StringVar(value="Main Course")
        self.menu_price = tk.StringVar()
        for col, (label, var, width) in enumerate([
            ("Item name", self.menu_name, 24),
            ("Category", self.menu_category, 18),
            ("Price (₹)", self.menu_price, 12),
        ]):
            ttk.Label(form, text=label).grid(row=0, column=col, sticky="w", padx=5)
            ttk.Entry(form, textvariable=var, width=width).grid(
                row=1, column=col, padx=5, pady=5, sticky="w")
        btn_row = tk.Frame(form, bg=WHITE)
        btn_row.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self._button(btn_row, "Add Item", self._add_menu_item, primary=True).pack(
            side="left", padx=(5, 8))
        self._button(btn_row, "Update Selected", self._update_menu_item).pack(side="left", padx=8)
        self._button(btn_row, "Clear Form", self._clear_menu_form).pack(side="left", padx=8)

        actions = tk.Frame(self.content, bg=BG)
        actions.pack(side="bottom", fill="x", pady=(10, 0))
        self._button(actions, "Toggle Availability", self._toggle_menu_availability).pack(side="left")

        self.menu_admin_tree = ttk.Treeview(self.content,
            columns=("id", "name", "category", "price", "available"),
            show="headings", height=12)
        for col, label, width in [
            ("id", "ID", 55), ("name", "Item", 250), ("category", "Category", 170),
            ("price", "Price", 120), ("available", "Available", 100)
        ]:
            self.menu_admin_tree.heading(col, text=label)
            self.menu_admin_tree.column(col, width=width, anchor="w")
        self.menu_admin_tree.pack(fill="both", expand=True, pady=(0, 8))
        self.menu_admin_tree.bind("<<TreeviewSelect>>", self._select_menu_item)
        self._load_menu_admin()

    def _load_menu_admin(self):
        for row in self.menu_admin_tree.get_children():
            self.menu_admin_tree.delete(row)
        for item in self.menu_service.list_items():
            self.menu_admin_tree.insert("", "end", iid=str(item["id"]), values=(
                item["id"], item["name"], item["category"],
                f"{CURRENCY}{Decimal(item['price']):.2f}",
                "Yes" if item["is_available"] else "No"
            ))

    def _select_menu_item(self, _event=None):
        selection = self.menu_admin_tree.selection()
        if not selection:
            return
        item = next((x for x in self.menu_service.list_items()
                     if x["id"] == int(selection[0])), None)
        if item:
            self.selected_menu_id = item["id"]
            self.menu_name.set(item["name"])
            self.menu_category.set(item["category"])
            self.menu_price.set(str(item["price"]))

    def _add_menu_item(self):
        try:
            price = Decimal(self.menu_price.get().strip())
            self.menu_service.save_item(self.menu_name.get(), self.menu_category.get(), price)
        except (ValueError, InvalidOperation) as exc:
            messagebox.showerror("Invalid menu item", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Could not add item", f"Check that the item name is unique.\n{exc}")
            return
        self._clear_menu_form()
        self._load_menu_admin()

    def _update_menu_item(self):
        if not self.selected_menu_id:
            messagebox.showinfo("Select item", "Select a menu item to update.")
            return
        try:
            self.menu_service.save_item(
                self.menu_name.get(), self.menu_category.get(),
                Decimal(self.menu_price.get().strip()), self.selected_menu_id
            )
        except (ValueError, InvalidOperation) as exc:
            messagebox.showerror("Invalid menu item", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Could not update item", str(exc))
            return
        self._clear_menu_form()
        self._load_menu_admin()

    def _clear_menu_form(self):
        self.selected_menu_id = None
        self.menu_name.set("")
        self.menu_category.set("Main Course")
        self.menu_price.set("")

    def _toggle_menu_availability(self):
        selection = self.menu_admin_tree.selection()
        if not selection:
            messagebox.showinfo("Select item", "Select a menu item first.")
            return
        item_id = int(selection[0])
        item = next(x for x in self.menu_service.list_items() if x["id"] == item_id)
        self.menu_service.set_available(item_id, not bool(item["is_available"]))
        self._load_menu_admin()

    def show_history(self):
        self._clear()
        self._title("Order History", "Double-click an order to review the bill or record payment.")
        self._orders_tree(self.content, limit=300)

