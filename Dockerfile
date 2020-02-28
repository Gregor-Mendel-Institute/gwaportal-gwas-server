FROM python:2
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1
RUN useradd --uid=10372 -ms /bin/bash gwaportal

COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt && pip install gunicorn
COPY . /tmp
RUN pip install --no-cache-dir /tmp && rm -fr /tmp/*
USER gwaportal
ENTRYPOINT ["gunicorn","-b","0.0.0.0:8000","--workers", "2","gwasrv:api"]