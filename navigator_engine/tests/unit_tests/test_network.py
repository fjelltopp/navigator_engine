from navigator_engine.common.network import Network
import navigator_engine.tests.factories as factories
from navigator_engine.common import DecisionError
import networkx
import pytest


def test_get_root_node(mock_network):
    nodes = [
        factories.NodeFactory(conditional=factories.ConditionalFactory(id=1), conditional_id=1),
        factories.NodeFactory(action=factories.ActionFactory(id=1), action_id=1),
        factories.NodeFactory(action=factories.ActionFactory(id=2), action_id=2)
    ]
    mock_network.networkx = networkx.DiGraph()
    mock_network.networkx.add_edges_from([
        (nodes[0], nodes[1], {'type': True}),
        (nodes[0], nodes[2], {'type': False})
    ])
    result = Network.get_root_node(mock_network)
    assert result == nodes[0]


def test_get_complete_node(mock_network):
    nodes = [
        factories.NodeFactory(id=2, action_id=1, action=factories.ActionFactory(id=1)),
        factories.NodeFactory(id=3, action_id=2, action=factories.ActionFactory(id=2)),
        factories.NodeFactory(id=4, action_id=3, action=factories.ActionFactory(id=3, complete=True))
    ]
    mock_network.networkx = networkx.DiGraph()
    mock_network.networkx.add_nodes_from(nodes)
    result = Network.get_complete_node(mock_network)
    assert result == nodes[2]


def test_get_complete_node_raises_error(mock_network):
    nodes = [
        factories.NodeFactory(id=2, action_id=1, action=factories.ActionFactory(id=1)),
        factories.NodeFactory(id=3, action_id=2, action=factories.ActionFactory(id=2)),
        factories.NodeFactory(id=4, action_id=3, action=factories.ActionFactory(id=3))
    ]
    mock_network.networkx = networkx.DiGraph()
    mock_network.networkx.add_nodes_from(nodes)
    with pytest.raises(DecisionError, match="has no complete node"):
        Network.get_complete_node(mock_network)


@pytest.mark.parametrize("current_node,expected_result", [
    (1, [9]),
    (3, [11])
])
def test_milestone_path(mock_network, simple_network, current_node, expected_result):
    network = Network(simple_network['network'])
    result = network.milestone_path(simple_network['nodes'][current_node])
    expected_milestones = [simple_network['nodes'][i] for i in expected_result]
    assert result == expected_milestones
