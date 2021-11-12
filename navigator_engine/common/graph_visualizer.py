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


graph_stylesheet = [  # Group selectors
    {
        'selector': 'node',
        'style': {
            'content': 'data(label)'
        }
    },

    # Class selectors for nodes
    {
        'selector': '.red',
        'style': {
            'background-color': 'red',
            'line-color': 'red'
        }
    },
    {
        'selector': '.blue',
        'style': {
            'background-color': 'blue',
            'line-color': 'blue'
        }
    },
    {
        'selector': '.green',
        'style': {
            'background-color': 'green',
            'line-color': 'green'
        }
    },
    {
        'selector': '.triangle',
        'style': {
            'shape': 'triangle'
        }
    },
    {
        'selector': '.square',
        'style': {
            'shape': 'square'
        }
    },

    # Class selectors for edges
    {
        'selector': '.true',
        'style': {'width': 5}
    },
    {
        'selector': '.false',
        'style': {'line-style': 'dashed'}
    }
]


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
            node = model.load_node(node_id=n.id)
            if node.action:
                node_element = {'data': {'id': str(node.id),
                                         'label': f'A {node.action.id}'
                                         },
                                'classes': 'red triangle'
                                }
            elif node.milestone:
                node_element = {'data': {'id': str(node.id),
                                         'label': f'M {node.milestone.id}'
                                         },
                                'classes': 'blue square'
                                }
            elif node.conditional:
                node_element = {'data': {'id': str(node.id),
                                         'label': f'C {node.conditional.id}'
                                         },
                                'classes': 'green circle'
                                }
            else:
                continue

            elements.append(node_element)

        for e in graph_x.edges:
            edge = model.load_edge(from_id=e[0].id, to_id=e[1].id)
            if edge.type:
                edge_element = {'data': {'source': str(e[0].id), 'target': str(e[1].id)},
                                'classes': 'true'}
            elif not edge.type:
                edge_element = {'data': {'source': str(e[0].id), 'target': str(e[1].id)},
                                'classes': 'false'}
            else:
                continue

            elements.append(edge_element)

        fig = cyto.Cytoscape(
            id='cytoscape',
            layout={'name': 'cose'},
            style={'width': '100%', 'height': '400px'},
            stylesheet=graph_stylesheet,
            elements=elements
        )

        return [fig]

    return dash_app

