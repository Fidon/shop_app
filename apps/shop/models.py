from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import CustomUser


def dtime():
    return timezone.now() + timedelta(hours=3)

# Inventory/product model
class Product(models.Model):
    id = models.AutoField(primary_key=True)
    regdate = models.DateTimeField(default=dtime)
    names = models.CharField(max_length=255)
    qty = models.FloatField()
    price = models.FloatField()
    expiry = models.DateField(null=True, default=None)
    comment = models.TextField(null=True, default=None)
    deleted = models.BooleanField(default = False)
    addedBy = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='pro_registrar')
    lastEdited = models.DateTimeField(null=True, default=None)
    editedBy = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='pro_editor', null=True, default=None)
    objects = models.Manager()
    
    def __str__(self):
        return str(self.names)