from multiprocessing import Process

import logging
from flask import Flask
from flask_socketio import SocketIO
import redis
import os

sio = SocketIO()
REDIS_URL = os.getenv("REDIS_URL", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME", "navigator_frontend")
redis_conn = redis.Redis(host=REDIS_URL, port=REDIS_PORT, db=4, charset="utf-8", decode_responses=True)

log = logging.getLogger(__name__)

# TODO:  Can't for the life of me get flask_socketio to subscribe to redis pub/sub message queue.
@sio.event
def navigate(data):
    print(f"Navigating with {data}")

def sub(name: str):
   pubsub = redis_conn.pubsub()
   pubsub.subscribe(REDIS_QUEUE_NAME)
   for message in pubsub.listen():
       print(f"NAME: {name}, Message: {message}")


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'secret-key-goes-here'

    sio.init_app(app, message_queue='redis://redis:6379/4', async_mode='gevent_uwsgi')

    # Publish events like this work fine (you can see them appear in Redis). Just no subscribing.
    sio.emit('app_created', {})

    log.error("Setting up engine processing")
    Process(target=sub, args=("reader1",)).start()
    return app
