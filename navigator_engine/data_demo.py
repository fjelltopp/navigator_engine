import navigator_engine.model as model
from flask import current_app


def create_demo_data():
    # Clear and reset the db
    model.db.drop_all()
    model.db.create_all()

    # Load a simple BDG
    graph = model.Graph(title="Upload ADR Data", version="0.1", description="Demo graph to guide people through ADR data upload")
    model.db.session.add(graph)
    model.db.session.commit()

    conditional1 = model.Conditional(title="Check if GeoJSON uploaded", function="check_resource_exists('inputs-geographic')")
    conditional2 = model.Conditional(title="Check if GeoJSON valid", function="check_resource_valid('inputs-geographic')")
    conditional3 = model.Conditional(title="Check if Survey data uploaded", function="check_resource_exists('inputs-survey')")
    conditional4 = model.Conditional(title="Check if Survey data valid", function="check_resource_valid('inputs-survey')")
    model.db.session.add(conditional1)
    model.db.session.add(conditional2)
    model.db.session.add(conditional3)
    model.db.session.add(conditional4)
    model.db.session.commit()

    action1 = model.Action(title="Upload your geographic data", html="Upload geographic data html", skippable=False, action_url="url")
    action2 = model.Action(title="Validate your geographic data", html="Validate geographic data html", skippable=False, action_url="url")
    action3 = model.Action(title="Upload your survey data", html="Upload survey data html", skippable=False, action_url="url")
    action4 = model.Action(title="Validate your survey data", html="Validate survey data html", skippable=False, action_url="url")
    model.db.session.add(action1)
    model.db.session.add(action2)
    model.db.session.add(action3)
    model.db.session.add(action4)
    model.db.session.commit()

    node1 = model.Node(graph_id=graph.id, conditional_id=conditional1.id)
    node2 = model.Node(graph_id=graph.id, conditional_id=conditional2.id)
    node3 = model.Node(graph_id=graph.id, conditional_id=conditional3.id)
    node4 = model.Node(graph_id=graph.id, conditional_id=conditional4.id)
    node5 = model.Node(graph_id=graph.id, action_id=action1.id)
    node6 = model.Node(graph_id=graph.id, action_id=action2.id)
    node7 = model.Node(graph_id=graph.id, action_id=action3.id)
    node8 = model.Node(graph_id=graph.id, action_id=action4.id)
    model.db.session.add(node1)
    model.db.session.add(node2)
    model.db.session.add(node3)
    model.db.session.add(node4)
    model.db.session.add(node5)
    model.db.session.add(node6)
    model.db.session.add(node7)
    model.db.session.add(node8)
    model.db.session.commit()

    edge1 = model.Edge(graph_id=graph.id, from_id=node1.id, to_id=node2.id, type=True)
    edge2 = model.Edge(graph_id=graph.id, from_id=node1.id, to_id=node5.id, type=False)
    edge3 = model.Edge(graph_id=graph.id, from_id=node2.id, to_id=node3.id, type=True)
    edge4 = model.Edge(graph_id=graph.id, from_id=node2.id, to_id=node6.id, type=False)
    edge5 = model.Edge(graph_id=graph.id, from_id=node3.id, to_id=node4.id, type=True)
    edge6 = model.Edge(graph_id=graph.id, from_id=node3.id, to_id=node7.id, type=False)
    edge7 = model.Edge(graph_id=graph.id, from_id=node4.id, to_id=node8.id, type=False)
    model.db.session.add(edge1)
    model.db.session.add(edge2)
    model.db.session.add(edge3)
    model.db.session.add(edge4)
    model.db.session.add(edge5)
    model.db.session.add(edge6)
    model.db.session.add(edge7)
    model.db.session.commit()


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
