from decimal import Decimal
from repositories.menu_repository import MenuRepository

class MenuService:
    def __init__(self):
        self.repo = MenuRepository()

    def list_items(self, available_only=False):
        return self.repo.list_items(available_only)

    def save_item(self, name, category, price, item_id=None):
        try:
            price = Decimal(str(price))
        except Exception as exc:
            raise ValueError("Enter a valid price.") from exc
        if price < 0:
            raise ValueError("Price cannot be negative.")
        self.repo.save_item(name, category, price, item_id)

    def set_available(self, item_id, available):
        self.repo.set_available(item_id, available)
