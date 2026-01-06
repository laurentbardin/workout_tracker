# A small Django application to track workout sessions

Built to familiarize myself with Django development.

## Overview

TODO

## Installation

1. Clone the repository
    ```sh
    $ git clone git@gitlab.com:laurentbardin/workout_tracker
    ```

2. Install requirements in a virtualenv

    Using `pip`:
    ```sh
    $ python -mvenv .venv
    $ . .venv/bin/activate
    $ cd workout_tracker
    $ pip install -r requirements.txt
    ```

    _Or_ using `uv`:
    ```sh
    $ cd workout_tracker
    $ uv sync
    $ . .venv/bin/activate
    ```

3. Apply the migrations and the base data set
    ```sh
    $ python manage.py migrate
    $ py manage.py loaddata --app worksheet fixtures/workout_base.json
    ```

4. Run the development server
    ```sh
    $ python manage.py runserver
    ```
    Open a browser to test the app: [http://localhost:8000](http://localhost:8000)

## Notes

TODO
