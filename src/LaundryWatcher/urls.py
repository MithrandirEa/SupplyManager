"""
URL configuration for LaundryWatcher project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include

import authentication.views
import core.views
import supply.views
import supplier.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', core.views.dashboard, name='dashboard'),
    
    # Actions rapides AJAX du dashboard
    path(
        'dashboard/create-order/',
        core.views.create_order_ajax,
        name='create_order_ajax'
    ),
    path(
        'dashboard/update-inventory/',
        core.views.update_inventory_ajax,
        name='update_inventory_ajax'
    ),
    path(
        'dashboard/extend-contract/',
        core.views.extend_contract_ajax,
        name='extend_contract_ajax'
    ),
    
    # Page d'aide
    path('help/', core.views.help_view, name='help'),

    # Routes de connexion/déconnexion
    path('', LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True),
        name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    path(
        'change-password/', 
        authentication.views.change_password, 
        name='change_password'
    ),

    # Routes de la barre de navigation
    path('staff/', core.views.staff_management, name='staff_management'),
    path(
        'supplies-management/',
        core.views.supplies_management,
        name='supplies_management'
    ),
    path(
        'suppliers-management/',
        core.views.suppliers_management,
        name='suppliers_management'
    ),

    # Routes de gestion des utilisateurs
    path('create-user/', authentication.views.create_user,
         name='create_user'),
    path(
        'change-user/<int:user_id>/',
        authentication.views.change_user,
        name='change_user'
    ),
    path(
        'delete-user/<int:user_id>/',
        authentication.views.delete_user,
        name='delete_user'
    ),

    # Routes de gestion des items
    path('create-category/', supply.views.create_category, name='create_category'),
    path('create-item/', supply.views.create_item, name='create_item'),
    path(
        'change-item/<int:item_id>/',
        supply.views.change_item,
        name='change_item'
    ),
    path(
        'delete-item/<int:item_id>/',
        supply.views.delete_item,
        name='delete_item'
    ),

    # Routes de gestion des fournisseurs
    path(
        'create-supplier/',
        supplier.views.create_supplier,
        name='create_supplier'
    ),
    path(
        'change-supplier/<int:supplier_id>/',
        supplier.views.change_supplier,
        name='change_supplier'
    ),
    path(
        'delete-supplier/<int:supplier_id>/',
        supplier.views.delete_supplier,
        name='delete_supplier'
    ),

    # Routes de gestion des commandes
    path(
        'change-order/<int:order_id>/',
        supplier.views.change_order,
        name='change_order'
    ),
    path(
        'receive-order/<int:order_id>/',
        supplier.views.receive_order,
        name='receive_order'
    ),
    path(
        'delete-order/<int:order_id>/',
        supplier.views.delete_order,
        name='delete_order'
    ),

    # Routes de gestion des inventaires
    path(
        'change-inventory/<int:inventory_id>/',
        core.views.change_inventory,
        name='change_inventory'
    ),

    # Routes d'export
    path('export/items/', core.views.export_items, name='export_items'),
    path('export/orders/', core.views.export_orders, name='export_orders'),
    path('export/orders/<int:order_id>/', core.views.export_order, name='export_order'),
    path('export/inventories/', core.views.export_inventories, name='export_inventories'),
    path('export/inventories/<int:inventory_id>/', core.views.export_inventory, name='export_inventory'),
    path('export/monthly-stats/', core.views.export_monthly_stats, name='export_monthly_stats'),

    # Impression fiche inventaire
    path('print-inventory-sheet/', core.views.print_inventory_sheet, name='print_inventory_sheet'),
]
