from workout.models import (
    Exercise, Program, Workout,
)

class ProgramSetupMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        exercises = Exercise.objects.bulk_create([
            Exercise(name="Exercise 1", weight=True),
            Exercise(name="Exercise 2", weight=False),
            Exercise(name="Exercise 3", weight=True),
            Exercise(name="Exercise 4", weight=False),
        ])
        workout = Workout.objects.create(
            name="Test workout",
            repeat=False,
        )
        cls.workout = workout

        for ex in exercises:
            Program.objects.create(workout=workout, exercise=ex)
