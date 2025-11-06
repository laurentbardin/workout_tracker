import datetime

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from worksheet.models import Exercise, Program, Workout, Worksheet

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

        timezone.activate(getattr(settings, "CURRENT_TIME_ZONE", settings.TIME_ZONE))

    def test_no_previously_active_worksheets(self):
        worksheet = self._create_worksheet()

        self.assertEqual(Worksheet.objects.count(), 1)
        self.assertQuerySetEqual(
            Worksheet.objects.get_active(before=worksheet.started_at.date()),
            []
        )

    def test_previously_active_worksheets(self):
        now = timezone.localtime()
        self._create_worksheet(started_at=now)
        self._create_worksheet(started_at=now + datetime.timedelta(days=1))
        self._create_worksheet(started_at=now - datetime.timedelta(days=1))
        self._create_worksheet(started_at=now - datetime.timedelta(days=2))

        self.assertEqual(Worksheet.objects.count(), 4)
        self.assertEqual(
            Worksheet.objects.get_active().count(),
            2
        )

    def _create_worksheet(self, started_at=None, done=False):
        fields = {
            'workout': self.workout,
            'done': done,
        }

        if started_at is None:
            fields['date'] = timezone.localdate()
        else:
            fields.update({
                'started_at': started_at,
                'date': timezone.localdate(started_at),
            })

        worksheet = Worksheet.objects.create(**fields)

        return worksheet
