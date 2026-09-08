import datetime
import math

from django.urls import reverse
from django.views.generic import TemplateView

from worksheet.forms import ResultNoteForm
from worksheet.models import Worksheet


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
                'calendar_url': reverse(
                    'worksheet:calendar',
                    kwargs={ 'year': worksheet.date.year, 'month': worksheet.date.month }
                ),
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


