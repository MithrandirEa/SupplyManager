"""
Formulaires pour les actions rapides du dashboard
"""
from datetime import date
from django import forms
from supply.models import Item
from authentication.models import User


class InventoryUpdateForm(forms.Form):
    """
    Formulaire pour enregistrer un inventaire
    """
    item_id = forms.IntegerField(widget=forms.HiddenInput())
    last_inventory_quantity = forms.IntegerField(
        label='Quantité constatée',
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quantité lors de l\'inventaire'
        })
    )

    def clean_item_id(self):
        item_id = self.cleaned_data['item_id']
        try:
            Item.objects.get(pk=item_id)
        except Item.DoesNotExist:
            raise forms.ValidationError("Article introuvable.")
        return item_id

    def save(self):
        """Enregistre l'inventaire pour l'article"""
        item_id = self.cleaned_data['item_id']
        quantity = self.cleaned_data['last_inventory_quantity']
        
        item = Item.objects.get(pk=item_id)
        item.last_inventory_quantity = quantity
        item.last_inventory_date = date.today()
        item.save()
        
        return item


class ContractExtensionForm(forms.Form):
    """
    Formulaire pour prolonger un contrat d'un membre Crew
    """
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    new_end_date = forms.DateField(
        label='Nouvelle date de fin',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    def clean_user_id(self):
        user_id = self.cleaned_data['user_id']
        try:
            User.objects.get(pk=user_id, role=User.CREW)
        except User.DoesNotExist:
            raise forms.ValidationError("Utilisateur Crew introuvable.")
        return user_id

    def clean_new_end_date(self):
        new_date = self.cleaned_data['new_end_date']
        if new_date <= date.today():
            raise forms.ValidationError(
                "La nouvelle date doit être dans le futur."
            )
        return new_date

    def save(self):
        """Met à jour la date de fin de contrat et réactive le compte si nécessaire"""
        user_id = self.cleaned_data['user_id']
        new_date = self.cleaned_data['new_end_date']
        
        user = User.objects.get(pk=user_id)
        user.date_end_contract = new_date
        
        # Réactiver automatiquement le compte si la date est dans le futur
        if new_date >= date.today():
            user.still_active = True
        
        user.save()
        
        return user
