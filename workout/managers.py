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

        return super().get_queryset().filter(done=False, date__lt=before)

    def close(self, pk=None):
        if pk is not None:
            worksheet = super().get_queryset().get(pk=pk, done=False)
            worksheet.close().save()
