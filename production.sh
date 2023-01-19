pip install uwsgi

# uwsgi --http 127.0.0.1:5000 --master --enable-threads -p 4 -w rest.rest:app &
# uwsgi --http 127.0.0.1:5001 --master --enable-threads -p 4 -w rpc:rpc_app

# sudo pkill -f uwsgi -9


# only 1 can run at a time?
# fuser -k 5000/tcp
# gunicorn --workers 4 --bind 0.0.0.0:5000 rest.rest:app & 
gunicorn --workers 8 --bind 0.0.0.0:5001 rpc:rpc_app