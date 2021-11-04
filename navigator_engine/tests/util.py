from navigator_engine.app import create_app
import navigator_engine.model as model
import logging


# We should only need one seperate flask app for testing, so import from here.
app = create_app('navigator_engine.config.Testing')

logger = logging.getLogger("Tests")


def create_demo_data():
    # Clear and reset the db
    model.db.drop_all()
    model.db.create_all()

    # Load a simple BDG
    graph = model.Graph(title="Upload ADR Data", version="0.1", description="Demo graph to guide people through ADR data upload")
    model.db.session.add(graph)
    model.db.session.commit()

    conditional1 = model.Conditional(title="Check if GeoJSON uploaded", function="dict_value(1)")
    conditional2 = model.Conditional(title="Check if GeoJSON valid", function="dict_value(2)")
    conditional3 = model.Conditional(title="Check if Survey data uploaded", function="dict_value(3)")
    conditional4 = model.Conditional(title="Check if Survey data valid", function="dict_value(4)")
    model.db.session.add(conditional1)
    model.db.session.add(conditional2)
    model.db.session.add(conditional3)
    model.db.session.add(conditional4)
    model.db.session.commit()

    action1 = model.Action(title="Upload your geographic data", html="Upload geographic data html", skippable=False, action_url="url")
    action2 = model.Action(title="Validate your geographic data", html="Validate geographic data html", skippable=True, action_url="url")
    action3 = model.Action(title="Upload your survey data", html="Upload survey data html", skippable=True, action_url="url")
    action4 = model.Action(title="Validate your survey data", html="Validate survey data html", skippable=True, action_url="url")
    action5 = model.Action(title="Milestone complete", html="Congratulations! You've completed the milestone", skippable=False, action_url="url", complete=True)
    model.db.session.add(action1)
    model.db.session.add(action2)
    model.db.session.add(action3)
    model.db.session.add(action4)
    model.db.session.add(action5)
    model.db.session.commit()

    node1 = model.Node(conditional_id=conditional1.id)
    node2 = model.Node(conditional_id=conditional2.id)
    node3 = model.Node(conditional_id=conditional3.id)
    node4 = model.Node(conditional_id=conditional4.id)
    node5 = model.Node(action_id=action1.id)
    node6 = model.Node(action_id=action2.id)
    node7 = model.Node(action_id=action3.id)
    node8 = model.Node(action_id=action4.id)
    node9 = model.Node(action_id=action5.id)
    model.db.session.add(node1)
    model.db.session.add(node2)
    model.db.session.add(node3)
    model.db.session.add(node4)
    model.db.session.add(node5)
    model.db.session.add(node6)
    model.db.session.add(node7)
    model.db.session.add(node8)
    model.db.session.add(node9)
    model.db.session.commit()

    edge1 = model.Edge(graph_id=graph.id, from_id=node1.id, to_id=node2.id, type=True)
    edge2 = model.Edge(graph_id=graph.id, from_id=node1.id, to_id=node5.id, type=False)
    edge3 = model.Edge(graph_id=graph.id, from_id=node2.id, to_id=node3.id, type=True)
    edge4 = model.Edge(graph_id=graph.id, from_id=node2.id, to_id=node6.id, type=False)
    edge5 = model.Edge(graph_id=graph.id, from_id=node3.id, to_id=node4.id, type=True)
    edge6 = model.Edge(graph_id=graph.id, from_id=node3.id, to_id=node7.id, type=False)
    edge7 = model.Edge(graph_id=graph.id, from_id=node4.id, to_id=node9.id, type=True)
    edge8 = model.Edge(graph_id=graph.id, from_id=node4.id, to_id=node8.id, type=False)
    model.db.session.add(edge1)
    model.db.session.add(edge2)
    model.db.session.add(edge3)
    model.db.session.add(edge4)
    model.db.session.add(edge5)
    model.db.session.add(edge6)
    model.db.session.add(edge7)
    model.db.session.add(edge8)
    model.db.session.commit()
    return graph
