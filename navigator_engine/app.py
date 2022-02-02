import os
import sentry_sdk
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.exceptions import HTTPException
from navigator_engine import cli
from navigator_engine.api import api_blueprint
from navigator_engine.model import db
from navigator_engine.common import dash_app
from navigator_engine.healthz import healthz_bp
import importlib
import json
import json_logging
from flask_babel import Babel, _


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
    if app.config['JSON_LOGGING']:
        json_logging.init_flask(enable_json=app.config['JSON_LOGGING'])
        json_logging.init_request_instrument(app)
    if app.config.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            environment=app.config["ENV_TYPE"],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        )

    babel = Babel(app)

    db.init_app(app)
    app.register_blueprint(api_blueprint)
    cli.register(app)

    # Importing this code registers all the pluggable_logic for use
    importlib.import_module('navigator_engine.pluggable_logic')

    app.register_blueprint(healthz_bp)

    @app.route('/')
    def index():
        return jsonify({"status": _("Navigator Engine Running")})

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

    @babel.localeselector
    def get_locale():
        return request.accept_languages.best_match(app.config['LANGUAGES'])

    return app


app = create_app()
app = dash_app.add_dash_app(app)
