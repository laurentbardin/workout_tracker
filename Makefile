.PHONY: server

IMAGE := registry.gitlab.com/laurentbardin/workout_tracker:latest
DOCKER_RUN_ARGS := -v ./:/home/workout_tracker --rm --name workout_tracker

server: data/db.sqlite3
	@docker compose -p workout_tracker up

data/db.sqlite3:
	@docker run $(DOCKER_RUN_ARGS) $(IMAGE) python manage.py migrate
	@docker run $(DOCKER_RUN_ARGS) $(IMAGE) python manage.py loaddata --app worksheet fixtures/worksheet.json
