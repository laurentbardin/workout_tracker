from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from worksheet.models import (
    Exercise,
    Workout,
    Worksheet,
)


class ProgramSetupMixin:
    """
    This class sets up a workout with 5 associated exercises.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.workout = cls._create_workout()

        timezone.activate(getattr(settings, "USER_TIME_ZONE", settings.TIME_ZONE))

    @classmethod
    def _create_workout(cls, name="Default workout"):
        workout = Workout.objects.create(
            name=name,
            repeat=False,
        )

        cls._create_exercises(workout, 5)

        return workout

    @classmethod
    def _create_exercises(cls, workout, n):
        exercises = []
        for i in range(n):
            exercises.append(Exercise(name=f"{workout.name} - Exercise {i+1}", weight=not i%2))

        workout.exercises.set(Exercise.objects.bulk_create(exercises))

class WorksheetMixin(ProgramSetupMixin):
    """
    This class contains facilities to create and update a worksheet associated
    with the workout created during setup.
    """
    def _create_worksheet(self, started_at=None, done=False):
        fields = {
            'workout': self.workout,
        }

        if started_at is None:
            started_at = timezone.localtime()

        fields.update({
            'started_at': started_at,
            'date': timezone.localdate(started_at),
        })

        worksheet = Worksheet.objects.create(**fields)
        worksheet.result_set(manager="results").create_all()

        if done:
            worksheet.close()

        return worksheet

    def _update_worksheet_result(self, worksheet, result_id, field, value):
        route_args = {
            'worksheet_id': worksheet.id,
            'result_id': result_id,
        }
        data = {
            field: str(value),
        } if value is not None else {}

        if field == 'note':
            route = 'worksheet:note'
        else:
            route = 'worksheet:result'
            route_args['field'] = field

        response = self.client.post(
            reverse(route, kwargs=route_args), data
        )

        return response
