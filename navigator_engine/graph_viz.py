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


def get_dash_app(flask_app, dash_app):
    dash_app.layout = html.Div(children=[
        html.Div([
            "Input: ",
            dcc.Input(id='graph-selector', value=1, type='number')
        ]),
        html.Div(
            id='cytoscape-container',
            children=[
                cyto.Cytoscape(
                    id='cytoscape-figure',
                    layout={'name': 'preset'},
                    style={'width': '100%', 'height': '400px'},
                    elements=[
                        {'data': {'id': 'nav', 'label': 'Navigator Engine'}, 'position': {'x': 75, 'y': 75}}
                    ])
            ]
        )
    ])

    @dash_app.callback(
        Output(component_id='cytoscape-container', component_property='children'),
        Input(component_id='graph-selector', component_property='value'))
    def update_figure(graph_id):

        with flask_app.app_context():
            graph = model.load_graph(graph_id=graph_id)
            graph_x = graph.to_networkx()

        elements = []
        for n in graph_x.nodes:
            node_element = {'data': {'id': str(n.id), 'label': f'Node {n.id}'}}
            elements.append(node_element)

        for e in graph_x.edges:
            edge_element = {'data': {'source': str(e[0].id), 'target': str(e[1].id)}}
            elements.append(edge_element)

        fig = cyto.Cytoscape(
            id='cytoscape',
            layout={'name': 'cose'},
            style={'width': '100%', 'height': '400px'},
            elements=elements
        )

        return [fig]

    return dash_app

