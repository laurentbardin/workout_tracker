FROM python:3 AS backend
WORKDIR /home/workout_tracker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


FROM node:22 AS frontend
WORKDIR /home/workout_tracker
COPY package.json package-lock.json .
RUN npm install


FROM backend AS server
COPY fixtures ./fixtures
COPY workout_tracker ./workout_tracker
COPY worksheet ./worksheet
COPY manage.py .
RUN python manage.py migrate && \
    python manage.py loaddata --app worksheet fixtures/worksheet.json
COPY --from=frontend /home/workout_tracker/node_modules ./node_modules


EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0:8000"]
