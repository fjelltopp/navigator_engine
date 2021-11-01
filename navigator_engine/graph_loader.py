import navigator_engine.model as model
import csv
import logging
from flask import current_app

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


def create_demo_data():
    # Clear and reset the db
    model.db.drop_all()
    model.db.create_all()

    # Read graph data into memory
    with open(current_app.config.get('INITIAL_GRAPH_CONFIG'), newline='') as csvfile:
        data_file = csv.reader(csvfile, delimiter=';')
        row_no = 1
        milestone_dict = {}
        data_dict = {}

        for row in data_file:
            if row_no == 1:
                milestone_headers = row
            elif row_no == 2:
                for i in range(0, len(row)):
                    milestone_dict[milestone_headers[i]] = row[i]
            elif row_no == 4:
                data_headers = row
            elif row_no > 4:
                data_dict[row[0]] = {"row": row_no}
                for i in range(0, len(row)):
                    data_dict[row[0]][data_headers[i]] = row[i]
            row_no = row_no + 1

    # TODO: validate the imported graph CSV

    # Load a simple BDG
    graph = model.Graph(
        title=milestone_dict['Milestone Title'],
        version=milestone_dict['Version'],
        description=milestone_dict['Description']
    )
    model.db.session.add(graph)
    model.db.session.commit()

    # Loop through the data dictionary to create nodes, conditionals and actions
    for sheet_id in data_dict:
        row = data_dict[sheet_id]
        conditional = model.Conditional(title=row['Conditional'], function=row['ConditionalFunction'])
        model.db.session.add(conditional)
        model.db.session.commit()

        node_conditional = model.Node(
            conditional_id=conditional.id
        )

        model.db.session.add(node_conditional)
        model.db.session.commit()

        data_dict[sheet_id]['DbNodeId'] = node_conditional.id

        if row['ConditionalNo'] == 'action':
            action = model.Action(
                title=row['Action'],
                html=row['ActionHtml'],
                skippable=_map_excel_boolean(row['ActionSkippable']),
                action_url=row['ActionUrl']
            )
            model.db.session.add(action)
            model.db.session.commit()

            node_action = model.Node(
                action_id=action.id
            )
            model.db.session.add(node_action)
            model.db.session.commit()

            data_dict[sheet_id]['DbNodeActionId'] = node_action.id
            model.db.session.add(node_action)
            model.db.session.commit()

    # Loop through the data dictionary to create edges
    for sheet_id in data_dict:
        row = data_dict[sheet_id]

        if row['ConditionalYes'] == 'end':
            logging.info('End node reached')
        else:
            edge_true = model.Edge(
                graph_id=graph.id,
                from_id=row['DbNodeId'],
                to_id=data_dict[row['ConditionalYes']]['DbNodeId'],
                type=True
            )
            model.db.session.add(edge_true)
            model.db.session.commit()

        if row['ConditionalNo'] == 'action':
            edge_false = model.Edge(
                graph_id=graph.id,
                from_id=row['DbNodeId'],
                to_id=row['DbNodeActionId'],
                type=False
            )
        else:
            edge_false = model.Edge(
                graph_id=graph.id,
                from_id=row['DbNodeId'],
                to_id=data_dict[row['ConditionalNo']]['DbNodeId'],
                type=False
            )
        model.db.session.add(edge_false)
        model.db.session.commit()


def _map_excel_boolean(boolean):
    if boolean in ['TRUE', 1, "1", "T", "t", "true", "True"]:
        return True
    elif boolean in ['FALSE', 0, "0", "F", "f", "false", "False"]:
        return False
    else:
        raise ValueError('Value {} read from Initial Graph Config is not valid; Only TRUE and FALSE are valid values.'
                         .format(boolean))
