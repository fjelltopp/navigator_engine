import pytest
from navigator_engine import model
from navigator_engine.common.graph_loader import graph_loader


@pytest.mark.usefixtures('with_app_context')
class TestGraphLoader:

    @classmethod
    def setup_class(cls):
        graph_loader('Estimates_Navigator_BDG_Validations.xlsx')

    @classmethod
    def teardown_class(cls):
        pass

    def test_graph_import(self):
        graphs = model.Graph.query.all()

    def test_node_import(self):
        nodes = model.Node.query.all()

    def test_conditional_import(self):
        conditionals = model.Node.query.all()

    def test_action_import(self):
        actions = model.Action.query.all()

    def test_edge_import(self):
        edges = model.Edge.query.all()

