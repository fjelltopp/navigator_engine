import os
import sentry_sdk
from flask import Flask, jsonify
import flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import dash

from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.exceptions import HTTPException
from navigator_engine import cli
from navigator_engine.api import api_blueprint
from navigator_engine.model import db
from navigator_engine.common import graph_loader
from navigator_engine import graph_viz
import importlib
import json


def create_app(config_object=None):

    app = Flask(__name__)

    if not config_object:
        config_object = os.environ.get(
            'NAVIGATOR_ENGINE_SETTINGS',
            'navigator_engine.config.Config'
        )

    app.config.from_object(config_object)
    app.url_map.strict_slashes = False
    app.logger.setLevel(app.config.get('LOGGING_LEVEL'))

    if app.config.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        )

    db.init_app(app)
    app.register_blueprint(api_blueprint)
    cli.register(app)

    dash_app = dash.Dash(__name__, server=app, url_base_pathname='/graph/')
    dash_app = graph_viz.get_dash_app(flask_app=app, dash_app=dash_app)

    # Importing this code registers all the pluggable_logic for use
    importlib.import_module('navigator_engine.pluggable_logic')

    @app.route('/')
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

    @app.route('/graph')
    def graph():
        return flask.redirect('/graph')

    return app


app = create_app()
