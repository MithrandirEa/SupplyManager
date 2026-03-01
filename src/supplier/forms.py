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
    
    # Champs pour les items (seront traités séparément)
    items = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
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
    
    def clean_items(self):
        """Valide les items sélectionnés"""
        import json
        from supply.models import Item
        
        items_json = self.cleaned_data.get('items', '[]')
        
        if not items_json or items_json == '[]':
            return []
        
        try:
            items_data = json.loads(items_json)
        except json.JSONDecodeError:
            raise forms.ValidationError("Format d'items invalide.")
        
        if not items_data:
            raise forms.ValidationError(
                "Veuillez ajouter au moins un article à la commande."
            )
        
        validated_items = []
        for item_data in items_data:
            try:
                # Vérifier que les champs requis sont présents
                if 'item_id' not in item_data or 'quantity' not in item_data:
                    raise ValueError("Champs requis manquants")
                
                item_id = int(item_data.get('item_id'))
                quantity = int(item_data.get('quantity'))
                
                if quantity <= 0:
                    raise forms.ValidationError(
                        "La quantité doit être supérieure à 0."
                    )
                
                item = Item.objects.get(pk=item_id)
                validated_items.append({
                    'item': item,
                    'quantity': quantity
                })
            except (ValueError, TypeError, Item.DoesNotExist, KeyError):
                raise forms.ValidationError(
                    "Article invalide dans la commande."
                )
        
        return validated_items

    def save(self, commit=True):
        from supplier.models import OrderItem
        from django.utils import timezone
        
        order = super().save(commit=False)
        order.order_date = timezone.now()
        order.status = 'pending'
        
        if self.user:
            order.created_by = self.user
        
        if commit:
            order.save()
            
            # Créer les OrderItems
            items_data = self.cleaned_data.get('items', [])
            for item_data in items_data:
                OrderItem.objects.create(
                    order=order,
                    item=item_data['item'],
                    quantity=item_data['quantity']
                )
        
        return order
