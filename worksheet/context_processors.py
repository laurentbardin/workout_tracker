import json

from worksheet.models import Worksheet

def active_worksheets(request):
    return { 'active_worksheets': Worksheet.objects.get_active().all() }

def htmx_config(request):
    config = {
        # From the doc:
        # "This should always be disabled when using HX-Request header to
        # optionally return partial responses"
        # This is the case with the CalendarView view. Disabling it globally is
        # quicker and safer than coming up with a system allowing each view be
        # responsible for setting it up if necessary (and potentially
        # forgetting to do so).
        'historyRestoreAsHxRequest': False,
        # Force issuing an HTTP request when navigating through browser history
        'historyCacheSize': 0,
    }

    return { 'htmx_config': json.dumps(config) }

def htmx_request(request):
    return { 'htmx_request': True if request.headers.get('HX-Request') else False }
