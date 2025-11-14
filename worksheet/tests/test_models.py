import datetime

from django.test import TestCase

from worksheet.models import Exercise, Result, Workout, Worksheet

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

class ResultModelTests(TestCase):
    def test_result_with_weight_is_filled(self):
        exercise = Exercise(name="Exercise with weights", weight=True)

        result = Result(reps=None, weight=None, exercise=exercise)
        self.assertFalse(result.is_filled())

        result.reps = 10
        self.assertFalse(result.is_filled())

        result.weight = 10
        self.assertTrue(result.is_filled())

        result.reps = None
        self.assertFalse(result.is_filled())

    def test_result_without_weight_is_filled(self):
        exercise = Exercise(name="Exercise without weights", weight=False)

        result = Result(reps=None, weight=None, exercise=exercise)
        self.assertFalse(result.is_filled())

        result.reps = 10
        self.assertTrue(result.is_filled())

        # The following two tests use theoritically impossible results, because
        # the exercises needs no weight, but it shouldn't prevent the
        # is_filled() method from returning the correct result, as it should
        # only depend on the value of reps.
        result.weight = 10
        self.assertTrue(result.is_filled())

        result.reps = None
        self.assertFalse(result.is_filled())
