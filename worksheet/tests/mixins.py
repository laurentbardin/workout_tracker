from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from worksheet.models import (
    Exercise, Program, Workout, Worksheet,
)

class ProgramSetupMixin:
    """
    This class sets up a workout with 4 associated exercises.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        exercises = Exercise.objects.bulk_create([
            Exercise(name="Exercise 1", weight=True),
            Exercise(name="Exercise 2", weight=False),
            Exercise(name="Exercise 3", weight=True),
            Exercise(name="Exercise 4", weight=False),
            Exercise(name="Exercise 5", weight=False),
        ])
        workout = Workout.objects.create(
            name="Test workout",
            repeat=False,
        )
        cls.workout = workout

        for ex in exercises:
            Program.objects.create(workout=workout, exercise=ex)

        timezone.activate(getattr(settings, "USER_TIME_ZONE", settings.TIME_ZONE))

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
