import datetime

from django.db import connections

from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View

from .models import Result, Workout, Worksheet

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

class CreateView(TemplateView):
    """
    The current workout page checks if workouts are still in progress. If there
    are, it offers to close them by pointing to their specific page. In case
    there are none, it checks if a workout is scheduled for today: if that's
    the case, it creates a worksheet and redirects to its page; otherwise, it
    redirects to the index page.
    """
    template_name = 'workout/worksheet.html'

    # TODO change this to a POST-only view:
    # * inherit from View
    # * modify the link on the index to become a button to submit a form
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
            'workout:workout',
            args=[ worksheet.date.year, worksheet.date.month, worksheet.date.day, ]
        ))

class WorkoutView(TemplateView):
    """
    Show a workout for a specific date.
    """
    template_name = 'workout/workout.html'

    def render_to_response(self, context, **response_kwargs):
        worksheet, results, date = self._get_worksheet_and_results(context)

        if worksheet is None:
            context['date'] = date
        else:
            context.update({
                'worksheet': worksheet,
                'results': results,
            })

        return super().render_to_response(context, **response_kwargs)

    def post(self, request, *args, **kwargs):
        post = request.POST.copy()

        self.extra_context = {
            'reps': post.pop('reps'),
            'weight': post.pop('weight'),
            'result_ids': post.pop('result'),
        }

        return self.update_worksheet(self.get_context_data(**kwargs))

    def update_worksheet(self, context, **response_kwargs):
        worksheet, results, date = self._get_worksheet_and_results(context)

        if worksheet is None:
            return HttpResponseRedirect(reverse('workout:index'))

        if worksheet.done:
            return HttpResponseRedirect(reverse(
                'workout:workout',
                args=[date.year, date.month, date.day],
            ))

        result_ids = context['result_ids']
        results = {str(r.id): r
                   for r in Result.objects.filter(
                       worksheet=worksheet,
                       pk__in=result_ids
                   ).order_by(
                       "exercise__program",
                       "_order"
                   ).select_related('exercise').all()
                  }

        result_errors = 0
        for idx, result_id in enumerate(result_ids):
            result = results[result_id]

            result.reps = context['reps'][idx]
            result.weight = context['weight'][idx] or None

            try:
                result.clean_fields()
            except ValidationError as ve:
                result_errors += 1

                if not hasattr(result, 'errors'):
                    result.errors = {}

                result.errors.update(ve.message_dict)

        if result_errors == 0:
            Result.objects.bulk_update(results.values(), ["reps", "weight"])

        context.update({
            'worksheet': worksheet,
            'results': results.values(),
            'result_errors': result_errors,
        })

        return super().render_to_response(context, **response_kwargs)

    def _get_worksheet_and_results(self, context):
        worksheet = None
        results = None
        date = datetime.date(context['year'], context['month'], context['day'])

        try:
            worksheet = Worksheet.objects.select_related('workout').get(date=date)
        except Worksheet.DoesNotExist:
            # TODO logging
            pass

        if worksheet is not None:
            results = worksheet.result_set.order_by(
                "exercise__program",
                "_order"
            ).filter(
                exercise__workout=worksheet.workout
            ).select_related("exercise").all()

            if worksheet.done:
                self.template_name = 'workout/workout_done.html'

        return worksheet, results, date

class CloseAction(View):
    def post(self, request, worksheet_id=None):
        try:
            Worksheet.objects.close(pk=worksheet_id)
        except Worksheet.DoesNotExist:
            pass

        return HttpResponseRedirect(reverse('workout:index'))

class ResultAction(View):
    def post(self, request, worksheet_id=None):
        try:
            worksheet = Worksheet.objects.filter(done=False).get(pk=worksheet_id)
        except Worksheet.DoesNotExist:
            return HttpResponseRedirect(reverse('workout:index'))

        post = request.POST.copy()
        reps = post.pop('reps')
        weight = post.pop('weight')
        result_ids = post.pop('result')

        results = {str(r.id): r
                   for r in Result.objects.filter(
                       worksheet=worksheet,
                       pk__in=result_ids
                   ).order_by(
                       "exercise__program",
                       "_order"
                   ).select_related('exercise').all()
                  }

        result_errors = {}
        for idx, result_id in enumerate(result_ids):
            result = results[result_id]

            result.reps = reps[idx]
            result.weight = weight[idx] or None

            try:
                result.clean_fields()
            except ValidationError as ve:
                if not hasattr(result_errors, result_id):
                    result_errors[result_id] = {}

                result_errors[result_id] = ve.message_dict

        if len(result_errors) == 0:
            Result.objects.bulk_update(results.values(), ["reps", "weight"])
        else:
            worksheet.results = results.values()
            return render(
                request,
                "workout/workout.html",
                {
                    'worksheet': worksheet,
                }
            )

        return HttpResponseRedirect(reverse(
            'workout:workout',
            args=[ worksheet.date.year, worksheet.date.month, worksheet.date.day, ]
        ))

