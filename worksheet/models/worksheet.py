from django.db import models
from django.urls import reverse
from django.utils import timezone

from worksheet.managers import WorksheetManager

from .workout import Workout


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

        self.save()

        return self

    def get_duration(self):
        ended_at = timezone.now()

        if self.done:
            ended_at = self.ended_at

        duration = ended_at.replace(microsecond=0) - self.started_at.replace(microsecond=0)

        return str(duration)

    def get_status(self):
        return "done" if self.done else "in-progress"

    def get_absolute_url(self):
        return reverse("worksheet:worksheet", args=[self.date.year, self.date.month, self.date.day])

    class Meta:
        constraints = [ # noqa
            models.UniqueConstraint(
                fields=["date"], name="unique_worksheet_per_day",
            )
        ]


