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
                attrs={'class': 'form-control', 'readonly': 'readonly'}
            ),
            'information': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        total_quantity = cleaned_data.get('total_quantity')
        outside_quantity = cleaned_data.get('outside_quantity')

        if total_quantity is not None and outside_quantity is not None:
            if outside_quantity > total_quantity:
                raise forms.ValidationError(
                    "La quantité hors site (chez le client/fournisseur) ne peut pas "
                    "être supérieure à la quantité totale."
                )
        return cleaned_data


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
                attrs={'class': 'form-control', 'readonly': 'readonly'}
            ),
            'information': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        total_quantity = cleaned_data.get('total_quantity')
        outside_quantity = cleaned_data.get('outside_quantity')

        if total_quantity is not None and outside_quantity is not None:
            if outside_quantity > total_quantity:
                raise forms.ValidationError(
                    "La quantité hors site (chez le client/fournisseur) ne peut pas "
                    "être supérieure à la quantité totale."
                )
        return cleaned_data


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

class ImportItemsForm(forms.Form):
    import_file = forms.FileField(
        label="Fichier d'import (CSV ou Excel)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv, .xlsx, .xls'})
    )
    update_existing = forms.BooleanField(
        label="Mettre à jour les articles existants (basé sur le nom)",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
