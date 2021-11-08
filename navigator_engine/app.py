import os
import sentry_sdk
from flask import Flask
from sentry_sdk.integrations.flask import FlaskIntegration

from navigator_engine.api import api_blueprint
from navigator_engine.model import db
from navigator_engine.graph_loader import graph_loader


def create_app(config_object=None):

    app = Flask(__name__)

    if not config_object:
        config_object = os.getenv('CONFIG_OBJECT', 'navigator_engine.config.Config')

    app.config.from_object(config_object)
    app.config.from_envvar('NAVIGATOR_ENGINE_SETTINGS', silent=True)
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

    with app.app_context():
        graph_loader()

    @app.route('/')
    def index():
        return "Navigator Engine Running"

    return app


app = create_app()
