from django.db import models

from worksheet.models import Workout

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
