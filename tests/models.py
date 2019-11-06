import uuid

from django.db import models


class Author(models.Model):
    public_id = models.CharField(max_length=100, blank=False, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=150, blank=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        permissions = [("change_active", "Can change active author")]

