import datetime

from django.db import models
from django.utils import timezone

class WorksheetManager(models.Manager):
    def get_active(self, before=None):
        """
        Get the list of in progress workouts, if any, before a certain date. If
        none is specified, use today.
        """
        if before is None or not isinstance(before, (datetime.datetime, datetime.date)):
            before = timezone.now().date()

        return super().get_queryset().filter(in_progress=True, date__lt=before)
