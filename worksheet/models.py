from itertools import batched

from django.contrib import admin
from django.core import validators
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from .managers import ResultRelatedManager, WorksheetManager

# Create your models here.
class Exercise(models.Model):
    name = models.CharField(max_length=50)
    weight = models.BooleanField(verbose_name="Use weights?", default=False)

    @admin.display(description="Exercise")
    def __str__(self):
        return self.name

class Workout(models.Model):
    name = models.CharField(max_length=50)
    repeat = models.BooleanField(verbose_name="Repeat workout exercises?", default=False)
    exercises = models.ManyToManyField(Exercise, through="Program")

    @admin.display(description="Workout")
    def __str__(self):
        return self.name

    def get_exercises_in_order(self):
        """
        Get the list of exercises of the workout, in the order they are
        executed, which will be different than the order they are displayed in
        the case of repeat workouts.
        """
        exercises = self.exercises.filter(workout=self)

        if self.repeat:
            # TODO use something else than the ID - slug or qname?
            match self.id:
                case 1:
                    # 1, 2, 3, 4 -> 1, 2, 3, 4, 2, 1, 4, 3
                    second_round = [exercise
                                    for couple in [(second, first) for first, second in batched(exercises, 2)]
                                    for exercise in couple]
                    exercises = list(exercises) + second_round

                case 2:
                    # 1, 2, 3, 4, 5, 6 -> 1, 2, 3, 1, 2, 3, 4, 5, 6, 4, 5, 6
                    exercises = [exercise
                                 for triplet in batched(exercises, 3)
                                 for series in (triplet, triplet)
                                 for exercise in series]

        return exercises

class Program(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    def __str__(self):
        return f"Exercise #{self._order + 1}"

    class Meta:
        order_with_respect_to = "workout"

class Schedule(models.Model):
    # ISO weekdays
    # Py: datetime.now().isoweekday()
    # Pg: EXTRACT(isodow FROM now())
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7
    DAY_CHOICES = {
        MONDAY: "Monday",
        TUESDAY: "Tuesday",
        WEDNESDAY: "Wednesday",
        THURSDAY: "Thursday",
        FRIDAY: "Friday",
        SATURDAY: "Saturday",
        SUNDAY: "Sunday",
    }
    day = models.SmallIntegerField(choices=DAY_CHOICES)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.DAY_CHOICES[self.day]}: {self.workout.name}"

class Worksheet(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.PROTECT)
    done = models.BooleanField(default=False)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(blank=True, null=True)
    date = models.DateField(default=timezone.localdate)

    objects = WorksheetManager()

    def __str__(self):
        return f"{self.workout} ({self.date})"

    def close(self):
        self.done = True
        # Don't override the end date if a worksheet is closed a second time
        # (through the admin for example)
        if self.ended_at is None:
            self.ended_at = timezone.now()

        return self

    def get_status(self):
        return "done" if self.done else "in-progress"

    def get_absolute_url(self):
        return reverse("worksheet:worksheet", args=[self.date.year, self.date.month, self.date.day])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["date"], name="unique_worksheet_per_day",
            )
        ]

class Result(models.Model):
    reps = models.SmallIntegerField(validators=[validators.MinValueValidator(0, message="Number of reps cannot be negative")], null=True)
    weight = models.SmallIntegerField(validators=[validators.MinValueValidator(0, message="Used weight cannot be negative")], blank=True, null=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    worksheet = models.ForeignKey(Worksheet, on_delete=models.CASCADE)

    objects = models.Manager()
    results = ResultRelatedManager()

    def clean_fields(self, exclude=None):
        if self.weight is not None and not self.exercise.weight:
            # Prevent any validation issue if a weight is submitted for a
            # weightless exercise by simply discarding the value.
            # TODO log a warning?
            self.weight = None

        return super().clean_fields(exclude)

    def is_filled(self):
        """
        Returns false if no full results have yet been submitted for this
        exercise, true otherwise.
        """
        return self.reps is not None and (
            self.weight is not None
            or
            not self.exercise.weight and self.weight is None
        )

    def get_status(self):
        return "filled" if self.is_filled() else ''

    class Meta:
        order_with_respect_to = "worksheet"
        constraints = [
            models.CheckConstraint(condition=Q(reps__gte=0) & Q(weight__gte=0), name="reps_and_weight_positive"),
        ]
