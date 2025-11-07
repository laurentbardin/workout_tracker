import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from worksheet.models import (
    Worksheet, Schedule,
)
from worksheet.tests.mixins import ProgramSetupMixin, WorksheetMixin

class IndexViewTests(WorksheetMixin, TestCase):
    def test_no_workout_day(self):
        """
        The index page does not offer to start a workout when none are
        scheduled for the current day.
        """
        response = self.client.get(reverse("worksheet:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No workout today!")

    def test_workout_day(self):
        """
        The index page offers to start a workout when one is scheduled for the
        current day.
        """
        today = timezone.localtime().isoweekday()
        Schedule.objects.create(day=today, workout=self.workout)

        response = self.client.get(reverse("worksheet:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Today's Workout")
        self.assertContains(response, "Test workout")
        self.assertContains(response, "Start")

    def test_workout_already_started(self):
        """
        The index page offers to continue the current workout if it's already
        been started.
        """
        today = timezone.localtime().isoweekday()
        Schedule.objects.create(day=today, workout=self.workout)

        worksheet = self._create_worksheet()

        response = self.client.get(reverse("worksheet:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Today's Workout")
        self.assertContains(response, "Test workout")
        self.assertContains(response, "Continue")
        self.assertContains(response, worksheet.get_absolute_url())

    def test_active_worksheet_are_displayed(self):
        """
        The index page doesn't offer to create a worksheet if any active one
        already exists.
        """
        today = timezone.localtime().isoweekday()
        Schedule.objects.create(day=today, workout=self.workout)

        worksheet = self._create_worksheet(
            started_at=timezone.now() - datetime.timedelta(days=1),
        )

        response = self.client.get(reverse('worksheet:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Found some workouts still in progress")
        self.assertContains(response, worksheet.get_absolute_url())

class CurrentViewTest(ProgramSetupMixin, TestCase):
    def test_creation_when_not_scheduled(self):
        """
        It isn't possible to create a workout when none are scheduled for the
        current day.
        """
        response = self.client.post(reverse("worksheet:create"), follow=True)

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
        now = timezone.localtime()
        weekday = now.isoweekday()
        date = now.date()
        Schedule.objects.create(day=weekday, workout=self.workout)

        response = self.client.post(reverse("worksheet:create"), follow=True)

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
            date=date,
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
            "worksheet:close",
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
            "worksheet:close",
            kwargs={'worksheet_id': worksheet.id},
        ))

        worksheet.refresh_from_db()
        ended_at = worksheet.ended_at
        self.assertIsInstance(ended_at, datetime.datetime)

        self.client.post(reverse(
            "worksheet:close",
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
