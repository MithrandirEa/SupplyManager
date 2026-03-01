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

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['name']
        indexes = [
            models.Index(fields=['available_quantity'], name='item_avail_qty_idx'),
            models.Index(fields=['outside_quantity'], name='item_out_qty_idx'),
            models.Index(fields=['excess_quantity'], name='item_excess_qty_idx'),
            models.Index(fields=['is_available'], name='item_is_avail_idx'),
            models.Index(fields=['category', 'name'], name='item_cat_name_idx'),
            models.Index(fields=['-created_at'], name='item_created_idx'),
        ]

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


class Inventory(models.Model):
    """Instantané d'inventaire complet à une date donnée."""
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='inventories'
    )
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = "Inventaire"
        verbose_name_plural = "Inventaires"
        ordering = ['-created_at']

    def __str__(self):
        return f"Inventaire du {self.created_at.strftime('%d/%m/%Y %H:%M')}"


class InventoryEntry(models.Model):
    """Ligne d'un inventaire : quantité comptée pour un article donné."""
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='inventory_entries'
    )
    counted_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Quantité comptée sur site lors de l'inventaire"
    )
    outside_quantity_snapshot = models.PositiveIntegerField(
        default=0,
        help_text="Quantité chez le fournisseur au moment de l'inventaire"
    )

    class Meta:
        verbose_name = "Entrée d'inventaire"
        verbose_name_plural = "Entrées d'inventaire"
        unique_together = [['inventory', 'item']]

    @property
    def total_counted(self):
        return self.counted_quantity + self.outside_quantity_snapshot

    def __str__(self):
        return f"{self.item.name} : {self.counted_quantity} (+ {self.outside_quantity_snapshot} fournisseur)"
