FROM python:3.12
ENV PYTHONUNBUFFERED=1
RUN mkdir /backend
WORKDIR /backend
COPY requirements.txt /backend/
RUN apt-get update && apt-get install -y cron inetutils-syslogd bzip2
RUN python -m pip install --upgrade pip setuptools wheel                                                                                                                                                                                                
RUN pip install -r requirements.txt
RUN pip install "git+https://github.com/saurav-codes/django-cryptography"
COPY . /backend
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENV DJANGO_SETTINGS_MODULE=migratis.settings
