from django.contrib import admin
from django.db import models


class Exercise(models.Model):
    name = models.CharField(max_length=50)
    weight = models.BooleanField(verbose_name="Use weights?", default=False)

    @admin.display(description="Exercise")
    def __str__(self):
        return self.name
