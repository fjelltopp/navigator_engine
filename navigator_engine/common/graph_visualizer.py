import navigator_engine.model as model
from dash import dcc
import dash_cytoscape as cyto
from dash import html
from dash.dependencies import Input, Output
from flask_babel import _

# Group selectors
graph_stylesheet = [
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
        'style': {
            'width': 5
        }
    },
    {
        'selector': '.false',
        'style': {
            'line-style': 'dashed'
        }
    }
]


def create_visualizer(flask_app, dash_app) -> None:
    dash_app.layout = html.Div(children=[
        html.Div(
            id='dropdown-container',
            children=[
                dcc.Dropdown(
                    id='graph-dropdown',
                    options=[],
                    placeholder=_('Select a graph')
                )
            ]
        ),
        html.Hr(),
        html.Div(
            id='cytoscape-container',
            children=[
                cyto.Cytoscape(
                    id='cytoscape-figure',
                    layout={'name': 'preset'},
                    style={'width': '100%', 'height': '400px'},
                    elements=[]
                )
            ]
        ),
        html.Hr(),
        html.P(
            id='tapNodeData-output',
            children=[_('Click a node to see more information about it')]
        ),
    ])

    @dash_app.callback(
        Output(component_id='tapNodeData-output', component_property='children'),
        Input(component_id='cytoscape-figure', component_property='tapNodeData'))
    def display_tap_node_data(data: dict) -> list:
        if data:
            return [data['infobox']]
        else:
            return []

    @dash_app.callback(
        Output(component_id='graph-dropdown', component_property='options'),
        Input(component_id='graph-dropdown', component_property='placeholder'))
    def load_dropdown_options(placeholder) -> list:
        with flask_app.app_context():
            graphs = model.load_all_graphs()
        dropdown_options = []
        for graph in graphs:
            dropdown_options.append({
                'label': _('Graph') + f'{graph.id} | {graph.title}',
                'value': graph.id
            })

        return dropdown_options

    @dash_app.callback(
        Output(component_id='cytoscape-container', component_property='children'),
        Input(component_id='graph-dropdown', component_property='value'))
    def update_figure(graph_id: int) -> list:

        if not graph_id:
            return []

        with flask_app.app_context():
            graph = model.load_graph(graph_id=graph_id)
            graph_x = graph.to_networkx()

        root_nodes = [n for n, d in graph_x.in_degree() if d == 0]
        assert len(root_nodes) == 1

        elements = []
        for n in graph_x.nodes:
            node = model.load_node(node_id=n.id)
            if node.action and node.action.complete:
                node_element = {
                    'classes': 'red triangle',
                    'data': {
                        'id': str(node.id),
                        'label': _('%(ref)s COMPLETE', ref=node.ref),
                        'infobox':
                            _('Action %(ref)s', ref=node.ref) + ' | ' +
                            _('Node %(id)s', id=node.id) + ' | ' +
                            f'{node.action.title}'
                    }
                }
            elif node.action and not node.action.complete:
                node_element = {
                    'classes': 'red triangle',
                    'data': {
                        'id': str(node.id),
                        'label': f'{node.ref}',
                        'infobox':
                            _('Action %(ref)s', ref=node.ref) + ' | ' +
                            _('Node %(id)s', id=node.id) + ' | ' +
                            f'{node.action.title}'
                    }
                }
            elif node.milestone:
                node_element = {
                    'classes': 'blue square',
                    'data': {
                        'id': str(node.id),
                        'label': f'{node.ref}',
                        'infobox':
                            _('Milestone %(ref)s', ref=node.ref) + ' | ' +
                            _('Node %(id)s', id=node.id) + ' | ' +
                            f'{node.action.title}'
                    }
                }
            elif node.conditional:
                node_element = {
                    'classes': 'green circle',
                    'data': {
                        'id': str(node.id),
                        'label': f'{node.ref}',
                        'infobox':
                            _('Conditional %(ref)s', ref=node.ref) + ' | ' +
                            _('Node %(id)s', id=node.id) + ' | ' +
                            f'{node.action.title}'
                    }
                }
            else:
                continue

            elements.append(node_element)

        for e in graph_x.edges:
            edge = model.load_edge(from_id=e[0].id, to_id=e[1].id)
            if edge.type:
                edge_element = {
                    'classes': 'true',
                    'data': {
                        'source': str(e[0].id),
                        'target': str(e[1].id)
                    },
                }
            elif not edge.type:
                edge_element = {
                    'classes': 'false',
                    'data': {
                        'source': str(e[0].id),
                        'target': str(e[1].id)
                    },
                }
            else:
                continue

            elements.append(edge_element)

        fig = cyto.Cytoscape(
            id='cytoscape-figure',
            layout={
                'name': 'breadthfirst',
                'roots': f'[id = "{root_nodes[0].id}"]'
            },
            style={
                'width': '100%',
                'height': '400px'
            },
            stylesheet=graph_stylesheet,
            elements=elements
        )

        return [fig]

    return dash_app
