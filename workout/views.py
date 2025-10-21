from django.utils import timezone
from django.views.generic import TemplateView

from .models import Workout

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
    template_name = 'workout/index.html'

    def render_to_response(self, context, **response_kwargs):
        today = timezone.now().isoweekday()
        try:
            workout = Workout.objects.get(schedule__day=today)
        except Workout.DoesNotExist:
            workout = None

        context['workout'] = workout

        return super().render_to_response(context, **response_kwargs)
