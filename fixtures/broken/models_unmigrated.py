from django.db import models


class Widget(models.Model):
    name = models.CharField(max_length=120)
    sku = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # demo 3: field with no migration — makemigrations --check fails
    colour = models.CharField(max_length=32, default="green")

    def __str__(self) -> str:
        return self.name
