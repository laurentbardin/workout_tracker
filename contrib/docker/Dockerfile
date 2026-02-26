FROM node:22 AS frontend
WORKDIR /home/workout_tracker
COPY package.json package-lock.json .
RUN npm install


FROM python:3 AS server
WORKDIR /home/workout_tracker

COPY requirements.txt manage.py .
RUN pip install --no-cache-dir -r requirements.txt

COPY workout_tracker ./workout_tracker
COPY worksheet ./worksheet
COPY fixtures ./fixtures
RUN python manage.py migrate && \
    python manage.py loaddata --app worksheet fixtures/worksheet.json

COPY --from=frontend /home/workout_tracker/node_modules ./node_modules

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0:8000"]
