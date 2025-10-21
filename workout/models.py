from django.contrib import admin
from django.core import validators
from django.db import models

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

class Program(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    def __str__(self):
        return f"Exercise #{self._order + 1}"

    class Meta:
        order_with_respect_to = "workout"

class Schedule(models.Model):
    # ISO weekdays
    # Py: datatime.now().isoweekday()
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
    date = models.DateField(auto_now_add=True)
    in_progress = models.BooleanField(default=True)
    workout = models.ForeignKey(Workout, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.workout} ({self.date})"

class Result(models.Model):
    reps = models.SmallIntegerField(validators=[validators.MinValueValidator(0)])
    weight = models.SmallIntegerField(validators=[validators.MinValueValidator(0)], blank=True, null=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT)
    worksheet = models.ForeignKey(Worksheet, on_delete=models.CASCADE)

    class Meta:
        order_with_respect_to = "worksheet"
