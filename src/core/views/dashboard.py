from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from authentication.decorators import role_required
from supplier.forms import QuickOrderForm
from supplier.models import Order, Supplier
from supply.models import Item

from ..forms import BulkInventoryForm, ContractExtensionForm
from ..services import DashboardService


@login_required
def dashboard(request):
    """
    Vue principale du dashboard.

    Affiche les stocks, alertes et statut des commandes.
    Accessible à tous les utilisateurs authentifiés.
    """
    # Récupération de toutes les données du dashboard
    dashboard_data = DashboardService.get_all_dashboard_data()

    # Calcul du nombre d'alertes à partir des données déjà récupérées
    alerts_count = DashboardService.get_alerts_count(dashboard_data)

    # Récupération des fournisseurs pour le formulaire de commande
    all_suppliers = Supplier.objects.all().order_by('name')

    # Récupération des items groupés par catégorie pour le formulaire
    items_by_category = defaultdict(list)
    all_items = Item.objects.filter(
        is_available=True
    ).select_related('category').order_by('category__name', 'name')

    for item in all_items:
        category_name = item.category.name if item.category else "Sans catégorie"
        items_by_category[category_name].append(item)

    # Récupération des commandes non terminées pour la réception
    pending_orders = Order.objects.filter(
        status__in=['pending', 'delayed']
    ).select_related('supplier').prefetch_related('order_items__item').order_by('expected_return_date')

    # Préparation du contexte
    context = {
        # Stocks
        'missing_items': dashboard_data['missing_items'],
        'excess_items': dashboard_data['excess_items'],
        'items_at_supplier': dashboard_data['items_at_supplier'],

        # Alertes
        'stock_alerts': dashboard_data['stock_alerts'],
        'order_alerts': dashboard_data['order_alerts'],
        'contract_alerts': dashboard_data['contract_alerts'],

        # Commandes
        'outdated_orders': dashboard_data['outdated_orders'],
        'waited_orders': dashboard_data['waited_orders'],
        'pending_orders': pending_orders,

        # Compteurs pour badges
        'alerts_count': alerts_count,

        # Informations additionnelles
        'total_alerts': alerts_count['total'],

        # Pour les actions rapides
        'all_suppliers': all_suppliers,
        'all_items': list(all_items),
        'items_by_category': dict(items_by_category),
    }

    return render(request, 'dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def create_order_ajax(request):
    """
    Vue AJAX pour créer une commande rapide depuis le dashboard
    """
    form = QuickOrderForm(request.POST, user=request.user)

    if form.is_valid():
        order = form.save()
        return JsonResponse({
            'success': True,
            'message': f'Commande #{order.id} créée avec succès.',
            'order_id': order.id
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
@role_required(['ADMIN', 'DIRECTOR'])
@require_http_methods(["POST"])
def update_inventory_ajax(request):
    """
    Vue AJAX pour Saisir un inventaire global (tous les articles).
    """

    form = BulkInventoryForm(request.POST)

    if form.is_valid():
        inventory = form.save(user=request.user)
        return JsonResponse({
            'success': True,
            'message': (
                f'Inventaire du {inventory.created_at.strftime("%d/%m/%Y %H:%M")} '
                f'enregistré ({inventory.entries.count()} articles).'
            ),
            'inventory_id': inventory.id,
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
@role_required(['ADMIN', 'DIRECTOR'])
@require_http_methods(["POST"])
def extend_contract_ajax(request):
    """
    Vue AJAX pour prolonger un contrat
    """
    form = ContractExtensionForm(request.POST)

    if form.is_valid():
        user = form.save()
        end_date = user.date_end_contract.strftime("%d/%m/%Y")
        return JsonResponse({
            'success': True,
            'message': (
                f'Contrat de {user.username} '
                f'prolongé jusqu\'au {end_date}.'
            ),
            'username': user.username,
            'new_date': user.date_end_contract.isoformat()
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
