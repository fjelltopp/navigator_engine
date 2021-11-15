import navigator_engine.model as model
from dash import dcc
import dash_cytoscape as cyto
from dash import html
from dash.dependencies import Input, Output


graph_stylesheet = [  # Group selectors
    {
        'selector': 'node',
        'style': {
            'content': 'data(label)'
        }
    },
    {
        'selector': 'edge',
        'style': {
            # The default curve style does not work with certain arrows
            'curve-style': 'bezier',
            'target-arrow-shape': 'vee'
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
        html.Hr(),
        html.Div(
            id='cytoscape-container',
            children=[
                cyto.Cytoscape(
                    id='cytoscape-figure',
                    layout={'name': 'preset'},
                    style={'width': '100%', 'height': '400px'},
                    elements=[
                    ])
            ]
        ),
        html.Hr(),
        html.P(
            id='tapNodeData-output',
            children=['Click a node to see more information about it']
        ),
    ])

    @dash_app.callback(
        Output('tapNodeData-output', 'children'),
        Input('cytoscape-figure', 'tapNodeData'))
    def display_tap_node_data(data):
        if data:
            return [data['infobox']]

    @dash_app.callback(
        Output(component_id='cytoscape-container', component_property='children'),
        Input(component_id='graph-selector', component_property='value'))
    def update_figure(graph_id):

        with flask_app.app_context():
            graph = model.load_graph(graph_id=graph_id)
            graph_x = graph.to_networkx()

        root_nodes = [n for n, d in graph_x.in_degree() if d == 0]
        assert len(root_nodes) == 1

        elements = []
        for n in graph_x.nodes:
            node = model.load_node(node_id=n.id)
            if node.action:
                node_element = {'data': {'id': str(node.id),
                                         'label': f'A {node.action.id}',
                                         'infobox': f'Action {node.action.id} | '
                                                    f'Node {node.id} | '
                                                    f'{node.action.title}'
                                         },
                                'classes': 'red triangle'
                                }
            elif node.milestone:
                node_element = {'data': {'id': str(node.id),
                                         'label': f'M {node.milestone.id}',
                                         'infobox': f'Milestone {node.milestone.id} | '
                                                    f'Node {node.id}  | '
                                                    f'{node.milestone.title}'
                                         },
                                'classes': 'blue square'
                                }
            elif node.conditional:
                node_element = {'data': {'id': str(node.id),
                                         'label': f'C {node.conditional.id}',
                                         'infobox': f'Conditional '
                                                    f'{node.conditional.id} | '
                                                    f'Node {node.id}  | '
                                                    f'{node.conditional.title}'
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
            id='cytoscape-figure',
            layout={'name': 'breadthfirst',
                    'roots': f'[id = "{root_nodes[0].id}"]'},
            style={'width': '100%', 'height': '400px'},
            stylesheet=graph_stylesheet,
            elements=elements
        )

        return [fig]

    return dash_app

