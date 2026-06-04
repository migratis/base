#!/bin/bash
touch /var/log/syslog
touch /var/log/cron.log
printenv | grep -Ev 'BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID|LANG|PWD|GPG_KEY|_=' >> /etc/environment
/etc/init.d/inetutils-syslogd start
service cron start
python manage.py collectstatic --noinput
python manage.py crontab add
#python manage.py loaddata db.json
# Wait for the database to be reachable, then migrate. In SQLite mode this
# succeeds on the first try; in Postgres mode (USE_SQLITE=False) it retries
# until the base-db container accepts connections — no depends_on needed.
until python manage.py migrate; do
  echo "Database not ready — retrying migrate in 2s…"
  sleep 2
done
# Translations are DB-backed (served from the i18n tables). Seed them on every
# boot so the standalone app has its UI strings even on a fresh SQLite DB.
# Idempotent (get_or_create), so it is safe to re-run.
python manage.py seed_translations
python manage.py runserver 0.0.0.0:8004
