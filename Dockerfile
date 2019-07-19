FROM python:3.6
MAINTAINER Vizzuality Science Team info@vizzuality.com

WORKDIR /validator

COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY entrypoint.sh entrypoint.sh

EXPOSE 6767

ENTRYPOINT ["./entrypoint.sh"]