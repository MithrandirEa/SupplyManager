"""
Tests pour le dashboard et ses composants
"""
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

import json
from supply.models import Item, ItemsCategory, Inventory, InventoryEntry
from supplier.models import Supplier, Order, OrderItem
from core.services import DashboardService
from core.forms import BulkInventoryForm, ChangeInventoryForm


User = get_user_model()


class DashboardServiceTestCase(TestCase):
    """Tests pour le service DashboardService"""

    def setUp(self):
        """Configuration initiale pour les tests"""
        # Créer des utilisateurs
        self.admin = User.objects.create_user(
            username='admin_test',
            password='testpass123',
            role=User.ADMIN
        )
        self.director = User.objects.create_user(
            username='director_test',
            password='testpass123',
            role=User.DIRECTOR
        )
        self.crew = User.objects.create_user(
            username='crew_test',
            password='testpass123',
            role=User.CREW,
            date_end_contract=date.today() + timedelta(days=10)
        )

        # Créer une catégorie
        self.category = ItemsCategory.objects.create(name='Linge')

        # Créer des items avec différents états
        self.item_missing = Item.objects.create(
            name='Serviette Manquante',
            category=self.category,
            total_quantity=100,
            available_quantity=30,
            outside_quantity=20,
            excess_quantity=0
        )

        self.item_excess = Item.objects.create(
            name='Drap Excédentaire',
            category=self.category,
            total_quantity=50,
            available_quantity=50,
            outside_quantity=0,
            excess_quantity=20
        )

        self.item_outside = Item.objects.create(
            name='Taie chez Fournisseur',
            category=self.category,
            total_quantity=100,
            available_quantity=80,
            outside_quantity=20,
            excess_quantity=0
        )

        # Créer un fournisseur
        self.supplier = Supplier.objects.create(
            name='Pressing Test',
            contact_email='test@pressing.fr'
        )

        # Créer des commandes
        self.order_delayed = Order.objects.create(
            supplier=self.supplier,
            order_date=timezone.now() - timedelta(days=15),
            expected_return_date=date.today() - timedelta(days=10),
            status='delayed',
            created_by=self.admin
        )

        self.order_waited = Order.objects.create(
            supplier=self.supplier,
            order_date=timezone.now() - timedelta(days=2),
            expected_return_date=date.today() + timedelta(days=5),
            status='pending',
            created_by=self.admin
        )

        # Ajouter des items aux commandes
        OrderItem.objects.create(
            order=self.order_delayed,
            item=self.item_missing,
            quantity=10
        )

    def test_get_missing_items(self):
        """Test de la récupération des items manquants"""
        missing_items = DashboardService.get_missing_items()

        self.assertEqual(len(missing_items), 1)
        self.assertEqual(missing_items[0].name, 'Serviette Manquante')
        self.assertEqual(missing_items[0].missing_quantity, 50)

    def test_get_excess_items(self):
        """Test de la récupération des items excédentaires"""
        excess_items = DashboardService.get_excess_items()

        self.assertEqual(len(excess_items), 1)
        self.assertEqual(excess_items[0].name, 'Drap Excédentaire')

    def test_get_items_at_supplier(self):
        """Test de la récupération des items chez fournisseur"""
        items_at_supplier = DashboardService.get_items_at_supplier()

        # On doit avoir 2 items : item_missing et item_outside
        self.assertEqual(len(items_at_supplier), 2)
        names = [item.name for item in items_at_supplier]
        self.assertIn('Serviette Manquante', names)
        self.assertIn('Taie chez Fournisseur', names)

    def test_get_stock_anomalies(self):
        """Test de la détection des anomalies de stock"""
        anomalies = DashboardService.get_stock_anomalies()

        # 1 déficit + 1 excès = 2 anomalies
        self.assertEqual(len(anomalies), 2)

        # Vérifier les types
        types = [a['type'] for a in anomalies]
        self.assertIn('deficit', types)
        self.assertIn('excess', types)

    def test_get_order_anomalies(self):
        """Test de la détection des commandes en retard"""
        anomalies = DashboardService.get_order_anomalies()

        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]['type'], 'order_delay')
        self.assertEqual(anomalies[0]['order'].id, self.order_delayed.id)
        self.assertEqual(anomalies[0]['severity'], 'danger')

    def test_get_contract_anomalies(self):
        """Test de la détection des contrats expirant"""
        anomalies = DashboardService.get_contract_anomalies()

        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]['type'], 'contract_expiry')
        self.assertEqual(anomalies[0]['user'].username, 'crew_test')

    def test_get_outdated_orders(self):
        """Test de la récupération des commandes en retard"""
        outdated = DashboardService.get_outdated_orders()

        self.assertEqual(len(outdated), 1)
        self.assertEqual(outdated[0].id, self.order_delayed.id)

    def test_get_waited_orders(self):
        """Test de la récupération des commandes attendues"""
        waited = DashboardService.get_waited_orders()

        self.assertEqual(len(waited), 1)
        self.assertEqual(waited[0].id, self.order_waited.id)

    def test_get_all_dashboard_data(self):
        """Test de la récupération de toutes les données"""
        data = DashboardService.get_all_dashboard_data()

        # Vérifier que toutes les clés sont présentes
        expected_keys = [
            'missing_items', 'excess_items', 'items_at_supplier',
            'stock_alerts', 'order_alerts', 'contract_alerts',
            'outdated_orders', 'waited_orders'
        ]

        for key in expected_keys:
            self.assertIn(key, data)

        # Vérifier quelques valeurs
        self.assertEqual(len(data['missing_items']), 1)
        self.assertEqual(len(data['excess_items']), 1)
        self.assertEqual(len(data['outdated_orders']), 1)

    def test_get_alerts_count(self):
        """Test du comptage des alertes"""
        counts = DashboardService.get_alerts_count()

        self.assertIn('stock', counts)
        self.assertIn('orders', counts)
        self.assertIn('contracts', counts)
        self.assertIn('total', counts)

        self.assertEqual(counts['stock'], 2)
        self.assertEqual(counts['orders'], 1)
        self.assertEqual(counts['contracts'], 1)
        self.assertEqual(counts['total'], 4)


class DashboardViewTestCase(TestCase):
    """Tests pour la vue dashboard"""

    def setUp(self):
        """Configuration initiale"""
        self.client = Client()

        # Créer des utilisateurs
        self.admin = User.objects.create_user(
            username='admin_view',
            password='testpass123',
            role=User.ADMIN
        )
        self.director = User.objects.create_user(
            username='director_view',
            password='testpass123',
            role=User.DIRECTOR
        )
        self.crew = User.objects.create_user(
            username='crew_view',
            password='testpass123',
            role=User.CREW
        )

        self.dashboard_url = reverse('dashboard')

    def test_dashboard_redirect_if_not_logged_in(self):
        """Test de redirection si non connecté"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('?next=/dashboard/', response.url)

    def test_dashboard_access_denied_for_crew(self):
        """Test de refus d'accès pour Crew"""
        self.client.login(username='crew_view', password='testpass123')
        response = self.client.get(self.dashboard_url)

        # Redirection vers home
        self.assertEqual(response.status_code, 302)

    def test_dashboard_access_allowed_for_admin(self):
        """Test d'accès autorisé pour Admin"""
        self.client.login(username='admin_view', password='testpass123')
        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_dashboard_access_allowed_for_director(self):
        """Test d'accès autorisé pour Director"""
        self.client.login(username='director_view', password='testpass123')
        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_dashboard_context_contains_all_data(self):
        """Test que le contexte contient toutes les données"""
        self.client.login(username='admin_view', password='testpass123')
        response = self.client.get(self.dashboard_url)

        # Vérifier que toutes les clés sont dans le contexte
        expected_keys = [
            'missing_items', 'excess_items', 'items_at_supplier',
            'stock_alerts', 'order_alerts', 'contract_alerts',
            'outdated_orders', 'waited_orders', 'alerts_count',
            'total_alerts'
        ]

        for key in expected_keys:
            self.assertIn(key, response.context)

    def test_dashboard_performance(self):
        """Test de performance : moins de 20 requêtes SQL"""
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        self.client.login(username='admin_view', password='testpass123')

        with CaptureQueriesContext(connection) as context:
            response = self.client.get(self.dashboard_url)

        # Le nombre de requêtes doit être raisonnable
        # grâce à select_related et prefetch_related
        self.assertLess(
            len(context.captured_queries),
            30,
            f"Trop de requêtes SQL : {len(context.captured_queries)}"
        )


class BulkInventoryFormTestCase(TestCase):
    """Tests pour BulkInventoryForm"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='inv_admin', password='pass', role=User.ADMIN
        )
        cat = ItemsCategory.objects.create(name='LingeTest')
        self.item1 = Item.objects.create(
            name='Serviette', category=cat,
            total_quantity=50, available_quantity=40,
            outside_quantity=5, created_by=self.admin
        )
        self.item2 = Item.objects.create(
            name='Drap', category=cat,
            total_quantity=30, available_quantity=25,
            outside_quantity=2, created_by=self.admin
        )

    def _make_form(self, items_list, notes=''):
        return BulkInventoryForm({
            'items_data': json.dumps(items_list),
            'notes': notes,
        })

    def test_valid_form_creates_inventory(self):
        """Un formulaire valide crée un Inventory + InventoryEntry."""
        form = self._make_form([
            {'item_id': self.item1.id, 'quantity': 42},
            {'item_id': self.item2.id, 'quantity': 28},
        ])
        self.assertTrue(form.is_valid(), form.errors)
        inv = form.save(user=self.admin)
        self.assertIsInstance(inv, Inventory)
        self.assertEqual(inv.entries.count(), 2)
        self.assertEqual(inv.created_by, self.admin)

    def test_save_updates_item_last_inventory(self):
        """save() met à jour available_quantity, total_quantity, last_inventory_quantity et last_inventory_date."""
        form = self._make_form([
            {'item_id': self.item1.id, 'quantity': 15},
        ])
        self.assertTrue(form.is_valid())
        form.save(user=self.admin)
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.last_inventory_quantity, 15)
        self.assertIsNotNone(self.item1.last_inventory_date)
        # available_quantity = counted
        self.assertEqual(self.item1.available_quantity, 15)
        # total_quantity = counted + outside_quantity
        expected_total = 15 + self.item1.outside_quantity
        self.assertEqual(self.item1.total_quantity, expected_total)

    def test_save_stores_outside_snapshot(self):
        """save() stocke outside_quantity_snapshot sur chaque InventoryEntry."""
        self.item1.outside_quantity = 8
        self.item1.save()
        form = self._make_form([{'item_id': self.item1.id, 'quantity': 20}])
        self.assertTrue(form.is_valid())
        inv = form.save(user=self.admin)
        entry = inv.entries.get(item=self.item1)
        self.assertEqual(entry.outside_quantity_snapshot, 8)
        self.assertEqual(entry.counted_quantity, 20)
        self.assertEqual(entry.total_counted, 28)
        # total_quantity mis à jour
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.total_quantity, 28)
        self.assertEqual(self.item1.available_quantity, 20)

    def test_notes_saved(self):
        """Les notes sont sauvegardées dans l'inventaire."""
        form = self._make_form(
            [{'item_id': self.item1.id, 'quantity': 10}],
            notes='RAS, tout OK'
        )
        self.assertTrue(form.is_valid())
        inv = form.save(user=self.admin)
        self.assertEqual(inv.notes, 'RAS, tout OK')

    def test_invalid_json_rejected(self):
        """Un JSON invalide est rejeté."""
        form = BulkInventoryForm({'items_data': 'pas_du_json', 'notes': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('items_data', form.errors)

    def test_empty_list_rejected(self):
        """Une liste vide est rejetée."""
        form = self._make_form([])
        self.assertFalse(form.is_valid())

    def test_negative_quantity_rejected(self):
        """Une quantité négative est rejetée."""
        form = self._make_form([{'item_id': self.item1.id, 'quantity': -5}])
        self.assertFalse(form.is_valid())

    def test_unknown_item_rejected(self):
        """Un item_id inexistant est rejeté."""
        form = self._make_form([{'item_id': 99999, 'quantity': 10}])
        self.assertFalse(form.is_valid())

    def test_ajax_endpoint_saves_inventory(self):
        """L'endpoint AJAX /dashboard/update-inventory/ crée un inventaire."""
        self.client.login(username='inv_admin', password='pass')
        data = {
            'items_data': json.dumps([
                {'item_id': self.item1.id, 'quantity': 7},
                {'item_id': self.item2.id, 'quantity': 3},
            ]),
            'notes': '',
        }
        response = self.client.post(reverse('update_inventory_ajax'), data)
        self.assertEqual(response.status_code, 200, response.content)
        resp_data = response.json()
        self.assertTrue(resp_data['success'], resp_data)
        self.assertEqual(Inventory.objects.count(), 1)
        self.assertEqual(InventoryEntry.objects.count(), 2)


class ChangeInventoryTestCase(TestCase):
    """Tests pour ChangeInventoryForm et la vue change_inventory."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='inv_admin2', password='pass', role=User.ADMIN
        )
        cat = ItemsCategory.objects.create(name='LingeChange')
        self.item = Item.objects.create(
            name='Serviette', category=cat,
            total_quantity=30, available_quantity=25,
            outside_quantity=5, created_by=self.admin
        )
        self.inventory = Inventory.objects.create(created_by=self.admin)
        InventoryEntry.objects.create(
            inventory=self.inventory,
            item=self.item,
            counted_quantity=20,
            outside_quantity_snapshot=5,
        )

    def test_change_inventory_form_updates_entries(self):
        """ChangeInventoryForm.save() met à jour les entrées et les stocks."""
        form = ChangeInventoryForm({
            'items_data': json.dumps([{'item_id': self.item.id, 'quantity': 12}]),
            'notes': 'test modif',
        })
        self.assertTrue(form.is_valid(), form.errors)
        form.save(self.inventory)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.notes, 'test modif')
        entry = self.inventory.entries.get(item=self.item)
        self.assertEqual(entry.counted_quantity, 12)
        self.item.refresh_from_db()
        self.assertEqual(self.item.available_quantity, 12)
        self.assertEqual(self.item.total_quantity, 12 + self.item.outside_quantity)

    def test_change_inventory_view_get(self):
        """La vue change_inventory affiche le formulaire en GET."""
        self.client.login(username='inv_admin2', password='pass')
        response = self.client.get(
            reverse('change_inventory', kwargs={'inventory_id': self.inventory.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'inventoryAccordion')

    def test_change_inventory_view_post(self):
        """La vue change_inventory met à jour en POST et redirige."""
        self.client.login(username='inv_admin2', password='pass')
        data = {
            'items_data': json.dumps([{'item_id': self.item.id, 'quantity': 8}]),
            'notes': 'mise à jour',
        }
        response = self.client.post(
            reverse('change_inventory', kwargs={'inventory_id': self.inventory.id}),
            data
        )
        self.assertRedirects(response, reverse('supplies_management'))
        self.item.refresh_from_db()
        self.assertEqual(self.item.available_quantity, 8)