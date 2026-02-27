.PHONY: server init-db

server:
	@docker compose up --watch

init-db:
	@docker exec workout_tracker-app-1 python manage.py migrate
	@docker exec workout_tracker-app-1 python manage.py loaddata --app worksheet fixtures/worksheet.json
