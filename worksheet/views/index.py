import calendar
import datetime

from django.db.models import Count
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from worksheet.models import Schedule, Workout, Worksheet


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

        super().__init__(*args, **kwargs)

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
                self.month == self.today.month or          # showing the current month
                any(self.today in week for week in weeks)  # or today is visible
            ) and
            not worksheets.get(self.today)                 # and there are no active worksheet
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


