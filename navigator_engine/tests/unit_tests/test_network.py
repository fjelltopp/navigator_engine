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
def test_milestone_path(simple_network, current_node, expected_result):
    network = Network(simple_network['network'])
    result = network.milestone_path(simple_network['nodes'][current_node])
    expected_milestones = [simple_network['nodes'][i] for i in expected_result]
    assert result == expected_milestones


def test_get_milestones(simple_network):
    network = Network(simple_network['network'])
    result = network.get_milestones()
    result_refs = {node.ref for node in result}
    assert result_refs == {'tst-0-8-m', 'tst-0-9-m', 'tst-0-10-m'}


@pytest.mark.parametrize("source, target, expected_paths", [
    (None, None, [[1, 9, 12, 2, 3, 11, 4, 8], [1, 9, 12, 2, 10, 14, 16, 18, 8]]),
    (3, None, [[3, 11, 4, 8]]),
    (None, 17, [[1, 9, 12, 2, 10, 14, 16, 17]]),
    (9, 15, [[9, 12, 2, 10, 14, 15]])
])
def test_all_possible_paths(simple_network, source, target, expected_paths):
    network = Network(simple_network['network'])
    result = network.all_possible_paths(
        source=simple_network['nodes'].get(source),
        target=simple_network['nodes'].get(target)
    )
    expected_paths = [[simple_network['nodes'][i] for i in nodes] for nodes in expected_paths]
    assert result == expected_paths


@pytest.mark.parametrize("source, target, expected_result", [
    (None, None, [1, 9, 12, 2, 8]),
    (3, None, [3, 11, 4, 8]),
    (None, 17, [1, 9, 12, 2, 10, 14, 16, 17]),
    (9, 15, [9, 12, 2, 10, 14, 15])
])
def test_common_path(simple_network, source, target, expected_result):
    network = Network(simple_network['network'])
    result = network.common_path(
        source=simple_network['nodes'].get(source),
        target=simple_network['nodes'].get(target)
    )
    expected_result = [simple_network['nodes'][i] for i in expected_result]
    assert result == expected_result
