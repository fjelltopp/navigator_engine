import logging
from flask import Flask

from . import pubsub

log = logging.getLogger(__name__)

@pubsub.subscribe
def navigate(message):
    print(f"Print message: {message}")


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'secret-key-goes-here'
    pubsub.publish('app_created', '{"message": "navigator engine has started"}')
    return app
