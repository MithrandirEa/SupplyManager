from django import forms
from .models import Item, ItemsCategory

class CreateCategoryForm(forms.ModelForm):
    class Meta:
        model = ItemsCategory
        fields = ['name']
        labels = {
            'name': 'Nom de la catégorie'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

class CreateItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'name', 'category', 'total_quantity',
            'outside_quantity', 'available_quantity', 'information'
        ]
        labels = {
            'name': 'Nom',
            'category': 'Catégorie',
            'total_quantity': 'Quantité totale',
            'outside_quantity': 'Quantité hors site',
            'available_quantity': 'Quantité sur site',
            'information': 'Informations complémentaires',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'total_quantity': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0}
            ),
            'outside_quantity': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0}
            ),
            'available_quantity': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0}
            ),
            'information': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
        }


class ChangeItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'name', 'category', 'total_quantity',
            'outside_quantity', 'available_quantity', 'information'
        ]
        labels = {
            'name': 'Nom',
            'category': 'Catégorie',
            'total_quantity': 'Quantité totale',
            'outside_quantity': 'Quantité hors site',
            'available_quantity': 'Quantité sur site',
            'information': 'Informations complémentaires',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'total_quantity': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0}
            ),
            'outside_quantity': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0}
            ),
            'available_quantity': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0}
            ),
            'information': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
        }


class BuyItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['total_quantity', 'suppliers', 'stock_entry_date']
        labels = {
            'total_quantity': 'Quantité achetée (à ajouter au stock)',
            'suppliers': 'Fournisseur',
            'stock_entry_date': "Date d'entrée en stock",
        }
        widgets = {
            'total_quantity': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 1}
            ),
            'suppliers': forms.Select(attrs={'class': 'form-select'}),
            'stock_entry_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
        }
