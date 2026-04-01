<h1>A small Django application to track workout sessions</h1>

* [Overview](#overview)
  * [Models](#models)
* [Installation](#installation)
  * [Docker/Podman](#dockerpodman)
  * [Manual installation](#manual-installation)
    * [1. Install requirements in a virtual environment](#1-install-requirements-in-a-virtual-environment)
    * [2. Install the frontend dependencies](#2-install-the-frontend-dependencies)
    * [3. (Optional) PostgreSQL setup](#3-optional-postgresql-setup)
    * [4. Apply the migrations and the base data set](#4-apply-the-migrations-and-the-base-data-set)
    * [5. Run the development server](#5-run-the-development-server)
  * [Optional refinements](#optional-refinements)
    * [1. Run the tests](#1-run-the-tests)
    * [2. Edit the current user's timezone](#2-edit-the-current-users-timezone)
    * [3. Create the super user account](#3-create-the-super-user-account)
* [Usage](#usage)
* [Notes](#notes)
  * [No user account needed](#no-user-account-needed)
  * [CSS Grid](#css-grid)
  * [HTMX](#htmx)

# Overview

This is an app built to tackle two issues at the same time:

1. Replace old, antiquated spreadsheets used to track workout sessions
2. Learn Django development

The first one can be considered done, and the second is still in progress (as
learning often is).

*Note:* please be aware that I am by no means a designer, and don't have any
pretention to be, so the app may look raw.

## Models

The app consists of 4 main and 2 intermediary models. You can deploy the
collapsed element below to get a description of those in about a thousand
words.

<details>
<summary>Models relationship</summary>
![A diagram showing the relationship between models](doc/worksheet.png "Models relationship of the app")

`Workout`, `Exercise`, and `Schedule` should be self-explanatory.

A `Program` is simply the list of `Exercise`s of a `Workout`, in a specific
order.

A `Worksheet` is an instance of a given `Workout`, on a given date.

Finally, a `Result` is the actual data associated with an `Exercise` and a
specific `Worksheet`.
</details>

# Installation

It all starts with cloning the repository:
```sh
$ git clone --depth=1 git@gitlab.com:laurentbardin/workout_tracker
```
Then, you can quickly test the app using Docker/Podman, or install everything
manually.

## Docker/Podman

This method only works with SQLite (because there is no PostgreSQL image
involved). The custom image doesn't contain any code from the app itself, it
only comes with the frontend and backend dependencies installed. The actual app
code is mounted into the container at run time.

```sh
$ cd workout_tracker
$ make server
```

Running `make server` should take care of everything: downloading the image,
initialising the SQLite database (adding 3 workouts and their exercises, as well
as a basic schedule from Monday to Saturday), and running a container.

You can now open a browser to test the app:
[http://localhost:8000](http://localhost:8000)

## Manual installation

### 1. Install requirements in a virtual environment

Using `pip`:
```sh
$ cd workout_tracker
$ python -mvenv .venv
$ . .venv/bin/activate
$ pip install -r requirements.txt
```

*Or* using `uv`:
```sh
$ cd workout_tracker
$ uv sync
$ . .venv/bin/activate
```

### 2. Install the frontend dependencies

The app has only two lightweight Javascript dependencies:
[HTMX](https://htmx.org/) and [Oat](https://oat.ink/).
```sh
$ npm install
```

### 3. (Optional) PostgreSQL setup

By default, the app uses SQLite for a quicker setup, but is perfectly
compatible with PostgreSQL (the `psycopg` library is part of the dependencies).
Simply edit the `pg_conf` and `DATABASES` entries to your liking in
`settings.py`.

*Note*: when using PostgreSQL, the server's timezone should be set to
`Etc/UTC`, just like the app (`TIME_ZONE` in `settings.py`).

### 4. Apply the migrations and the base data set
```sh
$ python manage.py migrate
$ python manage.py loaddata --app worksheet fixtures/worksheet.json
```
This step adds 3 workouts and their exercises, as well as a basic schedule
(Monday to Saturday).

### 5. Run the development server
```sh
$ python manage.py runserver
```
Open a browser to test the app: [http://localhost:8000](http://localhost:8000)

## Optional refinements

You can do any of the following whether you used Docker or went with a manual
installation.

### 1. Run the tests

Once the migrations are applied, you should be able to run the tests, and they
should all pass (🤞).
```sh
$ python manage.py test
```

### 2. Edit the current user's timezone

Because this app was thought of as single-user but deals with timezone-aware
datetimes, I added an app setting to simulate a user setting.

In `settings.py`, edit `USER_TIME_ZONE` to match the one of your current
geographical location. The default is `Europe/Paris`.

### 3. Create the super user account
```sh
$ python manage.py createsuperuser
```
If you want to take a look at the admin area.

# Usage

The homepage displays a calendar view of the current month, with the current
day highlighted. If a workout is scheduled for today, clicking the button will
create the needed worksheet and (empty) results, and redirect you to the
worksheet page where you can start inserting data (and working out).

When done, you simply close the worksheet with the button at the bottom of the
page.

On the calendar view, past workouts are clickable if done. You can navigate to
past and future months by clicking the arrows to the left and right of the
calendar title, or by pressing the Left or Right Arrow keys on your keyboard.

# Notes

## No user account needed

This was built to fill a personnal need, so I didn't bother using Django's
builtin user management for that reason.

## CSS Grid

Even though tables are a perfect use case for the way worksheets are presented,
some issues arose when adding the form to post the data using HTMX. As I wanted
to improve my knowledge of CSS Grid, this was a good opportunity to do so.

## HTMX

Another piece of technology I wanted to earn some experience with (there's a
pattern here), and that felt perfect for my needs instead of a full-blown
frontend framework.
