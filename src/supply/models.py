from django.db import models


class ItemsCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        ItemsCategory,
        on_delete=models.CASCADE,
        related_name='items'
    )
    suppliers = models.ManyToManyField(
        'supplier.Supplier',
        related_name='items',
        blank=True
    )
    total_quantity = models.PositiveIntegerField(default=0)
    outside_quantity = models.PositiveIntegerField(default=0)
    available_quantity = models.PositiveIntegerField(default=0)
    excess_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Quantité excédentaire"
    )
    information = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stock_entry_date = models.DateField(blank=True, null=True)
    last_inventory_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Quantité lors du dernier inventaire"
    )
    last_inventory_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date du dernier inventaire"
    )

    @property
    def missing_quantity(self):
        """Calcule la quantité manquante.
        
        Formule: total - (disponible + chez fournisseur)
        """
        result = self.total_quantity - (
            self.available_quantity + self.outside_quantity
        )
        return max(0, result)  # Ne peut pas être négatif

    @property
    def actual_loss_quantity(self):
        """Calcule la perte réelle par rapport au dernier inventaire"""
        if self.last_inventory_quantity == 0:
            return 0
        result = self.total_quantity - self.last_inventory_quantity
        return result if result < 0 else 0  # Retourne valeur négative si perte

    def __str__(self):
        return self.name
