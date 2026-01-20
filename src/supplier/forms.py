from django import forms
from .models import Supplier


class CreateSupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'website', 'contact_email', 'phone_number', 'other_details', 'associated_items']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'other_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'associated_items': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }


class ChangeSupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'website', 'contact_email', 'phone_number', 'other_details', 'associated_items']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'other_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'associated_items': forms.SelectMultiple(attrs={'class': 'form-select'}),

        }