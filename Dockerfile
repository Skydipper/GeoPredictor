FROM python:3.6
MAINTAINER Vizzuality Science Team info@vizzuality.com

COPY entrypoint.sh entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]