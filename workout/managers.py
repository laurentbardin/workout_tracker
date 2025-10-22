import datetime

from django.db import models
from django.utils import timezone

class WorksheetManager(models.Manager):
    def get_active(self, date=None):
        """
        Get the list of in progress workouts, if any, before a certain date. If
        none is specified, use today.
        """
        if date is None or not isinstance(date, (datetime.datetime, datetime.date)):
            date = timezone.now().date()

        return super().get_queryset().filter(in_progress=True, date__lt=date)
