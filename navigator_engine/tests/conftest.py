import pytest
from navigator_engine.tests.util import app
from navigator_engine.model import db
from networkx import DiGraph
import unittest.mock as mock
from navigator_engine.common.progress_tracker import ProgressTracker
import navigator_engine.tests.factories as factories


@pytest.fixture
def client(scope="module"):
    """
    Passes as a test_client to the test (as arg "client"), used to fetch
    end points from the flask app.  e.g. client.get("/")
    """
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
        yield client


@pytest.fixture(scope="module")
def with_app_context():
    """
    Runs the test within the flask app context.  This should probably be used if
    the test is failing with a RuntimeError "No application found".
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield


@pytest.fixture
def mock_tracker():
    tracker = mock.Mock(spec=ProgressTracker)
    tracker.network = mock.Mock(spec=DiGraph)
    tracker.route = []
    tracker.entire_route = []
    tracker.previous_route = []
    tracker.milestones = []
    tracker.complete_node = factories.NodeFactory()
    tracker.action_breadcrumbs = []
    return tracker


@pytest.fixture
def simple_network():
    """
    Creates a small network of conditionals [c] actions [a] and milestone [m]:

            c1
           /  \
          a5   m9
                \
                c12
                /  \
              a13   c2
                   /  \
                  c3   m10
                 /  \    \
                a6  m11  c14
                   /     /  \
                  c4   a15  c16
                 /  \       /  \
                a7   \   a17   c18
                      \        /  \
                       \     a19   \
                        \__________ a8
    """
    nodes = [
        factories.NodeFactory(id=1, conditional_id=1, conditional=factories.ConditionalFactory(id=1)),
        factories.NodeFactory(id=2, conditional_id=2, conditional=factories.ConditionalFactory(id=2)),
        factories.NodeFactory(id=3, conditional_id=3, conditional=factories.ConditionalFactory(id=3)),
        factories.NodeFactory(id=4, conditional_id=4, conditional=factories.ConditionalFactory(id=4)),
        factories.NodeFactory(id=5, action_id=1, action=factories.ActionFactory(id=1)),
        factories.NodeFactory(id=6, action_id=2, action=factories.ActionFactory(id=2)),
        factories.NodeFactory(id=7, action_id=3, action=factories.ActionFactory(id=3)),
        factories.NodeFactory(id=8, action_id=4, action=factories.ActionFactory(id=4, complete=True)),
        factories.NodeFactory(id=9, milestone_id=1, milestone=factories.MilestoneFactory(id=1)),
        factories.NodeFactory(id=10, milestone_id=2, milestone=factories.MilestoneFactory(id=2)),
        factories.NodeFactory(id=11, milestone_id=3, milestone=factories.MilestoneFactory(id=3)),
        factories.NodeFactory(id=12, conditional_id=5, conditional=factories.ConditionalFactory(id=5)),
        factories.NodeFactory(id=13, action_id=5, action=factories.ActionFactory(id=5)),
        factories.NodeFactory(id=14, conditional_id=6, conditional=factories.ConditionalFactory(id=6)),
        factories.NodeFactory(id=15, action_id=6, action=factories.ActionFactory(id=6)),
        factories.NodeFactory(id=16, conditional_id=7, conditional=factories.ConditionalFactory(id=7)),
        factories.NodeFactory(id=17, action_id=7, action=factories.ActionFactory(id=7)),
        factories.NodeFactory(id=18, conditional_id=8, conditional=factories.ConditionalFactory(id=8)),
        factories.NodeFactory(id=19, action_id=8, action=factories.ActionFactory(id=8))
    ]
    nodes = dict((n.id, n) for n in nodes)
    network = DiGraph()
    network.add_edges_from([
        (nodes[1], nodes[5], {'type': False}),
        (nodes[1], nodes[9], {'type': True}),
        (nodes[9], nodes[12], {'type': True}),
        (nodes[12], nodes[13], {'type': False}),
        (nodes[12], nodes[2], {'type': True}),
        (nodes[2], nodes[3], {'type': False}),
        (nodes[2], nodes[10], {'type': True}),
        (nodes[3], nodes[6], {'type': False}),
        (nodes[3], nodes[11], {'type': True}),
        (nodes[11], nodes[4], {'type': True}),
        (nodes[10], nodes[14], {'type': True}),
        (nodes[14], nodes[16], {'type': True}),
        (nodes[14], nodes[15], {'type': False}),
        (nodes[16], nodes[17], {'type': False}),
        (nodes[16], nodes[18], {'type': True}),
        (nodes[18], nodes[19], {'type': False}),
        (nodes[18], nodes[8], {'type': True}),
        (nodes[4], nodes[7], {'type': False}),
        (nodes[4], nodes[8], {'type': True})
    ])
    return {'network': network, 'nodes': nodes}
