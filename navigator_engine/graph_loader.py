import navigator_engine.model as model
from navigator_engine.app import create_app
import csv
import logging
from flask import current_app
import os
import pandas as pd

MILESTONE_COLUMNS = {
    'TITLE': 'Milestone Title',
    'VERSION': 'Version',
    'DESCRIPTION': 'Description'
}

DATA_COLUMNS = {
    'CONDITIONAL': 'Conditional',
    'CONDITIONAL_FUNCTION': 'ConditionalFunction',
    'CONDITIONAL_YES': 'ConditionalYes',
    'CONDITIONAL_NO': 'ConditionalNo',
    'ACTION': 'Action',
    'SKIPPABLE': 'ActionSkippable',
    'ACTION_HTML': 'ActionHtml',
    'ACTION_URL': 'ActionUrl'
}


def graph_loader():
    # Clear and reset the db
    model.db.drop_all()
    model.db.create_all()

    split_file_name = os.path.splitext(current_app.config.get('INITIAL_GRAPH_CONFIG'))
    file_extension = split_file_name[1]

    if file_extension == '.csv':
        graph_header = pd.read_csv(current_app.config.get('INITIAL_GRAPH_CONFIG'), header=0).loc[0][0:4]
        graph_data = pd.read_csv(current_app.config.get('INITIAL_GRAPH_CONFIG'), header=3, index_col=0)
        import_data(graph_header, graph_data)

    elif file_extension == '.xlsx':
        graph_header = pd.read_csv(current_app.config.get('INITIAL_GRAPH_CONFIG'), header=0).loc[0][0:4]
        graph_data = pd.read_csv(current_app.config.get('INITIAL_GRAPH_CONFIG'), header=3, index_col=0)
        import_data(graph_header, graph_data)

    else:
        raise ValueError('File extension of Initial Graph Config must be XLSX or CSV')


def import_data(graph_header, graph_data):
    # Read graph data into memory
    data_dict = {}

    # TODO: validate the imported graph CSV

    # Load a simple BDG
    graph = model.Graph(
        title=graph_header['Milestone Title'],
        version=graph_header['Version'],
        description=graph_header['Description']
    )
    model.db.session.add(graph)
    model.db.session.commit()

    # Loop through the data dictionary to create nodes, conditionals and actions
    graph_data.insert(0, 'DbNodeId', None)
    graph_data.insert(1, 'DbActionNodeId', None)

    for idx in graph_data.index:
        conditional = model.Conditional(
            title=graph_data.loc[idx, 'Conditional'],
            function=graph_data.loc[idx, 'ConditionalFunction']
        )
        model.db.session.add(conditional)
        model.db.session.commit()

        node_conditional = model.Node(
            conditional_id=conditional.id
        )

        model.db.session.add(node_conditional)
        model.db.session.commit()

        graph_data.at[idx, 'DbNodeId'] = node_conditional.id

        if graph_data.at[idx, 'ConditionalNo'] == 'action':
            action = model.Action(
                title=graph_data.at[idx, 'Action'],
                html=graph_data.at[idx, 'ActionHtml'],
                skippable=_map_excel_boolean(graph_data.at[idx, 'ActionSkippable']),
                action_url=graph_data.at[idx, 'ActionUrl']
            )
            model.db.session.add(action)
            model.db.session.commit()

            node_action = model.Node(
                action_id=action.id
            )
            model.db.session.add(node_action)
            model.db.session.commit()

            graph_data.at[idx, 'DbNodeActionId'] = node_action.id
            model.db.session.add(node_action)
            model.db.session.commit()

    # Loop through the data dictionary to create edges
    for idx in graph_data.index:

        if graph_data.at[idx, 'ConditionalYes'] == 'end':
            logging.info('End node reached')
        else:
            edge_true = model.Edge(
                graph_id=graph.id,
                from_id=graph_data.at[idx, 'DbNodeId'],
                to_id=graph_data.at[int(graph_data.at[idx, 'ConditionalYes']), 'DbNodeId'],
                type=True
            )
            model.db.session.add(edge_true)
            model.db.session.commit()

        if graph_data.at[idx, 'ConditionalNo'] == 'action':
            edge_false = model.Edge(
                graph_id=graph.id,
                from_id=graph_data.at[idx, 'DbNodeId'],
                to_id=graph_data.at[idx, 'DbNodeActionId'],
                type=False
            )
        else:
            edge_false = model.Edge(
                graph_id=graph.id,
                from_id=graph_data.at[idx, 'DbNodeId'],
                to_id=graph_data.at[int(graph_data.at[idx, 'ConditionalNo']), 'DbNodeId'],
                type=False
            )
        model.db.session.add(edge_false)
        model.db.session.commit()
    foo = 1


def _map_excel_boolean(boolean):
    if boolean in ['TRUE', 1, "1", "T", "t", "true", "True"]:
        return True
    elif boolean in ['FALSE', 0, "0", "F", "f", "false", "False"]:
        return False
    else:
        raise ValueError('Value {} read from Initial Graph Config is not valid; Only TRUE and FALSE are valid values.'
                         .format(boolean))
