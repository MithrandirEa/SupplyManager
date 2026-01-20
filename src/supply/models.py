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

    def __str__(self):
        return self.name
