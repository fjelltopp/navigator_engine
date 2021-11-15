import dash
import flask
from navigator_engine.common import graph_visualizer


def add_dash_app(navigator_app):
    dash_app = dash.Dash(__name__, server=navigator_app, url_base_pathname='/graph/')
    graph_visualizer.create_visualizer(flask_app=navigator_app, dash_app=dash_app)

    @navigator_app.route('/graph')
    def graph():
        return flask.redirect('/graph')

    return navigator_app
