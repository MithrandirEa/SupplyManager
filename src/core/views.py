from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from authentication.decorators import role_required
from authentication.models import User
from supplier.forms import QuickOrderForm
from supplier.models import Supplier
from supply.models import Item

from .forms import (BulkInventoryForm, ChangeInventoryForm, ContactForm,
                    ContractExtensionForm)
from .services import DashboardService


@login_required
def staff_management(request):
    users = User.objects.all().order_by('role', 'username')
    return render(request, 'staff_management.html', {'users': users})


@login_required
def supplies_management(request):
    from collections import defaultdict

    from django.db.models import F, Sum
    from django.db.models.functions import Coalesce, TruncMonth

    from supplier.models import Order, OrderItem
    from supply.models import Inventory, Item

    # 1. Récupérer tous les items pour les colonnes du tableau
    all_items = Item.objects.filter(
        is_available=True).order_by('category__name', 'name')

    # 2. Récupérer les données agrégées par mois et par item
    # On passe par OrderItem pour avoir accès à la date de la commande via 'order__order_date'
    raw_stats = OrderItem.objects.annotate(
        month=TruncMonth('order__order_date')
    ).values('month', 'item').annotate(
        sent=Coalesce(Sum('quantity'), 0),
        received=Coalesce(Sum('received_quantity'), 0),
        invoiced=Coalesce(Sum('invoiced_quantity'), 0),
    ).order_by('-month', 'item__category__name', 'item__name')

    # 3. Restructurer les données : { mois: { item_id: { sent: x, received: y, ... } } }
    grouped_stats = defaultdict(lambda: defaultdict(
        lambda: {'sent': 0, 'received': 0, 'invoiced': 0}))

    # On garde une liste des mois uniques pour l'itération, triée desc
    unique_months = set()

    for stat in raw_stats:
        m = stat['month']
        if m:
            unique_months.add(m)
            item_id = stat['item']
            grouped_stats[m][item_id] = {
                'sent': stat['sent'],
                'received': stat['received'],
                'invoiced': stat['invoiced']
            }

    sorted_months = sorted(list(unique_months), reverse=True)

    # On ne fait pas une "list" pour monthly_stats ici mais "monthly_tables"
    # Cependant, l'ancienne variable 'monthly_stats' était utilisée dans le template.
    # On va remapper monthly_tables dans le contexte de manière appropriée.

    # 4. Construire la structure finale pour le template
    sorted_months = sorted(grouped_stats.keys(), reverse=True)
    monthly_tables = []

    for m in sorted_months:
        if m is None:
            continue  # Cas théorique

        # Liste ordonnée de stats pour chaque item
        items_stats = []

        # Totaux de la ligne (pour le calcul global du mois si besoin ou simplification)
        # Mais le tableau demandé est Items en colonnes.

        for item in all_items:
            stats = grouped_stats[m].get(
                item.id, {'sent': 0, 'received': 0, 'invoiced': 0})

            s = stats['sent'] or 0
            r = stats['received'] or 0
            i = stats['invoiced'] or 0

            items_stats.append({
                'item_id': item.id,
                'sent': s,
                'received': r,
                'invoiced': i,
                'diff_recv': r - s,      # Différence reçue
                'diff_inv': i - s        # Différence facturé - envoyé
            })

        monthly_tables.append({
            'month': m,
            'stats': items_stats
        })

    orders = Order.objects.select_related(
        'supplier', 'created_by'
    ).prefetch_related('order_items__item').all().order_by('-order_date')
    inventories = Inventory.objects.select_related(
        'created_by'
    ).prefetch_related('entries__item__category').all()

    # Récupération de tous les items pour l'onglet Matériels
    # items = Item.objects.all().order_by('category__name', 'name')
    # On va regrouper tous les items (dispo ou non) par catégorie pour l'affichage de l'onglet Matériels
    all_items_by_cat = defaultdict(list)
    all_items_qs = Item.objects.select_related('category').prefetch_related(
        'suppliers').order_by('category__name', 'name')
    for item in all_items_qs:
        cat_name = item.category.name if item.category else "Sans catégorie"
        all_items_by_cat[cat_name].append(item)

    # On trie les catégories par ordre alphabétique (sauf "Sans catégorie" qui pourrait être à la fin si on voulait peaufiner)
    all_items_by_cat_sorted = dict(sorted(all_items_by_cat.items()))

    # Groupement par catégorie pour le modal inventaire (seulement items disponibles)
    items_by_category = defaultdict(list)
    available_items = Item.objects.filter(
        is_available=True
    ).select_related('category').order_by('category__name', 'name')
    for item in available_items:
        cat = item.category.name if item.category else "Sans catégorie"
        items_by_category[cat].append(item)

    # Compter les commandes non terminées
    pending_orders_count = orders.exclude(
        status__in=['completed', 'partial']).count()

    context = {
        'items_by_category_all': all_items_by_cat_sorted,  # Pour l'onglet Matériels
        # Pour compatibilité si utilisé ailleurs (modals de suppression ?)
        'items': all_items_qs,
        'orders': orders,
        'inventories': inventories,
        'pending_orders_count': pending_orders_count,
        # Pour le modal inventaire
        'items_by_category': dict(items_by_category),
        'monthly_tables': monthly_tables,
        'all_items_headers': all_items,
    }

    return render(request, 'supplies_management.html', context)


@login_required
def suppliers_management(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(
        request,
        'suppliers_management.html',
        {'suppliers': suppliers}
    )


@login_required
def print_inventory_sheet(request):
    """
    Vue pour afficher une fiche d'inventaire imprimable.
    ?sort=alpha (par défaut) ou sort=category
    """
    from collections import defaultdict

    from supply.models import Item

    sort = request.GET.get('sort', 'alpha')
    items = Item.objects.filter(is_available=True).select_related('category')

    context = {'sort': sort}

    if sort == 'category':
        items = items.order_by('category__name', 'name')
        items_by_cat = defaultdict(list)
        for item in items:
            cat = item.category.name if item.category else "Sans catégorie"
            items_by_cat[cat].append(item)
        # Trier les clés
        context['items_by_category'] = dict(sorted(items_by_cat.items()))
    else:
        # alpha
        items = items.order_by('name')
        context['items'] = items

    return render(request, 'inventory_sheet.html', context)


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
    from collections import defaultdict

    from supply.models import ItemsCategory

    items_by_category = defaultdict(list)
    all_items = Item.objects.filter(
        is_available=True
    ).select_related('category').order_by('category__name', 'name')

    for item in all_items:
        category_name = item.category.name if item.category else "Sans catégorie"
        items_by_category[category_name].append(item)

    # Récupération des commandes non terminées pour la réception
    from supplier.models import Order
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


@login_required
@role_required(['ADMIN', 'DIRECTOR'])
def change_inventory(request, inventory_id):
    """Vue pour modifier un inventaire existant."""

    from collections import defaultdict

    from supply.models import Inventory, Item

    inventory = Inventory.objects.prefetch_related(
        'entries__item__category'
    ).get(pk=inventory_id)

    entry_map = {
        e.item_id: (e.counted_quantity, e.outside_quantity_snapshot)
        for e in inventory.entries.all()
    }

    all_items = Item.objects.filter(
        is_available=True
    ).select_related('category').order_by('category__name', 'name')

    items_by_category = defaultdict(list)
    for item in all_items:
        cat = item.category.name if item.category else "Sans catégorie"
        if item.id in entry_map:
            counted, outside = entry_map[item.id]
        else:
            counted = item.available_quantity
            outside = item.outside_quantity
        items_by_category[cat].append((item, counted, outside))

    if request.method == 'POST':
        form = ChangeInventoryForm(request.POST)
        if form.is_valid():
            form.save(inventory)
            messages.success(
                request,
                f'Inventaire du {inventory.created_at.strftime("%d/%m/%Y %H:%M")} '
                f'mis à jour.'
            )
            return redirect('supplies_management')
    else:
        form = ChangeInventoryForm(initial={'notes': inventory.notes})

    return render(request, 'change_inventory.html', {
        'inventory': inventory,
        'items_by_category': dict(items_by_category),
        'form': form,
    })


# ─────────────────────────────────────────────
#  Vues d'export
# ─────────────────────────────────────────────

@login_required
def export_items(request):
    """Export CSV ou Excel de tous les articles."""
    from .exports import export_items_csv, export_items_excel
    fmt = request.GET.get('fmt', 'csv')
    items = Item.objects.select_related('category').prefetch_related(
        'suppliers'
    ).order_by('category__name', 'name')
    if fmt == 'excel':
        return export_items_excel(items)
    return export_items_csv(items)


@login_required
def export_orders(request):
    """
    Export commandes.
    ?fmt=csv|excel  &  ?scope=list|all-detail
    """
    from supplier.models import Order

    from .exports import (export_orders_all_detail_csv,
                          export_orders_all_detail_excel,
                          export_orders_list_csv, export_orders_list_excel)
    fmt = request.GET.get('fmt', 'csv')
    scope = request.GET.get('scope', 'list')
    orders = Order.objects.select_related('supplier', 'created_by').prefetch_related(
        'order_items__item__category'
    ).order_by('-order_date')
    if scope == 'all-detail':
        if fmt == 'excel':
            return export_orders_all_detail_excel(orders)
        return export_orders_all_detail_csv(orders)
    # list
    if fmt == 'excel':
        return export_orders_list_excel(orders)
    return export_orders_list_csv(orders)


@login_required
def export_order(request, order_id):
    """Export CSV ou Excel du détail d'une commande."""
    from supplier.models import Order

    from .exports import export_order_detail_csv, export_order_detail_excel
    fmt = request.GET.get('fmt', 'csv')
    order = Order.objects.select_related('supplier').prefetch_related(
        'order_items__item__category'
    ).get(pk=order_id)
    if fmt == 'excel':
        return export_order_detail_excel(order)
    return export_order_detail_csv(order)


@login_required
def export_inventories(request):
    """
    Export inventaires.
    ?fmt=csv|excel  &  ?scope=list|all-detail
    """
    from supply.models import Inventory

    from .exports import (export_inventories_all_detail_csv,
                          export_inventories_all_detail_excel,
                          export_inventories_list_csv,
                          export_inventories_list_excel)
    fmt = request.GET.get('fmt', 'csv')
    scope = request.GET.get('scope', 'list')
    inventories = Inventory.objects.select_related('created_by').prefetch_related(
        'entries__item__category'
    ).order_by('-created_at')
    if scope == 'all-detail':
        if fmt == 'excel':
            return export_inventories_all_detail_excel(inventories)
        return export_inventories_all_detail_csv(inventories)
    if fmt == 'excel':
        return export_inventories_list_excel(inventories)
    return export_inventories_list_csv(inventories)


@login_required
def export_inventory(request, inventory_id):
    """Export CSV ou Excel du détail d'un inventaire."""
    from supply.models import Inventory

    from .exports import (export_inventory_detail_csv,
                          export_inventory_detail_excel)
    fmt = request.GET.get('fmt', 'csv')
    inventory = Inventory.objects.select_related('created_by').prefetch_related(
        'entries__item__category'
    ).get(pk=inventory_id)
    if fmt == 'excel':
        return export_inventory_detail_excel(inventory)
    return export_inventory_detail_csv(inventory)


@login_required
def export_monthly_stats(request):
    """Export du suivi mensuel."""
    from .exports import export_monthly_stats_csv, export_monthly_stats_excel
    fmt = request.GET.get('fmt', 'csv')

    if fmt == 'excel':
        return export_monthly_stats_excel()
    return export_monthly_stats_csv()


def help_view(request):
    """
    Vue pour la page d'aide et le formulaire de contact.
    """
    # On garde le formulaire pour l'affichage, mais le traitement se fait via mailto (client-side)
    form = ContactForm()

    return render(request, 'help.html', {'form': form})
