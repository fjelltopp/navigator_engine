from navigator_engine.common.progress_tracker import ProgressTracker
from navigator_engine.common import DecisionError
import navigator_engine.tests.factories as factories
import networkx
import pytest


def test_add_node(mock_tracker):
    node = factories.NodeFactory(id=2)
    ProgressTracker.add_node(mock_tracker, node)
    assert mock_tracker.complete_route == [node]
    assert mock_tracker.milestone_route == [node]


def test_pop_node(mock_tracker):
    nodes = [
        factories.NodeFactory(id=2),
        factories.NodeFactory(id=3),
        factories.NodeFactory(id=4)
    ]
    mock_tracker.complete_route = nodes.copy()
    mock_tracker.milestone_route = [nodes[-1]]
    result = ProgressTracker.pop_node(mock_tracker)
    assert result == nodes[-1]
    assert mock_tracker.complete_route == nodes[:-1]
    assert mock_tracker.milestone_route == []


def test_reset(mock_tracker):
    nodes = [
        factories.NodeFactory(id=2),
        factories.NodeFactory(id=3),
        factories.NodeFactory(id=4)
    ]
    mock_tracker.complete_route = nodes.copy()
    mock_tracker.previous_route = nodes[0:2].copy()
    mock_tracker.milestone_route = [nodes[2]]
    ProgressTracker.reset(mock_tracker)
    assert mock_tracker.complete_route == nodes[0:2]
    assert mock_tracker.milestone_route == []


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


def test_calculate_progress_raises_error(mock_tracker, simple_network):
    mock_tracker.network = simple_network['network']
    mock_tracker.milestone_route = [simple_network['nodes'][1]]
    with pytest.raises(DecisionError, match="Can only calculate progress for action nodes"):
        ProgressTracker.progress(mock_tracker)


@pytest.mark.parametrize("route,expected_result", [
    ([1, 5], 11),
    ([1, 9, 12, 13], 33),
    ([1, 9, 12, 2, 3, 6], 62),
    ([1, 9, 12, 2, 3, 11, 4, 7], 88),
    ([1, 9, 12, 2, 10, 14, 15], 67),
    ([1, 9, 12, 2, 10, 14, 16, 18, 8], 100)
])
def test_calculate_progress(mock_tracker, simple_network, route, expected_result):
    mock_tracker.network = simple_network['network']
    mock_tracker.complete_route = [simple_network['nodes'][i] for i in route]
    mock_tracker.milestone_route = [simple_network['nodes'][i] for i in route]
    mock_tracker.complete_node = simple_network['nodes'][8]
    result = ProgressTracker.progress(mock_tracker)
    assert result == expected_result


@pytest.mark.parametrize("route,expected_result", [
    ([1, 5], ([9], False)),
    ([1, 9, 12, 2, 3, 6], ([11], True))
])
def test_milestones_to_complete(mock_tracker, simple_network, route, expected_result):
    mock_tracker.network = simple_network['network']
    mock_tracker.complete_route = [simple_network['nodes'][i] for i in route]
    mock_tracker.milestone_route = [simple_network['nodes'][i] for i in route]
    mock_tracker.complete_node = simple_network['nodes'][8]
    result = ProgressTracker.milestones_to_complete(mock_tracker)
    expected_milestones = [simple_network['nodes'][i] for i in expected_result[0]]
    assert result == (expected_milestones, expected_result[1])
