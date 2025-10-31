import datetime

from django.test import TestCase
from django.utils import timezone

from workout.models import Exercise, Program, Workout, Worksheet

class WorksheetManagerTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        exercises = Exercise.objects.bulk_create([
            Exercise(name="Exercise 1"),
            Exercise(name="Exercise 2"),
        ])
        workout = Workout.objects.create(name="Test workout")
        cls.workout = workout

        for ex in exercises:
            Program.objects.create(workout=workout, exercise=ex)

    def test_no_previously_active_worksheets(self):
        worksheet = self._create_worksheet()

        self.assertEqual(Worksheet.objects.count(), 1)
        self.assertQuerySetEqual(
            Worksheet.objects.get_active(before=worksheet.started_at.date()),
            []
        )

    def test_previously_active_worksheets(self):
        now = timezone.now()
        self._create_worksheet(started_at=now)
        self._create_worksheet(started_at=now + datetime.timedelta(days=1))
        self._create_worksheet(started_at=now - datetime.timedelta(days=1))
        self._create_worksheet(started_at=now - datetime.timedelta(days=2))

        self.assertEqual(Worksheet.objects.count(), 4)
        self.assertEqual(
            Worksheet.objects.get_active(before=now).count(),
            2
        )

    def _create_worksheet(self, started_at=None, done=False):
        if started_at is None:
            started_at = timezone.now()

        worksheet = Worksheet.objects.create(
            workout=self.workout,
            started_at=started_at,
            done=done
        )

        return worksheet
