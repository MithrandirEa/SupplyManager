from django.db import models



class Supplier(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    other_details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    associated_items = models.ManyToManyField('supply.Item', related_name='suppliers', blank=True)

    def __str__(self):
        return self.name
