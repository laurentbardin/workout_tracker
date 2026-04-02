import datetime
import html
import math
import random

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from worksheet.models import (
    Worksheet, Result, Schedule,
)
from worksheet.tests.base import WorksheetTestCase
from worksheet.tests.mixins import ProgramSetupMixin, WorksheetMixin

class IndexViewTests(WorksheetMixin, TestCase):
    def test_index_display_current_month(self):
        """
        The index page displays a calendar for the current month
        """
        today = timezone.localdate()

        response = self.client.get(reverse('worksheet:index'))
        self.assertContains(response, f"Workout calendar for {today.strftime('%B %Y')}")
        self.assertContains(response, 'class="today"', 1)

    def test_workout_day(self):
        """
        The index page offers to start a workout when one is scheduled for the
        current day.
        """
        today = timezone.localtime().isoweekday()
        Schedule.objects.create(day=today, workout=self.workout)

        response = self.client.get(reverse("worksheet:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test workout")
        self.assertContains(response, '<button title="Start today\'s workout" name="workout">' + self.workout.name + '</button>', 1)

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
        self.assertContains(response, "Test workout")
        self.assertContains(response, worksheet.get_absolute_url())
        self.assertNotContains(response, '<button type="submit">' + self.workout.name + '</button>')

    def test_completed_worksheet(self):
        """
        The index page offers to show today's worksheet if it's already been
        completed.
        """
        today = timezone.localtime().isoweekday()
        Schedule.objects.create(day=today, workout=self.workout)

        worksheet = self._create_worksheet(done=True)

        response = self.client.get(reverse("worksheet:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test workout")
        self.assertContains(response, worksheet.get_absolute_url())
        self.assertNotContains(response, '<button type="submit">' + self.workout.name + '</button>')

    def test_active_worksheet_are_displayed(self):
        """
        The index page doesn't offer to create a worksheet if any active one
        already exists.
        """
        today = timezone.localtime().isoweekday()
        Schedule.objects.create(day=today, workout=self.workout)

        worksheet = self._create_worksheet(
            started_at=timezone.now() - datetime.timedelta(days=30),
        )

        response = self.client.get(reverse('worksheet:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, worksheet.get_absolute_url())
        self.assertNotContains(response, '<button type="submit">' + self.workout.name + '</button>')

class CalendarViewTest(WorksheetMixin, TestCase):
    def test_calendar_displays_current_month(self):
        today = timezone.localdate()

        response = self.client.get(reverse('worksheet:calendar', args=[ today.year, today.month ]))
        self.assertContains(response, '<!doctype html>')
        self.assertContains(response, f"Workout calendar for {today.strftime('%B %Y')}")
        self.assertContains(response, 'class="today"', 1)

    def test_calendar_displays_arbitrary_past_month(self):
        date = datetime.date(timezone.localdate().year + random.randint(-10, -1),
                             random.randint(1, 12),
                             1)

        response = self.client.get(reverse('worksheet:calendar', args=[ date.year, date.month ]))
        self.assertContains(response, '<!doctype html>')
        self.assertContains(response, f"Workout calendar for {date.strftime('%B %Y')}")
        self.assertNotContains(response, 'class="today"')

    def test_calendar_displays_arbitrary_future_month(self):
        date = datetime.date(timezone.localdate().year + random.randint(1, 10),
                             random.randint(1, 12),
                             1)

        response = self.client.get(reverse('worksheet:calendar', args=[ date.year, date.month ]))
        self.assertContains(response, '<!doctype html>')
        self.assertContains(response, f"Workout calendar for {date.strftime('%B %Y')}")
        self.assertNotContains(response, 'class="today"')

    def test_calendar_responds_to_htmx_requests(self):
        today = timezone.localdate()

        response = self.client.get(reverse('worksheet:calendar', args=[ today.year, today.month ]), headers={'HX-Request': 1})
        self.assertNotContains(response, '<!doctype html>')
        self.assertContains(response, f"Workout calendar for {today.strftime('%B %Y')}")
        self.assertContains(response, 'class="today"', 1)

    def test_calendar_displays_workout_completion_status(self):
        worksheet = self._create_worksheet()
        today = timezone.localdate()

        response = self.client.get(reverse('worksheet:calendar', args=[ today.year, today.month ]))
        self.assertContains(response, '(0 / 5)')

        self._update_worksheet_result(worksheet, result_id=1, field='reps', value=10)
        self._update_worksheet_result(worksheet, result_id=2, field='reps', value=10)
        self._update_worksheet_result(worksheet, result_id=2, field='weight', value=10)

        response = self.client.get(reverse('worksheet:calendar', args=[ today.year, today.month ]))
        self.assertContains(response, '(2 / 5)')

class CreateViewTest(ProgramSetupMixin, TestCase):
    def test_creation_when_not_scheduled(self):
        """
        It isn't possible to create a workout when none are scheduled for the
        current day.
        """
        response = self.client.post(reverse("worksheet:create"), follow=True)

        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'worksheet/index.html')

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
        self.assertContains(response, "5. Exercise 5")

        worksheet = Worksheet.objects.get(
            workout=self.workout,
            date=date,
            done=False,
        )
        self.assertEqual(worksheet.result_set.count(), 5)

class WorksheetViewTest(WorksheetMixin, WorksheetTestCase):
    def test_non_existing_worksheet(self):
        """
        Display a simple message when a worksheet doesn't exist
        """
        now = timezone.localtime().date()
        date = datetime.date(now.year, now.month, now.day)
        response = self.client.get(reverse(
            "worksheet:worksheet",
            args=[ date.year, date.month, date.day ]
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No workout for")
        self.assertContains(response, "Go back")
        self.assertContains(response, reverse('worksheet:index'))

    def test_duration_on_completed_worksheet(self):
        """
        Display the duration of completed worksheets
        """
        ended_at = timezone.localtime()
        started_at = ended_at - datetime.timedelta(minutes=37, seconds=42)

        worksheet = self._create_worksheet(started_at=started_at, done=True)
        worksheet.ended_at = ended_at
        worksheet.save()

        response = self.client.get(reverse(
            "worksheet:worksheet",
            args=[ worksheet.date.year, worksheet.date.month, worksheet.date.day ]
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test workout")
        self.assertContains(response, "Completed in <strong>0:37:42</strong>")

    def test_note_on_previous_result(self):
        """
        Display an icon near previous results which have a note attached
        """
        # Create a previous worksheet first
        today = timezone.localtime()
        yesterday = today - datetime.timedelta(days=1)
        worksheet = self._create_worksheet(started_at=yesterday, done=True)
        self._update_worksheet_result(worksheet, 1, 'note', 'This is an old note')

        # Create the current worksheet and check its display
        worksheet = self._create_worksheet(started_at=today)
        response = self.client.get(reverse(
            "worksheet:worksheet",
            args=[ worksheet.date.year, worksheet.date.month, worksheet.date.day ]
        ))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'note-add.svg', 5)
        self.assertContains(response, 'note-view.svg', 1)
        self.assertContains(response, 'title="This is an old note"', 1)

    def test_note_on_closed_worksheet(self):
        """
        Display an icon near results which have a note attached
        """
        yesterday = timezone.localtime() - datetime.timedelta(days=1)
        worksheet = self._create_worksheet(started_at=yesterday, done=True)
        worksheet.ended_at = yesterday + datetime.timedelta(minutes=30)
        worksheet.save()

        self._update_worksheet_result(worksheet, 1, 'note', 'This is an old note')
        self._update_worksheet_result(worksheet, 2, 'note', 'This is another old note')

        response = self.client.get(reverse(
            "worksheet:worksheet",
            args=[ worksheet.date.year, worksheet.date.month, worksheet.date.day ]
        ))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'note-add.svg', 0)
        self.assertContains(response, 'note-view.svg', 2)
        self.assertContains(response, 'title="This is an old note"', 1)
        self.assertContains(response, 'title="This is another old note"', 1)

    def test_completion_meter_is_displayed(self):
        """
        Display a progression meter on the active worksheet page
        """
        worksheet = self._create_worksheet(done=True)
        response = self.client.get(reverse(
            "worksheet:worksheet",
            args=[ worksheet.date.year, worksheet.date.month, worksheet.date.day ]
        ))

        expected_max = expected_optimum = worksheet.result_set.count()
        expected_low = math.ceil(expected_max / 2)
        expected_high = expected_max - 1

        self.assertContains(response, f'<meter id="worksheet-progress" min="0" '
                            f'max="{expected_max}" low="{expected_low}" '
                            f'high="{expected_high}" value="0" optimum="{expected_optimum}"></meter>')

    def test_completion_meter_is_reflecting_progress(self):
        worksheet = self._create_worksheet(done=True)
        self._update_worksheet_result(worksheet, 1, 'reps', '10')

        response = self.client.get(reverse(
            "worksheet:worksheet",
            args=[ worksheet.date.year, worksheet.date.month, worksheet.date.day ]
        ))

        expected_max = expected_optimum = worksheet.result_set.count()
        expected_low = math.ceil(expected_max / 2)
        expected_high = expected_max - 1
        expected_value = 1

        self.assertContains(response, f'<meter id="worksheet-progress" '
                            f'min="0" max="{expected_max}" '
                            f'low="{expected_low}" high="{expected_high}" '
                            f'value="{expected_value}" optimum="{expected_optimum}"></meter>')

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

class ResultActionTest(WorksheetMixin, WorksheetTestCase):
    def test_update_result(self):
        worksheet = self._create_worksheet()
        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='reps',
                                                 value=10)
        self.assertEqual(response.content, b'')
        self.assertHeaderJSONEqual(
            response,
            'hx-trigger-after-settle',
            {
                'updateSuccess': {
                    'meter': {
                        'value': 1,
                    },
                },
            },
        )

        result = Result.objects.get(pk=1)
        self.assertEqual(result.reps, 10)
        self.assertIsNone(result.weight)
        self.assertIsNone(result.note)

        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='weight',
                                                 value=6)
        self.assertEqual(response.content, b'')
        self.assertHeaderJSONEqual(
            response,
            'hx-trigger-after-settle',
            {
                'updateSuccess': {
                    'meter': {
                        'value': None,
                    },
                },
            },
        )

        result.refresh_from_db()
        self.assertEqual(result.reps, 10)
        self.assertEqual(result.weight, 6)
        self.assertIsNone(result.note)

    def test_update_result_without_reps(self):
        worksheet = self._create_worksheet()
        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='reps',
                                                 value=None)
        self.assertContains(response, 'Missing number of reps')
        self.assertHasNotHeader(response, 'hx-trigger-after-settle')

        result = Result.objects.get(pk=1)
        self.assertIsNone(result.reps)
        self.assertIsNone(result.weight)
        self.assertIsNone(result.note)

    def test_update_result_with_negative_values(self):
        worksheet = self._create_worksheet()
        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='reps',
                                                 value=-2)
        self.assertContains(response, html.escape("Invalid value -2 for field 'reps'"))
        self.assertHeaderEqual(response, 'hx-trigger-after-settle', 'updateError')

        result = Result.objects.get(pk=1)
        self.assertIsNone(result.reps)
        self.assertIsNone(result.weight)
        self.assertIsNone(result.note)

        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='weight',
                                                 value=-3)
        self.assertContains(response, html.escape("Invalid value -3 for field 'weight'"))
        self.assertHeaderEqual(response, 'hx-trigger-after-settle', 'updateError')

        result.refresh_from_db()
        self.assertIsNone(result.reps)
        self.assertIsNone(result.weight)
        self.assertIsNone(result.note)

    def test_update_result_with_invalid_values(self):
        worksheet = self._create_worksheet()
        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='reps',
                                                 value="foo")

        self.assertContains(response, html.escape("Field 'reps' expected a number but got 'foo'"))
        self.assertHeaderEqual(response, 'hx-trigger-after-settle', 'updateError')

        result = Result.objects.get(pk=1)
        self.assertIsNone(result.reps)
        self.assertIsNone(result.weight)
        self.assertIsNone(result.note)

        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='weight',
                                                 value="bar")

        self.assertContains(response, html.escape("Field 'weight' expected a number but got 'bar'"))
        self.assertHeaderEqual(response, 'hx-trigger-after-settle', 'updateError')

        result.refresh_from_db()
        self.assertIsNone(result.reps)
        self.assertIsNone(result.weight)
        self.assertIsNone(result.note)

    def test_update_weightless_exercise_with_weight(self):
        worksheet = self._create_worksheet()
        response = self._update_worksheet_result(worksheet,
                                                 result_id=2,
                                                 field='weight',
                                                 value=10)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(response.content), 0)
        self.assertHasNotHeader(response, 'hx-trigger-after-settle')

        result = Result.objects.get(pk=2)
        self.assertIsNone(result.reps)
        self.assertIsNone(result.weight)
        self.assertIsNone(result.note)

    def test_update_inexistant_result(self):
        worksheet = self._create_worksheet()
        response = self._update_worksheet_result(worksheet,
                                                 result_id=42,
                                                 field='reps',
                                                 value=10)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(response.content), 0)
        self.assertHasNotHeader(response, 'hx-trigger-after-settle')

        response = self._update_worksheet_result(worksheet,
                                                 result_id=42,
                                                 field='weight',
                                                 value=10)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(response.content), 0)
        self.assertHasNotHeader(response, 'hx-trigger-after-settle')

    def test_add_modify_remove_note_result(self):
        worksheet = self._create_worksheet()
        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='note',
                                                 value='This is a note')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="noteForm"')
        self.assertNotContains(response, '"errorlist"')
        self.assertContains(response, 'data-note="This is a note"')
        self.assertContains(response, '"result-action-1"')
        self.assertContains(response, 'note-view.svg')
        self.assertHeaderJSONEqual(response, "HX-Trigger", { 'noteAdded': 'Note added' })

        result = Result.objects.get(pk=1)
        self.assertIsNone(result.reps)
        self.assertIsNone(result.weight)
        self.assertEqual(result.note, 'This is a note')

        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='note',
                                                 value='This is a new note')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="noteForm"')
        self.assertNotContains(response, '"errorlist"')
        self.assertContains(response, 'data-note="This is a new note"')
        self.assertContains(response, '"result-action-1"')
        self.assertContains(response, 'note-view.svg')
        self.assertHeaderJSONEqual(response, "HX-Trigger", { 'noteAdded': 'Note added' })

        result = Result.objects.get(pk=1)
        self.assertIsNone(result.reps)
        self.assertIsNone(result.weight)
        self.assertEqual(result.note, 'This is a new note')

        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='note',
                                                 value='')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="noteForm"')
        self.assertNotContains(response, '"errorlist"')
        self.assertContains(response, 'data-note=""')
        self.assertContains(response, '"result-action-1"')
        self.assertContains(response, 'note-add.svg')
        self.assertHeaderJSONEqual(response, "HX-Trigger", { 'noteDeleted': 'Note deleted' })

        result = Result.objects.get(pk=1)
        self.assertIsNone(result.reps)
        self.assertIsNone(result.weight)
        self.assertIsNone(result.note)

    def test_note_is_rejected_if_too_long(self):
        worksheet = self._create_worksheet()
        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='note',
                                                 value='abc' * 70)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="noteForm"')
        self.assertContains(response, '"errorlist"')
        self.assertContains(response, 'Ensure this value has at most 200 characters (it has 210).')
        self.assertHasNotHeader(response, "HX-Trigger")

        self.assertNotContains(response, 'data-note')
        self.assertNotContains(response, '"result-action-1"')
        self.assertNotContains(response, 'note-view.svg')

        result = Result.objects.get(pk=1)
        self.assertIsNone(result.reps)
        self.assertIsNone(result.weight)
        self.assertIsNone(result.note)

    def test_update_unknown_field(self):
        worksheet = self._create_worksheet()
        response = self._update_worksheet_result(worksheet,
                                                 result_id=1,
                                                 field='foobar',
                                                 value=10)
        self.assertEqual(response.status_code, 404)
        self.assertHasNotHeader(response, "HX-Trigger-After-Settle")

        result = Result.objects.get(pk=1)
        self.assertIsNone(result.reps)
        self.assertIsNone(result.weight)
