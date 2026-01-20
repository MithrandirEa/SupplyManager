from django.contrib import admin
from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'website', 'contact_email',
        'phone_number', 'other_details', 'created_at'
    )
    search_fields = ('name', 'contact_email')
    filter_horizontal = ('associated_items',)
    readonly_fields = ('created_at', 'updated_at')
