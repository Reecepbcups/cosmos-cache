# docker build -t reecepbcups/rpc-cache:latest .
# docker run -e RPC_WORKER_THREADS=2 -e REMOTE_CONFIG_TIME_FILE=https://raw.githubusercontent.com/Reecepbcups/cosmos-endpoint-cache/main/configs/cache_times.json -p 5001:5001 reecepbcups/rpc-cache:latest

FROM python:3.11-slim

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

# You can set this at run time with -e
ENV RPC_WORKER_THREADS=1

# CMD ["gunicorn", "-w", "echo ${WORKER_THREADS}", "-b", "0.0.0.0:5001", "rpc:rpc_app"]
CMD gunicorn -w ${RPC_WORKER_THREADS} -b 0.0.0.0:5001 rpc:rpc_app