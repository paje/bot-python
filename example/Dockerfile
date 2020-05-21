FROM alpine:latest

ENV LANG=en_US.UTF-8

ARG ICQBOT_NAME
ARG ICQBOT_TOKEN
ARG ICQBOT_OWNER
ARG ICQBOT_VERSION
ARG ICQBOT_API_URL="https://api.icq.net/bot/v1"

RUN apk update \
  && apk upgrade \
  && apk add bash bind-tools iputils \
  && apk add python3 py3-pip  \
  && python3 -m ensurepip --upgrade \
  && pip3 install -U pip \
  && rm -f /var/cache/apk/*

RUN pip3 install mailru-im-bot \
	sqlalchemy\
	python-gettext \
	alphabet-detector \
	pytz

RUN mkdir /work
VOLUME  /work/log /work/db
WORKDIR /work/

RUN echo "[default]" > paquebot.ini
RUN echo "ICQBOT_NAME = $ICQBOT_NAME" >> paquebot.ini
RUN echo "ICQBOT_TOKEN = $ICQBOT_TOKEN" >> paquebot.ini
RUN echo "ICQBOT_OWNER = $ICQBOT_OWNER" >> paquebot.ini
RUN echo "ICQBOT_VERSION = $ICQBOT_VERSION" >> paquebot.ini
RUN echo "ICQBOT_API_URL = $ICQBOT_API_URL" >> paquebot.ini

COPY *.py /work/
COPY logging.ini /work/

#ENTRYPOINT ["python3", "paquebot.py"]

