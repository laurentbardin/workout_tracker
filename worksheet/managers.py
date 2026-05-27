import datetime

from django.db import models, transaction, DatabaseError
from django.db.models import Count
from django.utils import timezone

class WorksheetManager(models.Manager):
    def get_active(self, before=None):
        """
        Get the list of in progress workouts, if any, before a certain date
        (inclusive). If none is specified, use today.
        """
        if before is None or not isinstance(before, (datetime.datetime, datetime.date)):
            before = timezone.localdate()

        return super().get_queryset().filter(done=False, date__lte=before)

    def close(self, pk=None):
        if pk is not None:
            worksheet = super().get_queryset().get(pk=pk, done=False)
            worksheet.close()

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

    def get_with_results(self, date):
        worksheet = None
        results = None

        try:
            worksheet = self.select_related('workout').annotate(
                total_exercise=Count("result")
            ).annotate(
                done_exercise=Count("result__reps")
            ).get(date=date)

            results = self._get_results(worksheet)
            self._get_previous_results(worksheet, results)
        except self.model.DoesNotExist:
            # TODO logging
            pass

        return worksheet, results

    def _get_results(self, worksheet):
        qs = worksheet.result_set.select_related('exercise')

        if worksheet.workout.repeat:
            qs = qs.order_by(
                "exercise__program",
                "_order"
            ).filter(
                exercise__workout=worksheet.workout
            )

        return qs.all()

    def _get_previous_results(self, worksheet, results):
        """
        Fetch the results of the same previous workout to display and
        compare, if any.
        """
        # This is only relevant or useful if a workout is in progress
        if not worksheet.done:
            previous_worksheet = self.filter(
                workout=worksheet.workout,
                date__lt=worksheet.date,
                done=True,
            ).order_by("-date").first()

            if previous_worksheet is not None:
                for res, prev in zip(results,
                                     self._get_results(previous_worksheet)):
                    res.previous = prev

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
