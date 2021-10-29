import navigator_engine.model as model
import csv
import logging
from flask import current_app


def create_demo_data():
    # Clear and reset the db
    model.db.drop_all()
    model.db.create_all()

    data = csv.DictReader(open(current_app.config.get('GRAPH_CSV'), newline=''))

    # Read graph data into memory
    data_dict = {}
    for row in data:
        keys = list(row.keys())
        data_dict[row[keys[0]]] = {}
        for col in keys[1:]:
            data_dict[row[keys[0]]][col] = row[col]

    # TODO: validate the imported graph CSV

    # Load a simple BDG
    graph = model.Graph(
        title="Upload ADR Data",
        version="0.1",
        description="Demo graph to guide people through ADR data upload")
    model.db.session.add(graph)
    model.db.session.commit()

    # Loop through the data dictionary to create nodes conditionals and actions
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
                action_url=row['ActionUrl'])
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
                type=True)
            model.db.session.add(edge_true)
            model.db.session.commit()

        if row['ConditionalNo'] == 'action':
            edge_false = model.Edge(
                graph_id=graph.id,
                from_id=row['DbNodeId'],
                to_id=row['DbNodeActionId'],
                type=False)
        else:
            edge_false = model.Edge(
                graph_id=graph.id,
                from_id=row['DbNodeId'],
                to_id=data_dict[row['ConditionalNo']]['DbNodeId'],
                type=False)
        model.db.session.add(edge_false)
        model.db.session.commit()
    foo = 1

    # edge1 = model.Edge(graph_id=graph.id, from_id=node1.id, to_id=node2.id, type=True)
    # edge2 = model.Edge(graph_id=graph.id, from_id=node1.id, to_id=node5.id, type=False)
    # edge3 = model.Edge(graph_id=graph.id, from_id=node2.id, to_id=node3.id, type=True)
    # edge4 = model.Edge(graph_id=graph.id, from_id=node2.id, to_id=node6.id, type=False)
    # edge5 = model.Edge(graph_id=graph.id, from_id=node3.id, to_id=node4.id, type=True)
    # edge6 = model.Edge(graph_id=graph.id, from_id=node3.id, to_id=node7.id, type=False)
    # edge7 = model.Edge(graph_id=graph.id, from_id=node4.id, to_id=node8.id, type=False)
    # model.db.session.add(edge1)
    # model.db.session.add(edge2)
    # model.db.session.add(edge3)
    # model.db.session.add(edge4)
    # model.db.session.add(edge5)
    # model.db.session.add(edge6)
    # model.db.session.add(edge7)
    # model.db.session.commit()


def demo_graph_etl():
    # Load the demo graph from the db
    graph = model.Graph.query.filter_by(id=1).first()

    # Convert data into a networkx Graph
    graph.to_networkx()

    # Find the decision graph root node
    root = [n for n, d in graph.network.in_degree() if d == 0]
    root = root[0]  # (there should only be one root)
    original_title = root.conditional.title
    current_app.logger.info(f"Root node {root} with title {original_title}")

    # Update the root node's title
    new_title = "Is geographic data loaded?"
    root.conditional.title = new_title

    # Write all changes made to the graph back to the db
    model.db.session.add(graph)
    model.db.session.commit()

    # Reload the graph fromt he db and check that the title of the root node is updated
    graph_reloaded = model.Graph.query.filter_by(id=1).first()
    graph_reloaded.to_networkx()
    root = [n for n, d in graph_reloaded.network.in_degree() if d == 0]
    root = root[0]
    current_app.logger.info(f"Reloaded root node {root} with title {root.conditional.title}")
    assert new_title == root.conditional.title


def _map_excel_boolean(boolean):
    if boolean == 'TRUE':
        return True
    elif boolean == 'FALSE':
        return False
    else:
        raise ValueError('Value {} read from Graph CSV is not valid; Only TRUE and FALSE are valid values.'
                         .format(boolean))

