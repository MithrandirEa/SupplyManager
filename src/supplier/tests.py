"""Tests for supplier app"""
import json
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from supplier.models import Supplier, Order, OrderItem
from supplier.forms import QuickOrderForm
from supply.models import Item, ItemsCategory

User = get_user_model()


class QuickOrderFormTestCase(TestCase):
    """Tests pour le formulaire de création rapide de commande"""
    
    def setUp(self):
        """Préparation des données de test"""
        # Créer un utilisateur admin
        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            role='ADMIN'
        )
        
        # Créer un fournisseur
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_email='supplier@test.com',
            phone_number='0123456789',
            address='123 Test St'
        )
        
        # Créer une catégorie
        self.category = ItemsCategory.objects.create(
            name='Test Category'
        )
        
        # Créer des items
        self.item1 = Item.objects.create(
            name='Item 1',
            category=self.category,
            available_quantity=100,
            total_quantity=100,
            is_available=True
        )
        self.item2 = Item.objects.create(
            name='Item 2',
            category=self.category,
            available_quantity=50,
            total_quantity=50,
            is_available=True
        )
    
    def test_create_order_without_items(self):
        """Test création de commande sans items"""
        form_data = {
            'supplier': self.supplier.id,
            'expected_return_date': (date.today() + timedelta(days=7)).isoformat(),
            'items': '[]'  # Liste vide
        }
        form = QuickOrderForm(form_data, user=self.admin)
        self.assertTrue(form.is_valid())
        
        order = form.save()
        self.assertEqual(order.supplier, self.supplier)
        self.assertEqual(order.order_items.count(), 0)
    
    def test_create_order_with_single_item(self):
        """Test création de commande avec un seul item"""
        items_data = [
            {'item_id': self.item1.id, 'quantity': 5}
        ]
        form_data = {
            'supplier': self.supplier.id,
            'expected_return_date': (date.today() + timedelta(days=7)).isoformat(),
            'items': json.dumps(items_data)
        }
        form = QuickOrderForm(form_data, user=self.admin)
        self.assertTrue(form.is_valid())
        
        order = form.save()
        self.assertEqual(order.order_items.count(), 1)
        
        order_item = order.order_items.first()
        self.assertEqual(order_item.item, self.item1)
        self.assertEqual(order_item.quantity, 5)
    
    def test_create_order_with_multiple_items(self):
        """Test création de commande avec plusieurs items"""
        items_data = [
            {'item_id': self.item1.id, 'quantity': 10},
            {'item_id': self.item2.id, 'quantity': 7}
        ]
        form_data = {
            'supplier': self.supplier.id,
            'expected_return_date': (date.today() + timedelta(days=7)).isoformat(),
            'items': json.dumps(items_data)
        }
        form = QuickOrderForm(form_data, user=self.admin)
        self.assertTrue(form.is_valid())
        
        order = form.save()
        self.assertEqual(order.order_items.count(), 2)
        
        # Vérifier les quantités
        item1_order = order.order_items.get(item=self.item1)
        self.assertEqual(item1_order.quantity, 10)
        
        item2_order = order.order_items.get(item=self.item2)
        self.assertEqual(item2_order.quantity, 7)
    
    def test_invalid_item_id(self):
        """Test avec un item_id inexistant"""
        items_data = [
            {'item_id': 99999, 'quantity': 5}  # ID inexistant
        ]
        form_data = {
            'supplier': self.supplier.id,
            'expected_return_date': (date.today() + timedelta(days=7)).isoformat(),
            'items': json.dumps(items_data)
        }
        form = QuickOrderForm(form_data, user=self.admin)
        self.assertFalse(form.is_valid())
        self.assertIn('items', form.errors)
    
    def test_invalid_quantity_zero(self):
        """Test avec une quantité invalide (zéro)"""
        items_data = [
            {'item_id': self.item1.id, 'quantity': 0}
        ]
        form_data = {
            'supplier': self.supplier.id,
            'expected_return_date': (date.today() + timedelta(days=7)).isoformat(),
            'items': json.dumps(items_data)
        }
        form = QuickOrderForm(form_data, user=self.admin)
        self.assertFalse(form.is_valid())
        self.assertIn('items', form.errors)
    
    def test_invalid_quantity_negative(self):
        """Test avec une quantité négative"""
        items_data = [
            {'item_id': self.item1.id, 'quantity': -5}
        ]
        form_data = {
            'supplier': self.supplier.id,
            'expected_return_date': (date.today() + timedelta(days=7)).isoformat(),
            'items': json.dumps(items_data)
        }
        form = QuickOrderForm(form_data, user=self.admin)
        self.assertFalse(form.is_valid())
        self.assertIn('items', form.errors)
    
    def test_invalid_json_format(self):
        """Test avec un JSON invalide"""
        form_data = {
            'supplier': self.supplier.id,
            'expected_return_date': (date.today() + timedelta(days=7)).isoformat(),
            'items': 'invalid json'
        }
        form = QuickOrderForm(form_data, user=self.admin)
        self.assertFalse(form.is_valid())
        self.assertIn('items', form.errors)
    
    def test_missing_required_fields_in_items(self):
        """Test avec des champs manquants dans les items"""
        items_data = [
            {'item_id': self.item1.id}  # Manque quantity
        ]
        form_data = {
            'supplier': self.supplier.id,
            'expected_return_date': (date.today() + timedelta(days=7)).isoformat(),
            'items': json.dumps(items_data)
        }
        form = QuickOrderForm(form_data, user=self.admin)
        self.assertFalse(form.is_valid())
        self.assertIn('items', form.errors)
