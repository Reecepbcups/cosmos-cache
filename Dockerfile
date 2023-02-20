# docker build . -t reecepbcups/rpc-cache:latest
# docker run --name rpc-cache -p 5001:5001 reecepbcups/rpc-cache:latest

FROM python:3.6-slim

COPY . /srv/flask_app
WORKDIR /srv/flask_app

RUN apt-get clean \
    && apt-get -y update

RUN apt-get -y install nginx \
    && apt-get -y install python3-dev \
    && apt-get -y install build-essential

RUN pip install -r requirements/requirements.txt --src /usr/local/src

EXPOSE 5001
CMD ["gunicorn", "-b", "0.0.0.0:5001", "rpc:rpc_app"]