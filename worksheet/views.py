import datetime

from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View

from .models import Result, Workout, Worksheet

# Create your views here.
class Index(TemplateView):
    """
    The index displays the name of today's workout and either a button to
    create a new worksheet for the scheduled workout, or a link to any already
    active worksheet.
    """
    template_name = 'worksheet/index.html'

    def render_to_response(self, context, **response_kwargs):
        active_worksheets = Worksheet.objects.get_active().all()

        if active_worksheets:
            context['active_worksheets'] = active_worksheets
        else:
            localdate = timezone.localdate()
            weekday = localdate.isoweekday()
            try:
                workout = Workout.objects.get(schedule__day=weekday)
                workout.worksheet = workout.worksheet_set.filter(
                    date=localdate,
                    done=False,
                ).first()
            except Workout.DoesNotExist:
                workout = None

            context['workout'] = workout
            context['localdate'] = localdate

        return super().render_to_response(context, **response_kwargs)

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

        # Likewise if no workout is scheduled for today
        weekday = timezone.localdate().isoweekday()
        try:
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
            return HttpResponseRedirect(reverse('worksheet:index'))

        if worksheet.done:
            return HttpResponseRedirect(reverse(
                'worksheet:worksheet',
                args=[date.year, date.month, date.day],
            ))

        results_dict = {str(r.id): r for r in results}

        result_errors = 0
        for idx, result_id in enumerate(context['result_ids']):
            result = results_dict[result_id]

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
            Result.objects.bulk_update(results, ["reps", "weight"])

        if worksheet.workout.repeat:
            self.template_name = 'worksheet/worksheet_repeat.html'

        context.update({
            'worksheet': worksheet,
            'results': results,
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
    def post(self, request, worksheet_id=None):
        result_id = request.POST.get('result', None)
        reps = request.POST.get('reps', None)
        weight = request.POST.get('weight', None)

        if not result_id or not reps:
            return HttpResponse('Missing result ID or reps')

        try:
            result = Result.objects.filter(worksheet=worksheet_id).get(pk=result_id)
            result.reps = reps
            result.weight = weight

            result.clean_fields()
            result.save(update_fields=["reps", "weight"])
        except Result.DoesNotExist:
            return HttpResponse(f'Could not update result {result_id} for worksheet {worksheet_id}')
        except ValidationError as ve:
            return render(request, 'worksheet/partials/result_error.html', {'errors': ve.message_dict})

        return HttpResponse('✅')
