FROM alpine:latest

ENV LANG=en_US.UTF-8

RUN apk update \
  && apk upgrade \
  && apk add bash bind-tools iputils \
  && apk add python3 py3-pip  \
  && python3 -m ensurepip --upgrade \
  && pip3 install -U pip \
  && rm -f /var/cache/apk/*

RUN python3.8 -m pip install --upgrade pip

RUN pip3 install mailru-im-bot \
	sqlalchemy\
	python-gettext \
	alphabet-detector \
	pytz \
  jsons \
  dnspython \
  cached-property \
  enum34 \
  expiringdict \
  monotonic \
  python-baseconv \
  requests \
  six \
  gTTS

RUN mkdir /work

VOLUME  /work/log /work/db /work/tmp
WORKDIR /work/


COPY paquebot.ini /work/
#RUN echo "[default]" > paquebot.ini
#RUN echo "ICQBOT_NAME = $ICQBOT_NAME" >> paquebot.ini
#RUN echo "ICQBOT_TOKEN = $ICQBOT_TOKEN" >> paquebot.ini
#RUN echo "ICQBOT_OWNER = $ICQBOT_OWNER" >> paquebot.ini
#RUN echo "ICQBOT_VERSION = $ICQBOT_VERSION" >> paquebot.ini
#RUN echo "ICQBOT_API_URL = $ICQBOT_API_URL" >> paquebot.ini

COPY *.py /work/
COPY logging.ini /work/

ENTRYPOINT ["python3", "paquebot.py"]

