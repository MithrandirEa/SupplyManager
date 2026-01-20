from django import forms
from .models import Item, ItemsCategory


class CreateItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'category', 'total_quantity', 'outside_quantity', 'available_quantity', 'information']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'total_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'outside_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'available_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'information': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ChangeItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'category', 'total_quantity', 'outside_quantity', 'available_quantity', 'information']
        widgets = {
            'total_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'outside_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'information': forms.TextInput(attrs={'class': 'form-control'}),

        }