FROM alpine:latest

ENV LANG=en_US.UTF-8


env ICQBOT_NAME="ICQBOT"
env ICQBOT_TOKEN="XXX.XXXXXXX.XXXXXXX:XXXXXX"
env ICQBOT_OWNER="1234567890"
env ICQBOT_VERSION="0.0.1"
env ICQBOT_TESTCHAT="Test_Chat"

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

COPY *.py /work/
COPY logging.ini /work/

