FROM debian:latest

RUN apt-get update && apt-get install -y python2 python-tk python-pthreading

COPY . /app
