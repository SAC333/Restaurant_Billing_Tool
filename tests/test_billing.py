import unittest
from decimal import Decimal
from services.billing_service import BillingService

class BillingTests(unittest.TestCase):
    def setUp(self):
        self.service = BillingService("0.05")

    def test_bill_calculation(self):
        items = [
            {"price": "240", "quantity": 2},
            {"price": "45", "quantity": 4},
        ]
        result = self.service.calculate(items)
        self.assertEqual(result["subtotal"], Decimal("660.00"))
        self.assertEqual(result["tax"], Decimal("33.00"))
        self.assertEqual(result["total"], Decimal("693.00"))

    def test_discount(self):
        result = self.service.calculate(
            [{"price": "100", "quantity": 1}], discount="10"
        )
        self.assertEqual(result["total"], Decimal("94.50"))

    def test_discount_cannot_exceed_subtotal(self):
        with self.assertRaises(ValueError):
            self.service.calculate([{"price": "100", "quantity": 1}], discount="101")

if __name__ == "__main__":
    unittest.main()
