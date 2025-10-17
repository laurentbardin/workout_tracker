from django.http import HttpResponse
from django.views import View

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
class Index(View):
    def get(self, request):
        return HttpResponse('This is the index')
