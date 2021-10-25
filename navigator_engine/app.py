import os
import sentry_sdk
from flask import Flask
from flask_restful import Api
from sentry_sdk.integrations.flask import FlaskIntegration
from navigator_engine.api_resources.whats_next import WhatsNext
from navigator_engine.api_resources.decision_graph import DecisionGraph
from navigator_engine.api_resources.conditional import Conditional
from navigator_engine.api_resources.action import Action

app = Flask(__name__)

config_object = os.getenv('CONFIG_OBJECT', 'navigator_engine.config.Development')
app.config.from_object(config_object)
app.config.from_envvar('NAVIGATOR_ENGINE_SETTINGS', silent=True)

if app.config.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=app.config["SENTRY_DSN"],
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0
    )


api = Api(app)
api.add_resource(WhatsNext, "/whatsnext")
api.add_resource(DecisionGraph, "/decisiongraph")
api.add_resource(Conditional, "/conditional")
api.add_resource(Action, "/action")


@app.route('/')
def index():
    return "Navigator Engine Running"
