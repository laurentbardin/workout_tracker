FROM node:22 AS frontend
WORKDIR /home/workout_tracker
RUN --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=package-lock.json,target=package-lock.json,rw \
    npm install



FROM python:3-alpine AS backend
WORKDIR /home/workout_tracker

RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install --no-cache-dir -r requirements.txt

COPY --from=frontend /home/workout_tracker/node_modules ./node_modules
COPY manage.py ./
COPY --parents worksheet/ workout_tracker/ ./

RUN mkdir data
RUN python manage.py migrate
RUN --mount=type=bind,source=fixtures/worksheet.json,target=worksheet.json \
    python manage.py loaddata --app worksheet worksheet.json

VOLUME /home/workout_tracker/data

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0:8000"]
