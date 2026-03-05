from django.contrib import admin

from .models import Order, OrderItem, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'website', 'contact_email',
        'phone_number', 'other_details', 'created_at'
    )
    search_fields = ('name', 'contact_email')
    readonly_fields = ('created_at', 'updated_at')


class OrderItemInline(admin.TabularInline):
    """Inline pour gérer les items d'une commande"""
    model = OrderItem
    extra = 1
    fields = ('item', 'quantity', 'notes')
    autocomplete_fields = ['item']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'supplier', 'order_date', 'expected_return_date',
        'actual_return_date', 'status', 'is_delayed', 'days_delayed',
        'created_by'
    )
    list_filter = ('status', 'order_date', 'expected_return_date')
    search_fields = ('supplier__name', 'notes')
    readonly_fields = (
        'created_at', 'updated_at', 'is_delayed', 'days_delayed'
    )
    fieldsets = (
        ('Informations de base', {
            'fields': ('supplier', 'order_date', 'created_by')
        }),
        ('Dates', {
            'fields': ('expected_return_date', 'actual_return_date')
        }),
        ('Statut', {
            'fields': ('status', 'is_delayed', 'days_delayed')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [OrderItemInline]
    date_hierarchy = 'order_date'

    def save_model(self, request, obj, form, change):
        """Définit automatiquement created_by lors de la création"""
        if not change:  # Si c'est une nouvelle commande
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'notes')
    list_filter = ('order__status', 'order__order_date')
    search_fields = ('item__name', 'order__supplier__name')
    autocomplete_fields = ['item', 'order']
