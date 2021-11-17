import pytest
import pickle
import networkx
import json
from navigator_engine import model
from navigator_engine.common.graph_loader import graph_loader
from navigator_engine.tests.util import app


@pytest.mark.usefixtures('with_app_context')
class TestGraphLoader:

    @classmethod
    def setup_class(cls):
        graph_loader(app.config.get('TEST_DATA_SPREADSHEET'))

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

    def test_network_isomorphism(self):
        graphs = model.Graph.query.all()

        network_test_data = json.loads(app.config.get('TEST_DATA_GRAPH_JSON'))

        for graph in graphs:
            network = graph.to_networkx()

            assert networkx.algorithms.isomorphism.is_isomorphic(network, network_test_data[graph.id])
