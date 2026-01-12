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
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        workout = Workout(name="Test Workout")
        cls.worksheet = Worksheet(workout=workout)

    def test_result_with_weight_status(self):
        exercise = Exercise(name="Exercise with weights", weight=True)

        result = Result(reps=None, weight=None, exercise=exercise, worksheet=self.worksheet)
        self.assertEqual(result.weight_status(), '')

        result.reps = 10
        self.assertEqual(result.weight_status(), '')

        result.weight = 10
        self.assertEqual(result.weight_status(), 'success')

        result.reps = None
        self.assertEqual(result.weight_status(), 'success')

    def test_result_without_weight_status(self):
        exercise = Exercise(name="Exercise without weights", weight=False)

        result = Result(reps=None, weight=None, exercise=exercise, worksheet=self.worksheet)
        self.assertEqual(result.weight_status(), '')

        result.reps = 10
        self.assertEqual(result.weight_status(), '')

        result.weight = 10
        self.assertEqual(result.weight_status(), '')

        result.reps = None
        self.assertEqual(result.weight_status(), '')

    def test_result_reps_status(self):
        exercise = Exercise(name="Exercise")

        result = Result(reps=None, weight=None, exercise=exercise, worksheet=self.worksheet)
        self.assertEqual(result.reps_status(), '')

        result.reps = 10
        self.assertEqual(result.reps_status(), 'success')

        result.weight = 10
        self.assertEqual(result.reps_status(), 'success')

        result.reps = None
        self.assertEqual(result.reps_status(), '')

    def test_results_status_with_worksheet_done(self):
        exercise = Exercise(name="Exercise with weights", weight = True)
        self.worksheet.done = True

        result = Result(reps=None, weight=None, exercise=exercise, worksheet=self.worksheet)
        self.assertEqual(result.weight_status(), '')
        self.assertEqual(result.reps_status(), '')

        result.reps = 10
        self.assertEqual(result.weight_status(), '')
        self.assertEqual(result.reps_status(), '')

        result.weight = 10
        self.assertEqual(result.weight_status(), '')
        self.assertEqual(result.reps_status(), '')

        result.reps = None
        self.assertEqual(result.weight_status(), '')
        self.assertEqual(result.reps_status(), '')
