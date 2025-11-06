import datetime

from django.db import models, transaction, DatabaseError
from django.utils import timezone

class WorksheetManager(models.Manager):
    def get_active(self, before=None):
        """
        Get the list of in progress workouts, if any, before a certain date. If
        none is specified, use today.
        """
        if before is None or not isinstance(before, (datetime.datetime, datetime.date)):
            before = timezone.localdate()

        return super().get_queryset().filter(done=False, date__lt=before)

    def close(self, pk=None):
        if pk is not None:
            worksheet = super().get_queryset().get(pk=pk, done=False)
            worksheet.close().save()

    def get_or_create(self, defaults=None, **kwargs):
        try:
            with transaction.atomic():
                worksheet, created = super().get_or_create(defaults=defaults, **kwargs)

                if created:
                    worksheet.result_set(manager="results").create_all()

        except DatabaseError:
            # TODO do something useful here
            raise

        return worksheet, created

class ResultRelatedManager(models.Manager):
    def create_all(self):
        """
        Create all the result entries for the related worksheet, unless they
        already exist.
        """
        worksheet = self.instance

        if self.filter(worksheet=worksheet).count() == 0:
            results = []
            exercises = worksheet.workout.get_exercises_in_order()

            for order, exercise in enumerate(exercises):
                results.append(self.model(
                    exercise=exercise,
                    worksheet=worksheet,
                    _order=order
                ))

            self.bulk_create(results)
