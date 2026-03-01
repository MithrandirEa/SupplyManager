from django.shortcuts import render, redirect
from django.contrib import messages
from authentication.models import User
from django.contrib.auth.decorators import login_required, permission_required

from supplier.models import Supplier
from supply.models import Item
from .services import DashboardService


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
    }

    return render(request, 'dashboard.html', context)
