from django.shortcuts import render, redirect
from django.contrib import messages
from authentication.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from supplier.models import Supplier
from supply.models import Item
from .services import DashboardService
from .forms import InventoryUpdateForm, ContractExtensionForm
from supplier.forms import QuickOrderForm


@login_required
def home(request):
    return render(request, 'home.html')


@login_required
@permission_required('authentication.view_user', raise_exception=True)
def staff_management(request):
    users = User.objects.all().order_by('role', 'username')
    return render(request, 'staff_management.html', {'users': users})


@login_required
def supplies_management(request):
    items = Item.objects.all().order_by('category', 'name')
    return render(request, 'supplies_management.html', {'items': items})


@login_required
@permission_required('supplier.view_supplier', raise_exception=True)
def suppliers_management(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(
        request,
        'suppliers_management.html',
        {'suppliers': suppliers}
    )


def _user_can_access_dashboard(user):
    """
    Vérifie si l'utilisateur peut accéder au dashboard.

    Seuls Admin et Director ont accès.
    """
    return user.role in [User.ADMIN, User.DIRECTOR]


@login_required
def dashboard(request):
    """
    Vue principale du dashboard.

    Affiche les stocks, alertes et statut des commandes.
    Accessible uniquement aux Admin et Director.
    """
    # Vérification des permissions
    if not _user_can_access_dashboard(request.user):
        messages.error(
            request,
            "Vous n'avez pas la permission d'accéder au dashboard."
        )
        return redirect('home')

    # Récupération de toutes les données du dashboard
    dashboard_data = DashboardService.get_all_dashboard_data()

    # Récupération du nombre d'alertes pour l'affichage
    alerts_count = DashboardService.get_alerts_count()

    # Récupération des fournisseurs pour le formulaire de commande
    all_suppliers = Supplier.objects.all().order_by('name')
    
    # Récupération des items pour le formulaire de commande
    all_items = Item.objects.filter(
        is_available=True
    ).order_by('category__name', 'name')

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

        # Compteurs pour badges
        'alerts_count': alerts_count,

        # Informations additionnelles
        'total_alerts': alerts_count['total'],
        
        # Pour les actions rapides
        'all_suppliers': all_suppliers,
        'all_items': all_items,
    }

    return render(request, 'dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def create_order_ajax(request):
    """
    Vue AJAX pour créer une commande rapide depuis le dashboard
    """
    # Vérification des permissions
    if not _user_can_access_dashboard(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée.'
        }, status=403)

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
@require_http_methods(["POST"])
def update_inventory_ajax(request):
    """
    Vue AJAX pour enregistrer un inventaire
    """
    # Vérification des permissions
    if not _user_can_access_dashboard(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée.'
        }, status=403)

    form = InventoryUpdateForm(request.POST)
    
    if form.is_valid():
        item = form.save()
        return JsonResponse({
            'success': True,
            'message': f'Inventaire de "{item.name}" enregistré.',
            'item_name': item.name,
            'new_quantity': item.last_inventory_quantity
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
@require_http_methods(["POST"])
def extend_contract_ajax(request):
    """
    Vue AJAX pour prolonger un contrat
    """
    # Vérification des permissions
    if not _user_can_access_dashboard(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée.'
        }, status=403)

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
