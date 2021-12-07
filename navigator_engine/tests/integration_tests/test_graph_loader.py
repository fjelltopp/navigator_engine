import pytest
import networkx
import pickle
from navigator_engine import model
from navigator_engine.common.graph_loader import graph_loader
from navigator_engine.tests.util import app


@pytest.mark.usefixtures('with_app_context')
class TestGraphLoader:

    @classmethod
    def setup_class(cls):
        graph_loader(app.config.get('DEFAULT_DECISION_GRAPH'))

    @classmethod
    def teardown_class(cls):
        pass

    def test_graph_import(self):
        graphs = model.Graph.query.all()
        assert graphs

    def test_node_import(self):
        nodes = model.Node.query.all()
        assert nodes

    def test_conditional_import(self):
        conditionals = model.Node.query.all()
        assert conditionals

    def test_action_import(self):
        actions = model.Action.query.all()
        assert actions

    def test_edge_import(self):
        edges = model.Edge.query.all()
        assert edges

    def test_graph_isomorphism(self):
        graphs = model.Graph.query.all()

        with open(f'{app.config.get("DECISION_GRAPH_FOLDER")}/graph_test_data.p', 'rb') as test_data_file:
            graph_test_data = pickle.load(test_data_file)

        for graph in graphs:
            assert networkx.algorithms.isomorphism.is_isomorphic(graph.to_networkx(), graph_test_data[str(graph.id)])
