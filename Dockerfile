FROM python:3.12-slim-bullseye
LABEL authors="arian.ott"
RUN apt update && apt upgrade -y
WORKDIR app
COPY . .
RUN pip3 install -r requirements.txt
RUN rm requirements.txt
RUN mkdir data &&\
    mkdir data/wagner &&\
    mkdir data/

ENTRYPOINT ["top", "-b"]