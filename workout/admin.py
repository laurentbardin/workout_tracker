from django.contrib import admin

from .models import Exercise, Workout, Program, Schedule

class ProgramInline(admin.TabularInline):
    model = Program
    verbose_name = "Exercise"
    # This does not seem to limit the number of requests, unfortunately.
    #list_select_related = ['workout', 'exercise']

class ExerciseAdmin(admin.ModelAdmin):
    fields = [('name', 'weight')]
    list_display = ['__str__', 'weight']

class WorkoutAdmin(admin.ModelAdmin):
    fields = [('name', 'repeat')]
    list_display = ['__str__', 'repeat']
    inlines = [
        # This creates many duplicated SQL requests. Investigate to find out
        # why, and how to prevent it.
        #
        # Check
        # https://docs.djangoproject.com/en/5.2/ref/models/querysets/#prefetch-related
        ProgramInline,
    ]

class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['day', 'workout']
    # NOTE Using 'workout__name' in list_display makes list_select_related
    # mandatory to limit SQL requests, whereas simply using 'workout' does not.
    #list_select_related = ['workout']
    ordering = ['day']

# Register your models here.
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Workout, WorkoutAdmin)
admin.site.register(Schedule, ScheduleAdmin)
