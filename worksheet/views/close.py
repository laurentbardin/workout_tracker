from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import View

from worksheet.models import Worksheet


class CloseAction(View):
    def post(self, request, worksheet_id=None):
        try:
            Worksheet.objects.get(pk=worksheet_id, done=False).close()
        except Worksheet.DoesNotExist:
            pass

        return HttpResponseRedirect(reverse('worksheet:index'))
