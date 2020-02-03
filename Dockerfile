
FROM python:3.7

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

COPY requirements.txt requirements-nats.txt ./

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ARG NATS_PYPI_INDEX
RUN if [ ! -z $NATS_PYPI_INDEX ]; then \
        echo Building with support for MachColl ;\
        pip install -i $NATS_PYPI_INDEX --no-cache-dir -r requirements-nats.txt; \
    else \
        echo Not building with support for MachColl ;\
    fi

COPY ./bluesky/bluesky ./bluesky/bluesky
COPY .env run.py VERSION ./
COPY ./bluebird ./bluebird
RUN find . -type d -name '__pycache__' -prune -exec rm -r {} \;

ENV FLASK_ENV=development
ENV BB_LOGS_ROOT="/var/log/bluebird"

CMD python ./run.py --sim-host=$BS_HOST
