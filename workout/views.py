import datetime

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from .models import Workout, Worksheet

# SQL requests reference
# * List of exercises for the current session with their reps and weight (if
# available)
#
#   SELECT e.name, r.reps, r.weight, w.status FROM workout_exercise AS e
#       LEFT JOIN workout_result AS r ON r.exercise_id = e.id
#       JOIN workout_program AS p ON p.exercise_id = e.id
#       JOIN workout_worksheet AS w ON w.workout_id = p.workout_id
#   WHERE w.status = 'In progress' ORDER BY p._order;

# Create your views here.
class Index(TemplateView):
    """
    The index displays the name of today's workout and a link to go to the
    current worksheet.
    """
    template_name = 'workout/index.html'

    def render_to_response(self, context, **response_kwargs):
        weekday = timezone.now().isoweekday()
        try:
            workout = Workout.objects.get(schedule__day=weekday)
        except Workout.DoesNotExist:
            workout = None

        context['workout'] = workout

        return super().render_to_response(context, **response_kwargs)

class Current(TemplateView):
    """
    The current workout page checks if workouts are still in progress. If there
    are, it offers to close them by pointing to their specific page. In case
    there are none, it checks if a workout is scheduled for today: if that's
    the case, it creates a worksheet and redirects to its page; otherwise, it
    redirects to the index page.
    """
    template_name = 'workout/worksheet.html'

    def render_to_response(self, context, **response_kwargs):
        active_worksheets = Worksheet.objects.get_active().count()

        if active_worksheets > 0:
            context['active_worksheets'] = Worksheet.objects.get_active().select_related('workout')
            return super().render_to_response(context, **response_kwargs)

        weekday = timezone.now().isoweekday()
        try:
            workout = Workout.objects.get(schedule__day=weekday)
        except Workout.DoesNotExist:
            return HttpResponseRedirect(reverse('workout:index'))

        worksheet, _ = Worksheet.objects.get_or_create(
            workout=workout,
            date=timezone.localdate(),
        )

        return HttpResponseRedirect(reverse(
            'workout:worksheet',
            args=[ worksheet.date.year, worksheet.date.month, worksheet.date.day, ]
        ))

class Archive(TemplateView):
    """
    Show a workout for a specific date. Using the current date should be
    equivalent to using the 'Current' view.
    """
    template_name = 'workout/workout.html'

    def render_to_response(self, context, **response_kwargs):
        date = datetime.date(context['year'], context['month'], context['day'])
        try:
            context['worksheet'] = Worksheet.objects.select_related('workout').get(date=date)
        except Worksheet.DoesNotExist:
            pass

        context['date'] = date

        return super().render_to_response(context, **response_kwargs)
