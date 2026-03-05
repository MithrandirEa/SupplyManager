from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.shortcuts import render

from authentication.models import User
from supplier.models import Order, OrderItem, Supplier
from supply.models import Inventory, Item

from ..forms import ContactForm


@login_required
def staff_management(request):
    users = User.objects.all().order_by('role', 'username')
    return render(request, 'staff_management.html', {'users': users})


@login_required
def supplies_management(request):
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


def help_view(request):
    """
    Vue pour la page d'aide et le formulaire de contact.
    """
    # On garde le formulaire pour l'affichage, mais le traitement se fait via mailto (client-side)
    form = ContactForm()

    return render(request, 'help.html', {'form': form})
