import navigator_engine.model as model
#from navigator_engine.tests import util
from dash import Dash
from sqlalchemy import select
from sqlalchemy.orm import Session
import dash_core_components as dcc
import dash_cytoscape as cyto
from dash import html
import networkx as nx
import plotly.express as px
from dash.dependencies import Input, Output


def get_dash_app(server):
    dash_app = Dash(__name__, server=server, url_base_pathname='/graph/')
    #elements = _get_graph(server)
    dash_app.layout = html.Div(children=[
        html.Div([
            "Input: ",
            dcc.Input(id='graph-selector', value='type id of graph', type='number')
        ]),
        html.Div(
            id='cytoscape',
            children=[
                cyto.Cytoscape(
                    id='cytoscape-figure',
                    layout={'name': 'preset'},
                    style={'width': '100%', 'height': '400px'},
                    elements=[
                        {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 75, 'y': 75}},
                        {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}},
                        {'data': {'source': 'one', 'target': 'two'}}
                    ])
            ]
        )
    ])

    @dash_app.callback(
        Output(component_id='cytoscape', component_property='children'),
        Input(component_id='graph-selector', component_property='value'))
    def update_figure(graph_id):

        graph = _get_graph(server, graph_id)

        fig = cyto.Cytoscape(
            id='cytoscape',
            layout={'name': 'preset'},
            style={'width': '100%', 'height': '400px'},
            elements=[
                {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 85, 'y': 75}},
                {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 210, 'y': 200}},
                {'data': {'source': 'one', 'target': 'two'}}
            ]
        )

        return fig

    return dash_app


def _get_graph(server, graph_id):
    with server.app_context():
        graph = model.load_graph(graph_id=graph_id)

    return graph
