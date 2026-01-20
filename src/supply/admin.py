from django.contrib import admin
from .models import Item, ItemsCategory


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'total_quantity', 'outside_quantity', 'available_quantity', 'information', 'created_by', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'category')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ItemsCategory)
class ItemsCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)