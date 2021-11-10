import os
import sentry_sdk
from flask import Flask, jsonify
import flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.exceptions import HTTPException
from navigator_engine import cli
from navigator_engine.api import api_blueprint
from navigator_engine.model import db
from navigator_engine import graph_viz
import importlib
import json


def create_app(config_object=None):

    server = Flask(__name__)

    if not config_object:
        config_object = os.environ.get(
            'NAVIGATOR_ENGINE_SETTINGS',
            'navigator_engine.config.Config'
        )

    server.config.from_object(config_object)
    server.url_map.strict_slashes = False
    server.logger.setLevel(server.config.get('LOGGING_LEVEL'))

    if server.config.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=server.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        )

    db.init_app(server)
    server.register_blueprint(api_blueprint)
    cli.register(server)

    dash_app = graph_viz.get_dash_app(server)

    # Importing this code registers all the pluggable_logic for use
    importlib.import_module('navigator_engine.pluggable_logic')

    @server.route('/')
    def index():
        return jsonify({"status": "Navigator Engine Running"})

    @app.errorhandler(HTTPException)
    def error_response(e):
        response = e.get_response()
        response.data = json.dumps({
            'status_code': e.code,
            'error': e.name,
            'message': e.description
        })
        response.content_type = "application/json"
        return response

    @server.route('/graph')
    def render_dashboard():
        return flask.redirect('/graph')

    app = DispatcherMiddleware(server, {
        '/graph': dash_app.server
    })

    return app.app


app = create_app()
