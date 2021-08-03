from flask import Flask
from flask_socketio import SocketIO

sio = SocketIO()

# TODO:  Can't for the life of me get flask_socketio to subscribe to redis pub/sub message queue.
@sio.event
def navigate(data):
    print(f"Navigating with {data}")


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'secret-key-goes-here'

    sio.init_app(app, message_queue='redis://redis:6379/4', async_mode='gevent_uwsgi')

    # Publish events like this work fine (you can see them appear in Redis). Just no subscribing.
    sio.emit('app_created', {})
    return app
