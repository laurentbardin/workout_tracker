import json

from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import View

from worksheet.forms import ResultNoteForm
from worksheet.models import Result, Worksheet


class NoteAction(View):
    def post(self, request, worksheet_id, result_id):
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
