from django.db import models

from .exercise import Exercise
from .workout import Workout


class Program(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    def __str__(self):
        return f"Exercise #{self._order + 1}"

    class Meta:
        order_with_respect_to = "workout"
