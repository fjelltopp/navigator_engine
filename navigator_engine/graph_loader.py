import navigator_engine.model as model
import logging
from flask import current_app
import os
import numpy as np
import pandas as pd
import re

MILESTONE_COLUMNS = {
    'TITLE': 'Milestone Title',
    'VERSION': 'Version',
    'DESCRIPTION': 'Description'
}

DATA_COLUMNS = {
    'CONDITIONAL': 'Task Test',
    'ACTION': 'Action Title (if test fails)',
    'SKIPPABLE': 'Mandatory to proceed?',
    'SKIP_TO': 'Proceed to test (if test fails)'
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
        xl = pd.ExcelFile(current_app.config.get('INITIAL_GRAPH_CONFIG'))
        p = re.compile('[\d]{2,2}-')

        for sheet_name in xl.sheet_names:

            if p.match(sheet_name):
                graph_header = pd.read_excel(current_app.config.get('INITIAL_GRAPH_CONFIG'),
                                             sheet_name=sheet_name,
                                             header=0
                                             ).loc[0][0:4]
                graph_data = pd.read_excel(current_app.config.get('INITIAL_GRAPH_CONFIG'),
                                           sheet_name=sheet_name,
                                           header=3,
                                           index_col=0
                                           )
                import_data(graph_header, graph_data)

    else:
        raise ValueError('File extension of Initial Graph Config must be XLSX or CSV')


def import_data(graph_header, graph_data):

    # TODO: validate the imported graph

    # Load a simple BDG
    graph = model.Graph(
        title=graph_header[MILESTONE_COLUMNS['TITLE']],
        version=graph_header[MILESTONE_COLUMNS['VERSION']],
        description=graph_header[MILESTONE_COLUMNS['DESCRIPTION']]
    )
    model.db.session.add(graph)
    model.db.session.commit()

    # Add new columns for references to database primary keys
    graph_data.insert(0, 'DbNodeId', None)
    graph_data.insert(1, 'DbActionNodeId', None)

    # Loop through the graph dataframe to create nodes, conditionals and actions
    for idx in graph_data.index:
        conditional = model.Conditional(
            title=graph_data.loc[idx, DATA_COLUMNS['CONDITIONAL']]
        )
        model.db.session.add(conditional)
        model.db.session.commit()

        node_conditional = model.Node(
            conditional_id=conditional.id
        )

        model.db.session.add(node_conditional)
        model.db.session.commit()

        graph_data.at[idx, 'DbNodeId'] = node_conditional.id

        # If Conditional is False, add an action node if no skip destination is given
        if graph_data.loc[:, DATA_COLUMNS['SKIP_TO']].isnull().loc[idx]:
            action = model.Action(
                title=graph_data.at[idx, DATA_COLUMNS['ACTION']],
                skippable=_map_excel_boolean(graph_data.at[idx, DATA_COLUMNS['SKIPPABLE']])
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

    # Add a completion action
    complete_action = model.Action(
        title='{} complete!'.format(graph_header[MILESTONE_COLUMNS['TITLE']]),
        html='Well done.  You have completed the milestone <milestone_title>.  Time to move on to the next one...'
            .format(graph_header[MILESTONE_COLUMNS['TITLE']]),
        skippable=False
    )
    model.db.session.add(complete_action)
    model.db.session.commit()


    # Loop through the graph dataframe to create edges
    for idx in graph_data.index:

        if graph_data.iloc[-1, :].equals(graph_data.loc[idx, :]):
            logging.info('End node reached')

        else:
            edge_true = model.Edge(
                graph_id=graph.id,
                from_id=graph_data.at[idx, 'DbNodeId'],
                to_id=graph_data.iloc[graph_data.index.get_loc(graph_data.loc[idx].name) + 1].loc['DbNodeId'],
                type=True
            )
            model.db.session.add(edge_true)
            model.db.session.commit()

        # If Conditional is False, add an edge to the relevant action if no skip destination is given
        if graph_data.loc[:, DATA_COLUMNS['SKIP_TO']].isnull().loc[idx]:
            edge_false = model.Edge(
                graph_id=graph.id,
                from_id=graph_data.at[idx, 'DbNodeId'],
                to_id=graph_data.at[idx, 'DbNodeActionId'],
                type=False
            )
        # if skip destination is given, add an edge to its node
        else:
            edge_false = model.Edge(
                graph_id=graph.id,
                from_id=graph_data.at[idx, 'DbNodeId'],
                to_id=graph_data.at[graph_data.at[idx, DATA_COLUMNS['SKIP_TO']], 'DbNodeId'],
                type=False
            )
        model.db.session.add(edge_false)
        model.db.session.commit()


def _map_excel_boolean(boolean):
    if boolean in ['TRUE', 1, "1", "T", "t", "true", "True"]:
        return True
    elif boolean in ['FALSE', 0, "0", "F", "f", "false", "False"] or np.isnan(boolean):
        return False
    else:
        raise ValueError('Value {} read from Initial Graph Config is not valid; Only TRUE and FALSE are valid values.'
                         .format(boolean))
