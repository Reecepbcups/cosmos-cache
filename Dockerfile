# docker build . -t reecepbcups/rpc-cache:latest
# docker run --name rpc-cache -p 5001:5001 reecepbcups/rpc-cache:latest

FROM python:3.6-slim

RUN apt-get clean \
    && apt-get -y update

RUN apt-get -y install nginx \
    && apt-get -y install python3-dev \
    && apt-get -y install build-essential

COPY requirements/requirements.txt /srv/flask_app/requirements/requirements.txt
RUN pip install -r /srv/flask_app/requirements/requirements.txt --src /usr/local/src

COPY . /srv/flask_app
WORKDIR /srv/flask_app

EXPOSE 5001
# ["gunicorn", "-w","3", "-b", "0.0.0.0:5000", "app"]
CMD ["gunicorn", "-b", "0.0.0.0:5001", "rpc:rpc_app"]