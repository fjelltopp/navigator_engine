import os
import sentry_sdk
from flask import Flask
from sentry_sdk.integrations.flask import FlaskIntegration
from navigator_engine.model import db
from navigator_engine.api import api

app = Flask(__name__)

config_object = os.getenv('CONFIG_OBJECT', 'navigator_engine.config.Config')
app.config.from_object(config_object)
app.config.from_envvar('NAVIGATOR_ENGINE_SETTINGS', silent=True)
app.logger.setLevel(app.config.get('LOGGING_LEVEL'))

if app.config.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=app.config["SENTRY_DSN"],
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0
    )

db.init_app(app)
api.init_app(app)


@app.route('/')
def index():
    return "Navigator Engine Running"
