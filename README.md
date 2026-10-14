# Student Management System (Django + PostgreSQL)

A modern student records app built with **Django**, the **Django ORM** and **PostgreSQL** (SQLite works out of the box for quick local runs).

## Features

| Area | What you get |
|---|---|
| **Dashboard** | Stat cards (total, active, graduated, average CGPA, admitted this year), 4 interactive Chart.js charts (department, status, admissions per year, CGPA distribution), top performers, recent additions. Click a bar or slice to jump to the filtered student list. |
| **Student management** | Add, edit, delete, search (name, roll no, email), filter (department, status, gender, year), sort, pagination |
| **Interactive UI** | Dark mode (remembers your choice, charts recolour instantly), responsive navigation, toast notifications, delete confirmation dialog |
| **Data export** | Download the current (filtered) list as CSV. Formula-injection safe, opens correctly in Excel |
| **Database** | Django ORM models with validation, indexes, and aggregate queries; PostgreSQL via `DATABASE_URL` |
| **Security** | Login required everywhere, CSRF protection, whitelisted sort keys, HTTPS and secure cookies in production |
| **Quality** | 13 automated tests, GitHub Actions CI that runs them against PostgreSQL |

**Tech:** Python 3.10+ · Django · PostgreSQL · psycopg 3 · Chart.js · WhiteNoise · Gunicorn

---

## 1. Run it on your computer (VS Code)

### Install once
1. **Python 3.10 or newer**: https://www.python.org/downloads/ (on Windows tick *Add Python to PATH*).
2. **VS Code**: https://code.visualstudio.com/ then install the **Python** extension (VS Code will suggest the recommended extensions when you open this folder).
3. **Git**: https://git-scm.com/downloads

### Open the project
`File → Open Folder…` and choose the `django-student-management-system` folder. Open the terminal with **Ctrl+`**.

### Set up and start (SQLite, no database install needed)

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_students
python manage.py runserver
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_students
python manage.py runserver
```

Open **http://127.0.0.1:8000** and sign in with the superuser you just created.

- `makemigrations` creates the database blueprint in `students/migrations/`. **Commit that folder to GitHub.**
- `seed_students` loads 150 demo students so the charts have data (`--count 500` for more, `--clear` to reseed).
- In VS Code you can also press **F5** to run the server with the debugger (config in `.vscode/launch.json`). If VS Code asks for an interpreter, choose the one inside `.venv`.

### Switch to PostgreSQL (recommended before deploying)
1. Install PostgreSQL: https://www.postgresql.org/download/
2. Open `psql` (on Windows: *SQL Shell (psql)*) as the `postgres` user and run:
   ```sql
   CREATE USER sms_user WITH PASSWORD 'sms_password' CREATEDB;
   CREATE DATABASE sms_db OWNER sms_user;
   ```
3. In `.env`, uncomment the line and save:
   ```
   DATABASE_URL=postgresql://sms_user:sms_password@localhost:5432/sms_db
   ```
4. Run `python manage.py migrate`, `createsuperuser` and `seed_students` again (this is a fresh database).

### Run the tests
```bash
python manage.py test
```

### Useful commands
| Command | Purpose |
|---|---|
| `python manage.py runserver` | Start the app |
| `python manage.py makemigrations` / `migrate` | Create / apply database changes after editing `models.py` |
| `python manage.py createsuperuser` | Create an admin login |
| `python manage.py seed_students --clear --count 300` | Replace data with 300 demo students |
| `python manage.py test` | Run the test suite |

---

## 2. Publish to GitHub

1. On https://github.com click **New repository**. Name it `student-management-system`. Leave "Add README" **unchecked**.
2. In the VS Code terminal (inside the project folder, with `.env` **not** committed: `.gitignore` already protects it):
   ```bash
   git init
   git add .
   git status                      # check: .env and db.sqlite3 must NOT be listed
   git commit -m "Student Management System: Django, PostgreSQL, dashboard, CSV export"
   git branch -M main
   git remote add origin https://github.com/<your-username>/student-management-system.git
   git push -u origin main
   ```
   If Git asks who you are: `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`.
3. Open the **Actions** tab on GitHub: the CI workflow runs the tests on PostgreSQL after every push. Add the green badge to this README if you like.
4. Polish for recruiters: add 2-3 screenshots (dashboard in light and dark mode, student list) to the README, set the repo description and topics (`django`, `postgresql`, `chartjs`), and pin the repo on your profile.

---

## 3. Put it live (free): Render + Neon PostgreSQL

This repo is already prepared: `build.sh`, `render.yaml`, `Procfile`, WhiteNoise for static files, and production security settings that switch on automatically when `DEBUG=False`.

### A. Database (Neon)
1. Create a free project at https://neon.tech and copy the **connection string** (it looks like `postgresql://user:pass@host/dbname?sslmode=require`).

### B. Web app (Render)
1. At https://render.com choose **New → Web Service** and connect your GitHub repository (or **New → Blueprint** to use `render.yaml`).
2. Settings if you configure it by hand:
   - Runtime: **Python 3**
   - Build command: `bash build.sh`
   - Start command: `gunicorn config.wsgi:application`
   - Plan: **Free**
3. Add these **environment variables**:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | the Neon connection string |
   | `SECRET_KEY` | a long random string (Render can generate one) |
   | `DEBUG` | `False` |
   | `PYTHON_VERSION` | `3.12.3` |
   | `DJANGO_SUPERUSER_USERNAME` | `admin` |
   | `DJANGO_SUPERUSER_PASSWORD` | a strong password (this becomes your login) |
   | `SEED_DEMO` | `1` for demo data on the first deploy, then set to `0` |

4. Click **Deploy**. `build.sh` installs packages, collects static files, applies migrations, creates the admin user and loads demo data.
5. Open your `https://<name>.onrender.com` URL and sign in with the admin credentials you set.

### After it is live
- **Free-tier behaviour:** the app goes to sleep after a period without visitors, so the first request can take up to a minute to wake it. Open it yourself shortly before showing it to someone.
- Free-tier limits change, so check Render's and Neon's current pricing pages.
- Put the live link at the top of this README and on your resume.
- Never commit `.env`. Rotate `SECRET_KEY` and the admin password if they were ever shared.

---

## Project structure

```
config/            settings (env-based), urls, wsgi
students/          models, forms, views, urls, admin, tests, seed command
templates/         base layout, dashboard, student list/form/delete, login
static/            app.css (light/dark, responsive), app.js (theme, menu, toasts, dialog)
.vscode/           launch / settings / recommended extensions
.github/workflows  CI: tests on PostgreSQL
build.sh, render.yaml, Procfile    deployment
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` not found (Windows) | Try `py` instead, or reinstall Python with *Add to PATH* ticked |
| PowerShell blocks `activate` | Run `Set-ExecutionPolicy -Scope Process RemoteSigned`, then activate again |
| `No such table: students_student` | You skipped `makemigrations` / `migrate` |
| `password authentication failed` | The user/password in `DATABASE_URL` do not match what you created in `psql` |
| Tests fail with "permission denied to create database" | Create the PostgreSQL user with `CREATEDB` (see step above) |
| Page has no styling on Render | Check the build log shows `collectstatic` ran, and that `DEBUG` is `False` |
| `DisallowedHost` / CSRF error on your own domain | Add it to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` |
