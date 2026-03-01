from django.db import models
from django.utils import timezone
from datetime import date


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    other_details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    associated_items = models.ManyToManyField(
        'supply.Item',
        related_name='supplier_set',
        blank=True
    )

    def __str__(self):
        return self.name


class Order(models.Model):
    """Modèle représentant une commande/envoi chez un fournisseur"""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('delayed', 'En retard'),
        ('completed', 'Terminée'),
    ]
    
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Fournisseur"
    )
    order_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de commande"
    )
    expected_return_date = models.DateField(
        verbose_name="Date de retour attendue"
    )
    actual_return_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de retour réelle"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders_created',
        verbose_name="Créé par"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-order_date']

    def __str__(self):
        return (
            f"Commande #{self.id} - {self.supplier.name} "
            f"({self.get_status_display()})"
        )

    @property
    def is_delayed(self):
        """Vérifie si la commande est en retard"""
        if self.status == 'completed':
            return False
        return date.today() > self.expected_return_date

    @property
    def days_delayed(self):
        """Calcule le nombre de jours de retard"""
        if not self.is_delayed:
            return 0
        return (date.today() - self.expected_return_date).days

    def save(self, *args, **kwargs):
        """Met à jour automatiquement le statut en fonction de la date"""
        if self.status != 'completed':
            if self.is_delayed:
                self.status = 'delayed'
            else:
                self.status = 'pending'
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Modèle intermédiaire pour les items d'une commande"""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name="Commande"
    )
    item = models.ForeignKey(
        'supply.Item',
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name="Article"
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Quantité"
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Notes"
    )

    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"
        unique_together = ['order', 'item']

    def __str__(self):
        return f"{self.item.name} x{self.quantity} (Commande #{self.order.id})"
