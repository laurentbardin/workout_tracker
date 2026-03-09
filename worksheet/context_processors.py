from worksheet.models import Worksheet

def active_worksheets(request):
    return { 'active_worksheets': Worksheet.objects.get_active().all() }
