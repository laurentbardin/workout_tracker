from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View

from worksheet.models import Workout, Worksheet


class CreateView(View):
    """
    Simple view to create a worksheet for the current day, if a workout is
    scheduled.
    """
    def post(self, request, *args, **kwargs):
        # If there's an older, active worksheet, bail and redirect to the index
        # where it will be listed
        if Worksheet.objects.get_active().exists():
            messages.error(request, "A workout session is already in progress (check the sidebar)")
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
            if workout_id is not None:
                messages.warning(request, "The specified workout doesn't exist.")
                messages.debug(request, f"Unknown workout {workout_id}")
            else:
                messages.warning(request, "No workout scheduled for today.")

            return HttpResponseRedirect(reverse('worksheet:index'))

        worksheet, created = Worksheet.objects.get_or_create(
            workout=workout,
            date=timezone.localdate(),
        )

        if created:
            messages.success(request, "Worksheet created")
            response = HttpResponseRedirect(reverse(
                'worksheet:worksheet',
                args=[ worksheet.date.year, worksheet.date.month, worksheet.date.day, ]
            ))
        else:
            messages.error(request, "An error occured when creating today's worksheet. Please try again later.")
            response = HttpResponseRedirect(reverse('worksheet:index'))

        return response

    def get(self, request):
        return HttpResponseRedirect(reverse('worksheet:index'))


