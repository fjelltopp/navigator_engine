import pytest
import networkx
import pickle
import re
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

    @pytest.mark.parametrize('language,title,description', [
        ('en', 'Test Data Overview', 'Test Milestone'),
        ('fr', 'FRENCH Test Data Overview', 'FRENCH Test Milestone'),
        ('pt_PT', 'PORTUGUESE Test Data Overview', 'PORTUGUESE Test Milestone')
    ])
    def test_graph_translation(self, language, title, description):
        graph = model.load_graph(graph_id=1)
        assert graph.translations[language].title == title
        assert graph.translations[language].description == description

    @pytest.mark.parametrize('language,title,html_start', [
        ('en', 'Welcome to the Navigator', '<p>Welcome to the HIV Estimates Navigator.'),
        ('fr', 'FRENCH Welcome to the Navigator', '<p>FRENCH Welcome to the HIV Estimates Navigator.'),
        ('pt_PT', 'PORTUGUESE Welcome to the Navigator', '<p>PORTUGUESE Welcome to the HIV Estimates Navigator.')
    ])
    def test_action_translation(self, language, title, html_start):
        actions = model.Action.query.all()
        assert actions[0].translations[language].title == title
        pattern = re.compile(f'^{html_start}.*')
        assert pattern.match(actions[0].translations[language].html)

    @pytest.mark.parametrize('language,title', [
        ('en', 'Test Resource 1, Test resource 2, Test link'),
        ('fr', 'FRENCH Test Resource 1, Test resource 2, Test link'),
        ('pt_PT', 'PORTUGUESE Test Resource 1, Test resource 2, Test link')
    ])
    def test_resource_translation(self, language, title):
        resources = model.Resource.query.all()
        assert resources[0].translations[language].title == title

    def test_resource_url(self):
        resources = model.Resource.query.all()
        assert resources[0].url == 'https://test.org'
