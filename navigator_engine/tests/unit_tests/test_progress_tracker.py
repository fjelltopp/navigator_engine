from navigator_engine.common.progress_tracker import ProgressTracker
from navigator_engine.common import DecisionError
import navigator_engine.tests.factories as factories
import networkx
import pytest


def test_add_node(mock_tracker):
    node = factories.NodeFactory(id=2)
    ProgressTracker.add_node(mock_tracker, node)
    assert mock_tracker.entire_route == [node]
    assert mock_tracker.route == [node]


def test_pop_node(mock_tracker):
    nodes = [
        factories.NodeFactory(id=2),
        factories.NodeFactory(id=3),
        factories.NodeFactory(id=4)
    ]
    mock_tracker.entire_route = nodes.copy()
    mock_tracker.route = [nodes[-1]]
    result = ProgressTracker.pop_node(mock_tracker)
    assert result == nodes[-1]
    assert mock_tracker.entire_route == nodes[:-1]
    assert mock_tracker.route == []


def test_reset(mock_tracker):
    nodes = [
        factories.NodeFactory(id=2),
        factories.NodeFactory(id=3),
        factories.NodeFactory(id=4)
    ]
    mock_tracker.entire_route = nodes.copy()
    mock_tracker.previous_route = nodes[0:2].copy()
    mock_tracker.route = [nodes[2]]
    ProgressTracker.reset(mock_tracker)
    assert mock_tracker.entire_route == nodes[0:2]
    assert mock_tracker.route == []


def test_get_complete_node(mock_tracker):
    nodes = [
        factories.NodeFactory(id=2, action_id=1, action=factories.ActionFactory(id=1)),
        factories.NodeFactory(id=3, action_id=2, action=factories.ActionFactory(id=2)),
        factories.NodeFactory(id=4, action_id=3, action=factories.ActionFactory(id=3, complete=True))
    ]
    mock_tracker.network = networkx.DiGraph()
    mock_tracker.network.add_nodes_from(nodes)
    result = ProgressTracker.get_complete_node(mock_tracker)
    assert result == nodes[2]


def test_get_complete_node_raises_error(mock_tracker):
    nodes = [
        factories.NodeFactory(id=2, action_id=1, action=factories.ActionFactory(id=1)),
        factories.NodeFactory(id=3, action_id=2, action=factories.ActionFactory(id=2)),
        factories.NodeFactory(id=4, action_id=3, action=factories.ActionFactory(id=3))
    ]
    mock_tracker.network = networkx.DiGraph()
    mock_tracker.network.add_nodes_from(nodes)
    with pytest.raises(DecisionError, match="has no complete node"):
        ProgressTracker.get_complete_node(mock_tracker)


@pytest.mark.parametrize("route,expected_result", [
    ([1, 5], 0),
    ([1, 9, 12, 13], 25),
    ([1, 9, 12, 2, 3, 6], 57),
    ([1, 9, 12, 2, 3, 11, 4, 7], 86),
    ([1, 9, 12, 2, 10, 14, 15], 62),
    ([1, 9, 12, 2, 10, 14, 16, 18, 19], 88),
    ([1, 9, 12, 2, 10, 14, 16, 18, 8], 100)
])
def test_percentage_progress(mock_tracker, simple_network, route, expected_result):
    mock_tracker.network = simple_network['network']
    mock_tracker.entire_route = [simple_network['nodes'][i] for i in route]
    mock_tracker.route = [simple_network['nodes'][i] for i in route]
    mock_tracker.complete_node = simple_network['nodes'][8]
    result = ProgressTracker.percentage_progress(mock_tracker)
    assert result == expected_result


@pytest.mark.parametrize("route,expected_result", [
    ([1, 5], ([9], False)),
    ([1, 9, 12, 2, 3, 6], ([11], True))
])
def test_milestones_to_complete(mock_tracker, simple_network, route, expected_result):
    mock_tracker.network = simple_network['network']
    mock_tracker.entire_route = [simple_network['nodes'][i] for i in route]
    mock_tracker.route = [simple_network['nodes'][i] for i in route]
    mock_tracker.complete_node = simple_network['nodes'][8]
    result = ProgressTracker.milestones_to_complete(mock_tracker)
    expected_milestones = [simple_network['nodes'][i] for i in expected_result[0]]
    assert result == (expected_milestones, expected_result[1])
