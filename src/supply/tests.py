from django.test import TestCase
from django.utils import timezone

from authentication.models import User

from .models import Inventory, InventoryEntry, Item, ItemsCategory


class ItemsCategoryTest(TestCase):
    def setUp(self):
        self.category = ItemsCategory.objects.create(name="Detergents")

    def test_str(self):
        self.assertEqual(str(self.category), "Detergents")


class ItemModelTest(TestCase):
    def setUp(self):
        self.category = ItemsCategory.objects.create(name="Linens")
        self.item = Item.objects.create(
            name="Bed Sheet",
            category=self.category,
            total_quantity=100,
            available_quantity=80,
            outside_quantity=10,
            last_inventory_quantity=0,
        )

    def test_item_creation(self):
        """Verify default values and basic creation."""
        self.assertEqual(self.item.name, "Bed Sheet")
        self.assertEqual(self.item.total_quantity, 100)
        self.assertEqual(self.item.available_quantity, 80)
        self.assertEqual(self.item.outside_quantity, 10)
        self.assertEqual(self.item.excess_quantity, 0)  # Default
        self.assertTrue(self.item.is_available)  # Default

    def test_missing_quantity_property(self):
        """Test calculation (total - (avail + outside))."""
        # 100 - (80 + 10) = 10
        self.assertEqual(self.item.missing_quantity, 10)

        # Case where available + outside > total (should be 0, not negative)
        # 100 - (95 + 10) = -5 -> Should be 0 based on model logic: max(0, result)
        self.item.available_quantity = 95
        self.item.save()
        self.assertEqual(self.item.missing_quantity, 0)

    def test_actual_loss_quantity_property(self):
        """Test calculation (total - last_inventory)."""
        # Initially last_inventory_quantity is 0, so actual_loss_quantity should be 0 (if logic is correct)
        # Model logic: if last_inventory_quantity == 0: return 0
        self.assertEqual(self.item.actual_loss_quantity, 0)

        # Case: Stock count (last inventory) was 105. Current total is 100.
        # Loss = 100 - 105 = -5.
        # Wait, typical logic is: Previous Inventory - Consumed + Received = Theoretical.
        # Here logic is simpler: total - last_inventory_quantity.
        # If last inventory was 105, and now we declare 100 total, we lost 5.
        # So return value is -5.
        self.item.last_inventory_quantity = 105
        self.item.save()
        self.assertEqual(self.item.actual_loss_quantity, -5)

        # Case: Stock count was 90. Current total is 100.
        # 100 - 90 = 10.
        # Logic says: return result if result < 0 else 0. So returns 0.
        self.item.last_inventory_quantity = 90
        self.item.save()
        self.assertEqual(self.item.actual_loss_quantity, 0)

    def test_str(self):
        self.assertEqual(str(self.item), "Bed Sheet")


class InventoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="inv_user", password="password", role="staff")
        self.category = ItemsCategory.objects.create(name="General")
        self.item = Item.objects.create(
            name="Towel", category=self.category, total_quantity=100)

    def test_inventory_creation(self):
        """Test basic inventory creation."""
        inventory = Inventory.objects.create(
            created_by=self.user, notes="Monthly Check")
        self.assertEqual(inventory.created_by, self.user)
        self.assertEqual(inventory.notes, "Monthly Check")
        self.assertIsNotNone(inventory.created_at)

        # Test __str__
        # Because created_at is auto_now_add, we rely on the object's string representation
        expected_str_part = "Inventaire du"
        self.assertIn(expected_str_part, str(inventory))
        self.assertIn(inventory.created_at.strftime(
            '%d/%m/%Y'), str(inventory))

    def test_inventory_entry_logic(self):
        """Manually create an Inventory and InventoryEntry."""
        inventory = Inventory.objects.create(created_by=self.user)

        # Create an entry
        counted = 50
        outside = 5
        entry = InventoryEntry.objects.create(
            inventory=inventory,
            item=self.item,
            counted_quantity=counted,
            outside_quantity_snapshot=outside
        )

        # Verify entry creation
        self.assertEqual(entry.inventory, inventory)
        self.assertEqual(entry.item, self.item)
        self.assertEqual(entry.counted_quantity, counted)
        self.assertEqual(entry.outside_quantity_snapshot, outside)

        # Verify total_counted property
        self.assertEqual(entry.total_counted, counted + outside)

        # Verify __str__
        # "Towel : 50 (+ 5 fournisseur)"
        expected_str = f"Towel : {counted} (+ {outside} fournisseur)"
        self.assertEqual(str(entry), expected_str)
