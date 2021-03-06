import dash
import flask
from navigator_engine.common import graph_visualizer


def add_dash_app(navigator_app) -> flask.app.Flask:
    dash_app = dash.Dash(__name__,
                         server=navigator_app,
                         requests_pathname_prefix=f'{navigator_app.config.get("DASH_REROUTE_PREFIX")}/graph/',
                         routes_pathname_prefix='/graph/')
    graph_visualizer.create_visualizer(flask_app=navigator_app, dash_app=dash_app)

    return navigator_app
