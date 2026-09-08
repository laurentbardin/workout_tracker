import json

from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.views.generic import View

from worksheet.models import Result


class ResultAction(View):
    def post(self, request, worksheet_id, result_id, field):
        import http

        filters = {
            'pk': result_id,
            'worksheet': worksheet_id,
        }
        match field:
            case 'reps':
                value = request.POST.get('reps', None)
                if value is None:
                    # While the reps field is NULLable, it should not accept an
                    # empty value (blank=False). Because we don't use Django's
                    # form validation, we handle this case manually here.
                    return HttpResponse('Missing number of reps')

            case 'weight':
                value = request.POST.get('weight', None)
                filters.update(exercise__weight=True)

            case _:
                return HttpResponseNotFound()

        errors = None
        try:
            # Atomicity is required for the tests more than anything else, apparently
            with transaction.atomic():
                updated = Result.objects.filter(**filters).update(**{field: value})
        except ValueError as ve:
            # Keep the same format as the one used by ValidationError even
            # though there's no real reason to
            errors = {field: [str(ve)]}
        except IntegrityError:
            errors = {field: [f"Invalid value {value} for field '{field}'"]}

        event = None
        if errors is not None:
            event = 'updateError'
            http_response = render(request,
                                   'worksheet/partials.html#result_error',
                                   {'errors': errors},
                                   status=http.HTTPStatus.OK)
        else:
            if updated == 1:
                event = json.dumps({
                    'updateSuccess': {
                        'meter': {
                            'value':
                            Result.objects.filter(worksheet=worksheet_id,
                                                  reps__isnull=False).count()
                            if field == 'reps' else None
                        }
                    }
                })
                status = http.HTTPStatus.OK
            else:
                status = http.HTTPStatus.NO_CONTENT

            http_response = HttpResponse(status=status)

        if event:
            http_response["HX-Trigger-After-Settle"] = event

        return http_response


