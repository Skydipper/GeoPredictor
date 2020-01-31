FROM python:3.7
MAINTAINER Vizzuality Science Team info@vizzuality.com

WORKDIR /GeoPredictor

COPY main.py main.py

COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY entrypoint.sh entrypoint.sh

EXPOSE 6868
COPY ./GeoPredictor GeoPredictor

ENTRYPOINT ["./entrypoint.sh"]