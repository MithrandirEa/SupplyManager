# ─────────────────────────────────────────────
#  MONTHLY STATS
# ─────────────────────────────────────────────

MONTHLY_STATS_HEADERS = [
    'Mois', 'Article', 'Catégorie', 'Envoyé', 'Reçu', 'Facturé',
    'Différence Reçu', 'Différence Facturé'
]

def _monthly_stats_rows():
    from supplier.models import OrderItem
    from supply.models import Item
    from django.db.models import Sum
    from django.db.models.functions import TruncMonth, Coalesce
    from collections import defaultdict

    # 1. Tous les items (disponibles)
    items = Item.objects.filter(is_available=True).select_related('category').order_by('category__name', 'name')
    items_dict = {i.id: i for i in items}
    
    # 2. Stats
    raw_stats = OrderItem.objects.annotate(
        month=TruncMonth('order__order_date')
    ).values('month', 'item').annotate(
        sent=Coalesce(Sum('quantity'), 0),
        received=Coalesce(Sum('received_quantity'), 0),
        invoiced=Coalesce(Sum('invoiced_quantity'), 0),
    ).order_by('-month', 'item')

    # 3. Grouper par mois
    grouped_stats = defaultdict(dict)
    months = set()
    
    for stat in raw_stats:
        m = stat['month']
        if m:
            months.add(m)
            grouped_stats[m][stat['item']] = stat

    sorted_months = sorted(list(months), reverse=True)
    
    rows = []
    for m in sorted_months:
        month_str = m.strftime('%B %Y').capitalize()
        for item in items:
            stats = grouped_stats[m].get(item.id, {'sent': 0, 'received': 0, 'invoiced': 0})
            s = stats['sent']
            r = stats['received']
            i = stats['invoiced']
            
            rows.append([
                month_str,
                item.name,
                item.category.name if item.category else '',
                s,
                r,
                i,
                r - s,      # Diff Reçu (Reçu - Envoyé)
                i - s       # Diff Facturé (Facturé - Envoyé)
            ])
    return rows

def export_monthly_stats_csv():
    response, writer = _csv_response('suivi_mensuel.csv')
    writer.writerow(MONTHLY_STATS_HEADERS)
    for row in _monthly_stats_rows():
        writer.writerow(row)
    return response

def export_monthly_stats_excel():
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Suivi Mensuel'
    ws.append(MONTHLY_STATS_HEADERS)
    for row in _monthly_stats_rows():
        ws.append(row)
    _style_header_row(ws)
    _autofit(ws)
    return _excel_response(wb, 'suivi_mensuel.xlsx')
