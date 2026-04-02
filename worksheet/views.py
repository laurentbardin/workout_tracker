import calendar
import datetime
import json
import math

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View

from .models import Result, Schedule, Workout, Worksheet
from .forms import ResultNoteForm

class IndexView(TemplateView):
    """
    The index displays a calendar view of the current month with past and
    upcoming workouts. The current day is highlighted, and if it contains a
    scheduled workout, a button will be available to start it.
    """
    template_name = 'worksheet/index.html'

    year = None
    month = None

    def render_to_response(self, context, **response_kwargs):
        self._get_calendar(context)

        return super().render_to_response(context, **response_kwargs)

    def _get_calendar(self, context):
        today = timezone.localdate()
        cal = calendar.Calendar()

        if self.year is None or self.month is None:
            (self.year, self.month) = (today.year, today.month)
        weeks = list(cal.monthdatescalendar(self.year, self.month))

        worksheets = {
            worksheet.date: worksheet
            for worksheet in Worksheet.objects.filter(
                # weeks is a list of list of datetime.date objects, so we want
                # worksheets from the first day of the first week to the last
                # day of the last week (inclusive)
                date__range=(weeks[0][0], weeks[-1][-1])
            ).annotate(
                # Add the total number of exercises...
                total_exercise=Count("result")
            ).annotate(
                # ... and the number of completed exercises
                done_exercise=Count("result__reps")
            ).select_related('workout').all()
        }

        schedules = {
            schedule.day: schedule
            for schedule in Schedule.objects.select_related('workout').all()
        }

        context['calendar'] = self._build_calendar(weeks, worksheets, schedules)
        context['today'] = today
        context['active_month'] = self.month
        context['days'] = list(calendar.day_name)

        # Avoid a request if possible
        if (
            (
                self.month == today.month or            # showing the current month
                any([today in week for week in weeks])  # or today is visible
            ) and
            schedules.get(today.isoweekday()) and       # with a workout scheduled for today
            not worksheets.get(today.isoweekday())      # that is not already active.
        ):
            context['workouts'] = Workout.objects.exclude(
                pk=schedules.get(today.isoweekday()).workout.id
            ).all()

        self._get_month_navigation(context, today)

    def _get_month_navigation(self, context, date):
        month = date.replace(day=1)
        context['month'] = month

        previous_month = month - datetime.timedelta(days=1)
        next_month = month + datetime.timedelta(days=32)
        context['previous_month_url'] = reverse('worksheet:calendar', args=[previous_month.year, previous_month.month])
        context['next_month_url'] = reverse('worksheet:calendar', args=[next_month.year, next_month.month])

    def _build_calendar(self, weeks, worksheets, schedules):
        workout_calendar = []

        for week in weeks:
            calendar_week = {}
            for date in week:
                if date in worksheets:
                    calendar_week[date] = {'worksheet': worksheets[date]}
                elif date.isoweekday() in schedules:
                    calendar_week[date] = {'workout': schedules[date.isoweekday()].workout}
                else:
                    calendar_week[date] = None

            workout_calendar.append(calendar_week)

        return workout_calendar

class CalendarView(IndexView):
    def render_to_response(self, context, **response_kwargs):
        (self.year, self.month) = (context['year'], context['month'])

        if (self.request.headers.get('HX-Request')):
            self._get_calendar(context)
            content = render_to_string('worksheet/index.html#calendar', context, self.request)
            content += render_to_string('worksheet/index.html#title', context, self.request)

            return HttpResponse(content)

        return super().render_to_response(context, **response_kwargs)

    def _get_month_navigation(self, context, date):
        date = datetime.date(self.year, self.month, 1)

        super()._get_month_navigation(context, date)

class CreateView(View):
    """
    Simple view to create a worksheet for the current day, if a workout is
    scheduled.
    """
    def post(self, request, *args, **kwargs):
        # If there's an older, active worksheet, bail and redirect to the index
        # where it will be listed
        if Worksheet.objects.get_active().exists():
            return HttpResponseRedirect(reverse('worksheet:index'))

        # Likewise if the requested workout doesn't exist, or none is scheduled
        # for today
        try:
            if (workout_id := request.POST.get('workout')):
                workout = Workout.objects.get(pk=workout_id)
            else:
                weekday = timezone.localdate().isoweekday()
                workout = Workout.objects.get(schedule__day=weekday)
        except Workout.DoesNotExist:
            return HttpResponseRedirect(reverse('worksheet:index'))

        worksheet, _ = Worksheet.objects.get_or_create(
            workout=workout,
            date=timezone.localdate(),
        )

        return HttpResponseRedirect(reverse(
            'worksheet:worksheet',
            args=[ worksheet.date.year, worksheet.date.month, worksheet.date.day, ]
        ))

    def get(self, request):
        return HttpResponseRedirect(reverse('worksheet:index'))

class WorksheetView(TemplateView):
    """
    Show or update a worksheet for a specific date.
    """
    template_name = 'worksheet/worksheet.html'

    def render_to_response(self, context, **response_kwargs):
        worksheet, results, date = self._get_worksheet_and_results(context)

        if worksheet is None:
            context['date'] = date
        else:

            if worksheet.workout.repeat:
                self.template_name = 'worksheet/worksheet_repeat.html'

            context.update({
                'worksheet': worksheet,
                'results': results,
                'note_form': ResultNoteForm(),
                'meter': {
                    'max': worksheet.total_exercise,
                    'low': math.ceil(worksheet.total_exercise / 2),
                    'high': worksheet.total_exercise - 1,
                    'optimum': worksheet.total_exercise,
                    'value': worksheet.done_exercise,
                },
            })

        return super().render_to_response(context, **response_kwargs)

    def _get_worksheet_and_results(self, context):
        worksheet = None
        results = None
        date = datetime.date(context['year'], context['month'], context['day'])

        try:
            worksheet = Worksheet.objects.select_related('workout').annotate(
                total_exercise=Count("result")
            ).annotate(
                done_exercise=Count("result__reps")
            ).get(date=date)
        except Worksheet.DoesNotExist:
            # TODO logging
            pass

        if worksheet is not None:
            results = self._get_results(worksheet)
            self._get_previous_results(worksheet, results)

        return worksheet, results, date

    def _get_results(self, worksheet):
        qs = worksheet.result_set.select_related('exercise')

        if worksheet.workout.repeat:
            qs = qs.order_by(
                "exercise__program",
                "_order"
            ).filter(
                exercise__workout=worksheet.workout
            )

        return qs.all()

    def _get_previous_results(self, worksheet, results):
        """
        Fetch the results of the same previous workout to display and
        compare, if any.
        """
        # This is only relevant or useful if a workout is in progress
        if not worksheet.done:
            previous_worksheet = Worksheet.objects.filter(
                workout=worksheet.workout,
                date__lt=worksheet.date,
                done=True,
            ).order_by("-date").first()

            if previous_worksheet is not None:
                for res, prev in zip(results,
                                     self._get_results(previous_worksheet)):
                    res.previous = prev

class CloseAction(View):
    def post(self, request, worksheet_id=None):
        try:
            Worksheet.objects.close(pk=worksheet_id)
        except Worksheet.DoesNotExist:
            pass

        return HttpResponseRedirect(reverse('worksheet:index'))

class ResultAction(View):
    def post(self, request, worksheet_id, result_id, field):
        # NOTE This should be a PUT request, but the CSRF middleware needs to
        # be configured for this to work. Need to read
        # https://docs.djangoproject.com/en/5.2/howto/csrf/ and
        # https://docs.djangoproject.com/en/5.2/ref/csrf/
        import http

        filters = {
            'pk': result_id,
            'worksheet': worksheet_id,
        }
        match field:
            case 'reps':
                value = request.POST.get('reps', None)
                if value is None:
                    # While the reps field is NULLable, it should not accept an
                    # empty value (blank=False). Because we don't use Django's
                    # form validation, we handle this case manually here.
                    return HttpResponse('Missing number of reps')

            case 'weight':
                value = request.POST.get('weight', None)
                filters.update(exercise__weight=True)

            case _:
                return HttpResponseNotFound()

        errors = None
        try:
            # Atomicity is required for the tests more than anything else, apparently
            with transaction.atomic():
                updated = Result.objects.filter(**filters).update(**{field: value})
        except ValueError as ve:
            # Keep the same format as the one used by ValidationError even
            # though there's no real reason to
            errors = {field: [str(ve)]}
        except IntegrityError:
            errors = {field: [f"Invalid value {value} for field '{field}'"]}

        event = None
        if errors is not None:
            event = 'updateError'
            http_response = render(request,
                                   'worksheet/partials.html#result_error',
                                   {'errors': errors},
                                   status=http.HTTPStatus.OK)
        else:
            if updated == 1:
                event = json.dumps({
                    'updateSuccess': {
                        'meter': {
                            'value':
                            Result.objects.filter(worksheet=worksheet_id,
                                                  reps__isnull=False).count()
                            if field == 'reps' else None
                        }
                    }
                })
                status = http.HTTPStatus.OK
            else:
                status = http.HTTPStatus.NO_CONTENT

            http_response = HttpResponse(status=status)

        if event:
            http_response["HX-Trigger-After-Settle"] = event

        return http_response

class NoteAction(View):
    def post(self, request, worksheet_id, result_id):
        # TODO Make this a PUT request
        note_form = ResultNoteForm(request.POST)
        context = {
            'note_form': note_form,
            'note_form_url': reverse('worksheet:note', kwargs={
                'worksheet_id': worksheet_id,
                'result_id': result_id,
            }),
        }

        if not note_form.is_valid():
            return render(request, 'worksheet/worksheet_base.html#note_form', context)

        value = note_form.cleaned_data['note']
        Result.objects.filter(pk=result_id, worksheet=worksheet_id).update(note=value)

        context.update({
            'result': Result(id=result_id, note=value),
            'worksheet': Worksheet(id=worksheet_id),
        })

        content = render_to_string('worksheet/worksheet_base.html#note_form', context, request)
        content += render_to_string('worksheet/worksheet.html#action_buttons', context, request)

        response = HttpResponse(content)

        if value is None:
            message = { 'noteDeleted': 'Note deleted' }
        else:
            message = { 'noteAdded': 'Note added' }

        response["HX-Trigger"] = json.dumps(message)

        return response
