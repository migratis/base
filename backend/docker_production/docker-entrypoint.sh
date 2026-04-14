#!/bin/bash
touch /var/log/syslog
touch /var/log/cron.log
printenv | grep -Ev 'BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID|LANG|PWD|GPG_KEY|_=' >> /etc/environment
/etc/init.d/inetutils-syslogd start
service cron start
python manage.py collectstatic --noinput
python manage.py crontab add
#python manage.py loaddata db.json
gunicorn migratis.wsgi --preload --reload --timeout 120 --bind 0.0.0.0:8002
