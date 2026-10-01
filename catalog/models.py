from django.db import models


class Widget(models.Model):
    name = models.CharField(max_length=120)
    sku = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name
