import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from workout.models import (
    Exercise, Program, Workout, Worksheet, Schedule,
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
    def _create_worksheet(self, done=False):
        now = timezone.now()
        worksheet = Worksheet.objects.create(
            workout=self.workout,
            started_at=now,
            done=done
        )
        worksheet.result_set(manager="results").create_all()

        return worksheet

    def _update_worksheet(self, worksheet, *, reps, weights):
        response = self.client.post(
            reverse("workout:workout", kwargs={
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

class IndexViewTests(TestCase):
    def test_no_workout_day(self):
        """
        The index page does not offer to start a workout when none are
        scheduled for the current day.
        """
        response = self.client.get(reverse("workout:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No workout today!")

    def test_workout_day(self):
        """
        The index page offers to start a workout when one is scheduled for the
        current day.
        """
        workout = Workout.objects.create(
            name="Test workout",
            repeat=False,
        )
        today = timezone.now().isoweekday()
        Schedule.objects.create(day=today, workout=workout)

        response = self.client.get(reverse("workout:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Today's workout: Test workout")

class CurrentViewTest(ProgramSetupMixin, TestCase):
    def test_creation_when_not_scheduled(self):
        """
        It isn't possible to create a workout when none are scheduled for the
        current day.
        """
        response = self.client.get(reverse("workout:create"), follow=True)

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No workout today!")

        self.assertQuerySetEqual(Worksheet.objects.all(), [])

    def test_creation_when_scheduled(self):
        """
        When a workout is scheduled for the current day, it should be created
        alongside its Result entries, and the user should be redirected to its
        detail page.
        """
        now = timezone.now()
        weekday = now.isoweekday()
        Schedule.objects.create(day=weekday, workout=self.workout)

        response = self.client.get(reverse("workout:create"), follow=True)

        # TODO Split into two tests: one for checking creation, one for
        # checking display
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test workout")
        self.assertContains(response, "1. Exercise 1")
        self.assertContains(response, "2. Exercise 2")
        self.assertContains(response, "3. Exercise 3")
        self.assertContains(response, "4. Exercise 4")

        worksheet = Worksheet.objects.get(
            workout=self.workout,
            done=False,
        )
        self.assertEqual(worksheet.result_set.count(), 4)

class CloseViewTest(WorksheetMixin, TestCase):
    def test_can_close_in_progress_workout(self):
        """
        It's possible to close an in-progress workout.
        """
        worksheet = self._create_worksheet()

        response = self.client.post(reverse(
            "workout:close",
            kwargs={'worksheet_id': worksheet.id},
        ))
        self.assertEqual(response.status_code, 302)

        worksheet.refresh_from_db()
        self.assertTrue(worksheet.done)

    def test_closing_worksheet_is_idempotent(self):
        """
        Closing a workout twice does not modify its end date.
        """
        worksheet = self._create_worksheet()

        self.client.post(reverse(
            "workout:close",
            kwargs={'worksheet_id': worksheet.id},
        ))

        worksheet.refresh_from_db()
        ended_at = worksheet.ended_at
        self.assertIsInstance(ended_at, datetime.datetime)

        self.client.post(reverse(
            "workout:close",
            kwargs={'worksheet_id': worksheet.id},
        ))

        worksheet.refresh_from_db()
        self.assertEqual(worksheet.ended_at, ended_at)

class ResultViewTest(WorksheetMixin, TestCase):
    def test_update_results_of_closed_workout(self):
        """
        It is not possible to update the results of a closed workout.
        """
        worksheet = self._create_worksheet(done=True)
        response = self._update_worksheet(worksheet,
                                          reps=[10, 10, 10, 10],
                                          weights=[10, 10, 10, 10])

        self.assertEqual(response.status_code, 302)

        for result in worksheet.result_set.all():
            self.assertIsNone(result.reps)
            self.assertIsNone(result.weight)

    def test_update_results_of_in_progress_workout(self):
        """
        It is possible to update the results of an in-progress workout.
        """
        worksheet = self._create_worksheet()
        response = self._update_worksheet(worksheet,
                                          reps=[10, 10, 10, 10],
                                          weights=[10, '', 10, ''])

        self.assertEqual(response.status_code, 200)

        for result in worksheet.result_set.select_related('exercise').all():
            self.assertEqual(result.reps, 10)
            if result.exercise.weight:
                self.assertEqual(result.weight, 10)
            else:
                self.assertIsNone(result.weight)

    def test_update_results_with_negative_reps(self):
        """
        Updating an exercise results with a negative number of reps produces an
        error message, rejecting the whole update.
        """
        worksheet = self._create_worksheet()
        response = self._update_worksheet(worksheet,
                                          reps=[10, 10, -3, -2],
                                          weights=[10, '', 10, ''])

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Number of reps cannot be negative', 2)
        self.assertContains(response, '-3', 1)
        self.assertContains(response, '-2', 1)

        for result in worksheet.result_set.select_related('exercise').all():
            self.assertIsNone(result.reps)
            self.assertIsNone(result.weight)

    def test_update_results_with_negative_weight(self):
        """
        Updating an exercise results with a negative weight produces an error
        message, rejecting the whole update.
        """
        worksheet = self._create_worksheet()
        response = self._update_worksheet(worksheet,
                                          reps=[10, 10, 10, 10],
                                          weights=[10, '', -4, ''])

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Used weight cannot be negative', 1)
        self.assertContains(response, '-4', 1)

        for result in worksheet.result_set.select_related('exercise').all():
            self.assertIsNone(result.reps)
            self.assertIsNone(result.weight)

    def test_update_results_of_weightless_exercise_with_weight(self):
        """
        Updating an exercise results with weight when said exercise doesn't use
        weights discards the unexpected values while still updating those that
        can.
        """
        worksheet = self._create_worksheet()
        response = self._update_worksheet(worksheet,
                                          reps=[10, 10, 10, 10],
                                          weights=[10, '', 10, ''])
        self.assertEqual(response.status_code, 200)

        response = self._update_worksheet(worksheet,
                                          reps=[10, 10, 10, 10],
                                          weights=[200, 100, 300, -400])

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Used weight cannot be negative', 0)
        # TODO '100' could be found occasionally in the CSRF token, try and
        # find a better sentinel value
        self.assertContains(response, '100', 0)
        self.assertContains(response, '-400', 0)

        for result in worksheet.result_set.select_related('exercise').all():
            self.assertEqual(result.reps, 10)
            if not result.exercise.weight:
                self.assertIsNone(result.weight)
            else:
                self.assertIn(result.weight, [200, 300])

    def test_worksheet_show_results_from_previous_same_workout(self):
        pass
