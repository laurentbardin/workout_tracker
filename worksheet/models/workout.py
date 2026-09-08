from itertools import batched

from django.contrib import admin
from django.db import models

from .exercise import Exercise


class Workout(models.Model):
    name = models.CharField(max_length=50)
    repeat = models.BooleanField(verbose_name="Repeat workout exercises?", default=False)
    exercises = models.ManyToManyField(Exercise, through="Program")

    @admin.display(description="Workout")
    def __str__(self):
        return self.name

    def get_exercises_in_order(self):
        """
        Get the list of exercises of the workout, in the order they are
        executed, which will be different than the order they are displayed in
        the case of repeat workouts.
        """
        exercises = self.exercises.filter(workout=self).order_by('program')

        if self.repeat:
            # TODO use something else than the ID - slug or qname?
            match self.id:
                case 1:
                    # 1, 2, 3, 4 -> 1, 2, 3, 4, 2, 1, 4, 3
                    second_round = [exercise
                                    for first, second in batched(exercises, 2)
                                    for exercise in (second, first)]
                    exercises = list(exercises) + second_round

                case 2:
                    # 1, 2, 3, 4, 5, 6 -> 1, 2, 3, 1, 2, 3, 4, 5, 6, 4, 5, 6
                    exercises = [exercise
                                 for first, second, third in batched(exercises, 3)
                                 for exercise in (first, second, third, first, second, third)]

        return exercises


