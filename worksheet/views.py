import calendar
import datetime
import json
import math

from django.db import IntegrityError, transaction
from django.db.models import Count
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

    def __init__(self, *args, **kwargs):
        self.today = timezone.localdate()

        return super().__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(self._get_calendar_context())

        return context

    def _get_calendar_context(self):
        if self.year is None or self.month is None:
            (self.year, self.month) = (self.today.year, self.today.month)

        cal = calendar.Calendar()
        weeks = list(cal.monthdatescalendar(self.year, self.month))

        visible_worksheets = Worksheet.objects.filter(
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
            ).select_related('workout')

        worksheets = {
            worksheet.date: worksheet
            for worksheet in visible_worksheets.all()
        }

        schedules = {
            schedule.day: schedule
            for schedule in Schedule.objects.select_related('workout').all()
        }

        context = {
            'calendar': self._get_calendar(weeks, worksheets, schedules),
            'today': self.today,
            'active_month': self.month,
            'days': list(calendar.day_name),
        }

        # Build the menu to select which workout to start (defaults to the
        # scheduled one). We avoid making the necessary request if no such menu
        # has to be displayed: when displaying a different month than the
        # current one and today is not visible, or there already is an active
        # worksheet.
        if (
            (
                self.month == self.today.month or            # showing the current month
                any([self.today in week for week in weeks])  # or today is visible
            ) and
            not worksheets.get(self.today)                   # and there are no active worksheet
        ):
            if schedules.get(self.today.isoweekday()):
                context['workouts'] = Workout.objects.exclude(
                    pk=schedules.get(self.today.isoweekday()).workout.id
                )
            else:
                context['workouts'] = Workout.objects.all()

        context.update(self._get_month_navigation(self.today))

        return context

    def _get_month_navigation(self, date):
        context = {}

        month = date.replace(day=1)
        context['month'] = month

        previous_month = month - datetime.timedelta(days=1)
        next_month = month + datetime.timedelta(days=32)
        context['previous_month_url'] = reverse('worksheet:calendar', args=[previous_month.year, previous_month.month])
        context['next_month_url'] = reverse('worksheet:calendar', args=[next_month.year, next_month.month])

        return context

    def _get_calendar(self, weeks, worksheets, schedules):
        workout_calendar = []

        for week in weeks:
            calendar_week = {}
            for date in week:
                if date in worksheets:
                    calendar_week[date] = {'worksheet': worksheets[date]}
                elif date.isoweekday() in schedules:
                    calendar_week[date] = {
                        'workout': schedules[date.isoweekday()].workout,
                        'skipped': date < self.today
                    }
                else:
                    calendar_week[date] = None

            workout_calendar.append(calendar_week)

        return workout_calendar

class CalendarView(IndexView):
    """
    CalendarView displays a calendar for a specific month of a specific year.
    It inherits from IndexView and overrides only the minimum necessary values
    (i.e. year and month) to work properly.
    """
    def get_context_data(self, **kwargs):
        """
        Properly set up this view's properties so that the calendar is
        correctly computed
        """
        (self.year, self.month) = (kwargs['year'], kwargs['month'])

        context = super().get_context_data(**kwargs)

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('HX-Request') is None:
            return super().render_to_response(context, **response_kwargs)

        response = HttpResponse()

        calendar = render_to_string('worksheet/index.html#calendar', context, self.request)
        nav = render_to_string('worksheet/index.html#calendar_nav', context, self.request)

        response.content = [calendar, nav]

        return response

    def _get_month_navigation(self, date):
        date = datetime.date(self.year, self.month, 1)

        return super()._get_month_navigation(date)

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
    Show a worksheet for a specific date.
    """
    template_name = 'worksheet/worksheet.html'

    repeat_workout = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        date = datetime.date(context['year'], context['month'], context['day'])
        worksheet, results = Worksheet.objects.get_with_results(date)

        if worksheet is None:
            context['date'] = date
        else:
            self.repeat_workout = worksheet.workout.repeat

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

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.repeat_workout:
            self.template_name = 'worksheet/worksheet_repeat.html'

        return super().render_to_response(context, **response_kwargs)

class CloseAction(View):
    def post(self, request, worksheet_id=None):
        try:
            Worksheet.objects.get(pk=worksheet_id, done=False).close()
        except Worksheet.DoesNotExist:
            pass

        return HttpResponseRedirect(reverse('worksheet:index'))

class ResultAction(View):
    def post(self, request, worksheet_id, result_id, field):
        # NOTE This should be a PUT request, but the CSRF middleware needs to
        # be configured for this to work. Need to read
        # https://docs.djangoproject.com/en/6.0/howto/csrf/ and
        # https://docs.djangoproject.com/en/6.0/ref/csrf/
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
        qs = Result.objects.filter(pk=result_id, worksheet=worksheet_id)
        if value is None:
            # Only delete existing notes in order to prevent a useless "Note
            # deleted" message
            qs = qs.filter(note__isnull=False)
        updated = qs.update(note=value)

        context.update({
            'result': Result(id=result_id, note=value),
            'worksheet': Worksheet(id=worksheet_id),
        })

        form = render_to_string('worksheet/worksheet_base.html#note_form', context, request)
        buttons = render_to_string('worksheet/worksheet.html#action_buttons', context, request)

        response = HttpResponse([form, buttons])

        if updated:
            if value is None:
                message = { 'noteDeleted': 'Note deleted' }
            else:
                message = { 'noteAdded': 'Note added' }

            response["HX-Trigger"] = json.dumps(message)

        return response
