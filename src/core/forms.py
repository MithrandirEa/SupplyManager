"""
Formulaires pour les actions rapides du dashboard
"""
import json
from datetime import date
from django import forms
from django.utils import timezone
from supply.models import Item, Inventory, InventoryEntry
from authentication.models import User


class BulkInventoryForm(forms.Form):
    """
    Formulaire d'inventaire global : soumet tous les articles avec leur
    quantité comptée en une seule fois.
    items_data est un JSON : [{"item_id": 1, "quantity": 5}, ...]
    """
    items_data = forms.CharField(widget=forms.HiddenInput())
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    def clean_items_data(self):
        raw = self.cleaned_data['items_data']
        try:
            entries = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raise forms.ValidationError("Format des données invalide.")
        if not isinstance(entries, list) or len(entries) == 0:
            raise forms.ValidationError("Aucun article fourni.")
        cleaned = []
        for entry in entries:
            try:
                item_id = int(entry['item_id'])
                quantity = int(entry['quantity'])
                # outside_quantity est optionnel : s'il n'est pas fourni, on prend 0 ou on traitera dans save()
                outside_quantity = entry.get('outside_quantity')
            except (KeyError, ValueError, TypeError):
                raise forms.ValidationError(
                    "Données d'article mal formées."
                )
            if quantity < 0:
                raise forms.ValidationError(
                    "La quantité ne peut pas être négative."
                )
            if outside_quantity is not None and int(outside_quantity) < 0:
                raise forms.ValidationError(
                    "La quantité fournisseur ne peut pas être négative."
                )
            try:
                item = Item.objects.get(pk=item_id)
            except Item.DoesNotExist:
                raise forms.ValidationError(
                    f"Article introuvable (id={item_id})."
                )
            
            cleaned_item = {
                'item': item, 
                'quantity': quantity
            }
            if outside_quantity is not None:
                cleaned_item['outside_quantity'] = int(outside_quantity)
                
            cleaned.append(cleaned_item)
        return cleaned

    def save(self, user=None):
        """Crée l'enregistrement Inventory + InventoryEntry et met à jour les stocks.

        Logique :
        - counted_quantity = articles comptés sur site
        - si outside_quantity fourni (mode manuel) : on l'utilise
        - sinon (mode auto) : on prend la valeur actuelle de item.outside_quantity
        - total mis à jour = counted + outside
        """
        entries = self.cleaned_data['items_data']
        notes = self.cleaned_data.get('notes', '')

        inventory = Inventory.objects.create(
            created_by=user,
            notes=notes,
        )
        now = timezone.now()
        for entry in entries:
            item = entry['item']
            counted = entry['quantity']
            
            # Détermination de outside_quantity
            if 'outside_quantity' in entry:
                outside = entry['outside_quantity']
            else:
                outside = item.outside_quantity  # Mode auto : snapshot actuel

            InventoryEntry.objects.create(
                inventory=inventory,
                item=item,
                counted_quantity=counted,
                outside_quantity_snapshot=outside,
            )
            # Mise à jour des stocks
            item.available_quantity = counted
            # On met à jour outside_quantity seulement si fourni (mode manuel)
            # Sinon, en mode auto, on suppose qu'il n'a pas bougé (ou géré ailleurs)
            if 'outside_quantity' in entry:
                item.outside_quantity = outside
                
            item.total_quantity = counted + outside
            item.last_inventory_quantity = counted
            item.last_inventory_date = now
            
            update_fields = [
                'available_quantity',
                'total_quantity',
                'last_inventory_quantity',
                'last_inventory_date',
            ]
            if 'outside_quantity' in entry:
                update_fields.append('outside_quantity')
                
            item.save(update_fields=update_fields)

        return inventory


class ChangeInventoryForm(forms.Form):
    """
    Formulaire pour modifier un inventaire existant.
    Même champ items_data que BulkInventoryForm, mais update au lieu de create.
    """
    items_data = forms.CharField(widget=forms.HiddenInput())
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    def clean_items_data(self):
        raw = self.cleaned_data['items_data']
        try:
            entries = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raise forms.ValidationError("Format des données invalide.")
        if not isinstance(entries, list) or len(entries) == 0:
            raise forms.ValidationError("Aucun article fourni.")
        cleaned = []
        for entry in entries:
            try:
                item_id = int(entry['item_id'])
                quantity = int(entry['quantity'])
            except (KeyError, ValueError, TypeError):
                raise forms.ValidationError("Données d'article mal formées.")
            if quantity < 0:
                raise forms.ValidationError(
                    "La quantité ne peut pas être négative."
                )
            try:
                item = Item.objects.get(pk=item_id)
            except Item.DoesNotExist:
                raise forms.ValidationError(
                    f"Article introuvable (id={item_id})."
                )
            cleaned.append({'item': item, 'quantity': quantity})
        return cleaned

    def save(self, inventory):
        """Met à jour un Inventory existant et recalcule les stocks."""
        entries_data = self.cleaned_data['items_data']
        notes = self.cleaned_data.get('notes', '')

        inventory.notes = notes
        inventory.save(update_fields=['notes'])

        # Supprimer les anciennes entrées et recréer depuis zéro
        inventory.entries.all().delete()

        now = timezone.now()
        for entry in entries_data:
            item = entry['item']
            counted = entry['quantity']
            outside = item.outside_quantity

            InventoryEntry.objects.create(
                inventory=inventory,
                item=item,
                counted_quantity=counted,
                outside_quantity_snapshot=outside,
            )
            item.available_quantity = counted
            item.total_quantity = counted + outside
            item.last_inventory_quantity = counted
            item.last_inventory_date = now
            item.save(update_fields=[
                'available_quantity',
                'total_quantity',
                'last_inventory_quantity',
                'last_inventory_date',
            ])

        return inventory


class InventoryUpdateForm(forms.Form):
    """
    Formulaire pour Saisir un inventaire (article unique — conservé pour compatibilité)
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

class ContactForm(forms.Form):
    '''
    Formulaire de contact pour l'aide et le support.
    '''
    subject = forms.CharField(
        max_length=100,
        label='Sujet',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bugg ou question...'})
    )
    sender = forms.EmailField(
        label='Votre email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'votre.email@example.com'})
    )
    message = forms.CharField(
        label='Message',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'D�crivez votre probl�me ici...'})
    )

