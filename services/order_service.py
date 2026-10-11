from repositories.order_repository import OrderRepository

class OrderService:
    def __init__(self):
        self.repo = OrderRepository()

    def list_orders(self):
        return self.repo.list_orders()

    def get_order(self, order_id):
        return self.repo.get_order(order_id)

    def dashboard_stats(self):
        return self.repo.dashboard_stats()
