"""
URLs pour l'application core
"""
from django.urls import path
from . import views


app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('staff/', views.staff_management, name='staff_management'),
    path('supplies/', views.supplies_management, name='supplies_management'),
    path(
        'suppliers/',
        views.suppliers_management,
        name='suppliers_management'
    ),
]
