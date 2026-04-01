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

VOLUME /home/workout_tracker

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0:8000"]
