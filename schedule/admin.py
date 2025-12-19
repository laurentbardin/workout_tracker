from django.contrib import admin

from .models import Schedule

class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['day', 'workout']
    # NOTE Using 'workout__name' in list_display makes list_select_related
    # mandatory to limit SQL requests, whereas simply using 'workout' does not.
    #list_select_related = ['workout']
    ordering = ['day']

admin.site.register(Schedule, ScheduleAdmin)
