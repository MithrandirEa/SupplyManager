from django.contrib import admin
from .models import Item, ItemsCategory, Inventory, InventoryEntry


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'total_quantity', 'available_quantity',
        'outside_quantity', 'excess_quantity', 'missing_quantity',
        'created_by', 'created_at'
    )
    list_filter = ('category', 'created_at', 'is_available')
    search_fields = ('name', 'category__name', 'information')
    readonly_fields = (
        'created_at', 'updated_at', 'missing_quantity', 'actual_loss_quantity'
    )
    fieldsets = (
        ('Informations de base', {
            'fields': (
                'name', 'category', 'suppliers',
                'information', 'created_by'
            )
        }),
        ('Quantités', {
            'fields': (
                'total_quantity', 'available_quantity', 'outside_quantity',
                'excess_quantity', 'missing_quantity'
            )
        }),
        ('Inventaire', {
            'fields': (
                'last_inventory_quantity', 'last_inventory_date',
                'actual_loss_quantity', 'stock_entry_date'
            )
        }),
        ('Statut', {
            'fields': ('is_available',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    filter_horizontal = ('suppliers',)

    def missing_quantity(self, obj):
        """Affiche la quantité manquante calculée"""
        return obj.missing_quantity
    missing_quantity.short_description = 'Quantité manquante'


@admin.register(ItemsCategory)
class ItemsCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class InventoryEntryInline(admin.TabularInline):
    model = InventoryEntry
    extra = 0
    readonly_fields = ('item', 'counted_quantity')


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'created_by', 'entry_count', 'notes')
    list_filter = ('created_at', 'created_by')
    readonly_fields = ('created_at',)
    inlines = [InventoryEntryInline]

    @admin.display(description='Nb articles')
    def entry_count(self, obj):
        return obj.entries.count()
