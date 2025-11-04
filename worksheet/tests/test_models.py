import datetime

from django.test import TestCase

from worksheet.models import Workout, Worksheet

class WorkoutModelTests(TestCase):
    def test_close_worksheet(self):
        """
        Closing a worksheet should set the ended_at field. Closing it a second
        time should not modify that field further.
        """
        workout = Workout(name="Test Workout")
        worksheet = Worksheet(workout=workout)

        self.assertIs(worksheet.done, False)
        self.assertIsNone(worksheet.ended_at)

        worksheet.close()
        self.assertIs(worksheet.done, True)
        self.assertIsInstance(worksheet.ended_at, datetime.datetime)

        ended_at = worksheet.ended_at
        worksheet.close()
        self.assertIs(worksheet.done, True)
        self.assertEqual(worksheet.ended_at, ended_at)
