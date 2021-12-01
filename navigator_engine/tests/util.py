from navigator_engine.app import create_app
import navigator_engine.model as model
import logging
import pickle

# We should only need one seperate flask app for testing, so import from here.
app = create_app('navigator_engine.config.Testing')

logger = logging.getLogger("Tests")


def create_demo_data():
    # Clear and reset the db
    model.db.drop_all()
    model.db.session.close()
    model.db.create_all()

    # Load a simple BDG
    # Code written before I learned the more concise way of creating graph data used for the 2nd graph
    graph = model.Graph(
        title="Upload ADR Data",
        version="0.1",
        description="Demo graph to guide people through ADR data upload"
    )

    nodes = [
        model.Node(conditional=model.Conditional(
            title="Check if GeoJSON uploaded",
            function="dict_value('1')"
        ), ref='tst-1-0-c'),  # id=1
        model.Node(conditional=model.Conditional(
            title="Check if GeoJSON valid",
            function="dict_value('2')"
        ), ref='tst-1-1-c'),  # id=2
        model.Node(conditional=model.Conditional(
            title="Check if Survey data uploaded",
            function="dict_value('3')"
        ), ref='tst-1-2-c'),  # id=4
        model.Node(conditional=model.Conditional(
            title="Check if Survey data valid",
            function="dict_value('4')"
        ), ref='tst-1-3-c'),  # id=6
        model.Node(action=model.Action(
            title="Upload your geographic data",
            html="Upload geographic data html",
            skippable=False,
            resources=[
                model.Resource(title="The AIDS Data Repository", url="https://adr.unaids.org")
            ]
        ), ref='tst-1-4-a'),  # id=3
        model.Node(action=model.Action(
            title="Validate your geographic data",
            html="Validate geographic data html",
            skippable=True,
            resources=[
                model.Resource(title="The AIDS Data Repository", url="https://adr.unaids.org"),
                model.Resource(title="HIV Tools", url="https://hivtools.unaids.org")
            ]
        ), ref='tst-1-5-a'),  # id= id=5
        model.Node(action=model.Action(
            title="Upload your survey data",
            html="Upload survey data html",
            skippable=True,
            resources=[
                model.Resource(title="The AIDS Data Repository", url="https://adr.unaids.org"),
                model.Resource(title="Naomi", url="https://naomi.unaids.org")
            ]
        ), ref='tst-1-6-a'),  # id=7
        model.Node(action=model.Action(
            title="Validate your survey data",
            html="Validate survey data html",
            skippable=True,
            resources=[
                model.Resource(title="HIV Tools", url="https://hivtools.unaids.org")
            ]
        ), ref='tst-1-7-a'),  # id=9
        model.Node(action=model.Action(
            title="Milestone complete",
            html="Congratulations! You've completed the milestone",
            skippable=False,
            complete=True
        ), ref='tst-1-8-a')  # id=8
    ]
    graph.edges = [
        model.Edge(graph_id=graph.id, from_node=nodes[0], to_node=nodes[1], type=True),
        model.Edge(graph_id=graph.id, from_node=nodes[0], to_node=nodes[4], type=False),
        model.Edge(graph_id=graph.id, from_node=nodes[1], to_node=nodes[2], type=True),
        model.Edge(graph_id=graph.id, from_node=nodes[1], to_node=nodes[5], type=False),
        model.Edge(graph_id=graph.id, from_node=nodes[2], to_node=nodes[3], type=True),
        model.Edge(graph_id=graph.id, from_node=nodes[2], to_node=nodes[6], type=False),
        model.Edge(graph_id=graph.id, from_node=nodes[3], to_node=nodes[8], type=True),
        model.Edge(graph_id=graph.id, from_node=nodes[3], to_node=nodes[7], type=False)
    ]
    model.db.session.add(graph)
    model.db.session.commit()

    graph_with_milestones = model.Graph(title="Demo Graph", version="0.1", description="Demo")
    nodes = [
        model.Node(conditional=model.Conditional(
            title="Conditional 1",
            function="dict_value('1')"
        ), ref='tst-2-0-c'),  # id=10
        model.Node(milestone=model.Milestone(
            title="ADR Data",
            data_loader="load_dict_value('data')",
            graph_id=1
        ), ref='tst-2-1-m'),  # id=12
        model.Node(milestone=model.Milestone(
            title="Naomi Data Review",
            data_loader="load_dict_value('naomi')",
            graph_id=3
        ), ref='tst-2-6-m'),  # id=14
        model.Node(conditional=model.Conditional(
            title="Conditional 2",
            function="dict_value('2')"
        ), ref='tst-2-2-c'),  # id=13
        model.Node(action=model.Action(
            title="Action 1",
            html="Action 1 HTML"
        ), ref='tst-2-3-a'),  # id=11
        model.Node(action=model.Action(
            title="Action 2",
            html="Action 2 HTML",
            resources=[model.Resource(title="Naomi", url="https://naomi.unaids.org")]
        ), ref='tst-2-4-a'),  # id=15
        model.Node(action=model.Action(
            title="Complete",
            html="Milestone Complete",
            complete=True
        ), ref='tst-2-5-a'),  # id=16
    ]
    graph_with_milestones.edges = [
        model.Edge(from_node=nodes[0], to_node=nodes[4], type=False),
        model.Edge(from_node=nodes[0], to_node=nodes[1], type=True),
        model.Edge(from_node=nodes[1], to_node=nodes[2], type=True),
        model.Edge(from_node=nodes[2], to_node=nodes[3], type=True),
        model.Edge(from_node=nodes[3], to_node=nodes[5], type=False),
        model.Edge(from_node=nodes[3], to_node=nodes[6], type=True)
    ]
    model.db.session.add(graph_with_milestones)
    model.db.session.commit()

    graph_naomi = model.Graph(title="Naomi Data Review", version="0.1", description="Demo")
    nodes = [
        model.Node(conditional=model.Conditional(
            title="Conditional 1",
            function="dict_value('1')"
        ), ref='tst-3-0-c'),  # id=17
        model.Node(action=model.Action(
            title="Naomi Action 1",
            html="Naomi Action 1 HTML",
            skippable=False
        ), ref='tst-3-1-a'),  # id=18
        model.Node(action=model.Action(
            title="Complete",
            html="Milestone Complete",
            complete=True
        ), ref='tst-3-2-a'),  # id=19
    ]
    graph_naomi.edges = [
        model.Edge(from_node=nodes[0], to_node=nodes[1], type=False),
        model.Edge(from_node=nodes[0], to_node=nodes[2], type=True)
    ]
    model.db.session.add(graph_naomi)
    model.db.session.commit()


def update_test_data_from_db():
    """
    This function can be manually called when the test graph requires updating. It will fetch all the graphs
    in the database into an array of Graph objects and dump the array into a pickle file.

    The function is not intended to be called as a part of normal navigator engine usage or tests.
    """
    graphs = model.Graph.query.all()
    graph_storage = {}

    for graph in graphs:
        graph_storage[str(graph.id)] = graph.to_networkx()
    with open(f'{app.config.get("DECISION_GRAPH_FOLDER")}/graph_test_data.p', 'wb') as f:
        pickle.dump(graph_storage, f)
