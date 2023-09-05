FROM python:3 AS uptest

WORKDIR /usr/src/app

RUN apt-get -y update && apt-get -y install gettext awscli && pip install requests

COPY config.tpl.py ./
COPY uptest.py ./

ENV USERNAME="email@example.com" \
    PASSWORD="tobedefined" \
    HOST="smtp.example.com" \
    PORT="465" \
    DEST="email@example.com" \
    URLS="example.com example.com/page/"

CMD envsubst < config.tpl.py > config.py && \
    python ./uptest.py
