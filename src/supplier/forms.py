from datetime import date, timedelta
from django import forms
from .models import Supplier, Order


class CreateSupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 'website', 'contact_email',
            'phone_number', 'other_details'
        ]
        labels = {
            'name': 'Nom',
            'website': 'Site web',
            'contact_email': 'Email de contact',
            'phone_number': 'Numéro de téléphone',
            'other_details': 'Informations complémentaires',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(
                attrs={'class': 'form-control'}
            ),
            'phone_number': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'other_details': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }


class ChangeSupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 'website', 'contact_email',
            'phone_number', 'other_details'
        ]
        labels = {
            'name': 'Nom',
            'website': 'Site web',
            'contact_email': 'Email de contact',
            'phone_number': 'Numéro de téléphone',
            'other_details': 'Informations complémentaires',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(
                attrs={'class': 'form-control'}
            ),
            'phone_number': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'other_details': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }


class QuickOrderForm(forms.ModelForm):
    """
    Formulaire simplifié pour créer une commande rapidement
    depuis le dashboard
    """
    class Meta:
        model = Order
        fields = ['supplier', 'expected_return_date']
        labels = {
            'supplier': 'Fournisseur',
            'expected_return_date': 'Date de retour attendue',
        }
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'expected_return_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Définir une date par défaut (7 jours)
        if not self.instance.pk:
            self.fields['expected_return_date'].initial = (
                date.today() + timedelta(days=7)
            )

    def clean_expected_return_date(self):
        expected_date = self.cleaned_data['expected_return_date']
        if expected_date < date.today():
            raise forms.ValidationError(
                "La date de retour attendue doit être dans le futur."
            )
        return expected_date

    def save(self, commit=True):
        order = super().save(commit=False)
        order.order_date = date.today()
        order.status = 'pending'
        
        if self.user:
            order.created_by = self.user
        
        if commit:
            order.save()
        
        return order
