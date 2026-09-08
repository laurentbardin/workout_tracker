from django.core import validators
from django.db import models
from django.db.models import Q

from worksheet.managers import ResultRelatedManager

from .exercise import Exercise
from .worksheet import Worksheet


class Result(models.Model):

    reps = models.SmallIntegerField(validators=[validators.MinValueValidator(0, message="Number of reps cannot be negative")], null=True)
    weight = models.SmallIntegerField(validators=[validators.MinValueValidator(0, message="Used weight cannot be negative")], blank=True, null=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    worksheet = models.ForeignKey(Worksheet, on_delete=models.CASCADE)
    note = models.CharField(max_length=200, null=True, blank=True)

    objects = models.Manager()
    results = ResultRelatedManager()

    def reps_status(self):
        return "success" if not self.worksheet.done and self.reps is not None else ''

    def weight_status(self):
        return "success" if not self.worksheet.done and self.exercise.weight and self.weight is not None else ''

    class Meta:
        order_with_respect_to = "worksheet"
        constraints = [ # noqa
            models.CheckConstraint(condition=Q(reps__gte=0) & Q(weight__gte=0), name="reps_and_weight_positive"),
        ]

