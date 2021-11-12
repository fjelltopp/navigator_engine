import dash
import flask
from navigator_engine import graph_viz


def add_dash_app(navigator_app):
    dash_app = dash.Dash(__name__, server=navigator_app, url_base_pathname='/graph/')
    dash_app = graph_viz.get_dash_app(flask_app=navigator_app, dash_app=dash_app)

    @navigator_app.route('/graph')
    def graph():
        return flask.redirect('/graph')

    return navigator_app
