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
        ])
        workout = Workout.objects.create(
            name="Test workout",
            repeat=False,
        )
        cls.workout = workout

        for ex in exercises:
            Program.objects.create(workout=workout, exercise=ex)

class WorksheetMixin(ProgramSetupMixin):
    """
    This class contains facilities to create and update a worksheet associated
    with the workout created during setup.
    """
    def _create_worksheet(self, done=False, started_at=None):
        if started_at is None:
            started_at = timezone.now()

        worksheet = Worksheet.objects.create(
            workout=self.workout,
            started_at=started_at,
            done=done
        )
        worksheet.result_set(manager="results").create_all()

        return worksheet

    def _update_worksheet(self, worksheet, *, reps, weights):
        response = self.client.post(
            reverse("worksheet:worksheet", kwargs={
                'year': worksheet.date.year,
                'month': worksheet.date.month,
                'day': worksheet.date.day,
            }),
            {
                'result': [str(result.id) for result in worksheet.result_set.all()],
                'reps': [str(value) for value in reps],
                'weight': [str(value) for value in weights],
            }
        )

        return response
