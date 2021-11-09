from navigator_engine.common.progress_tracker import ProgressTracker
from navigator_engine.common import DecisionError
import navigator_engine.tests.factories as factories
import networkx
import pytest


@pytest.mark.parametrize("completed", [True, False])
def test_add_milestone(mock_tracker, mocker, completed):
    route = [factories.NodeFactory(id=1), factories.NodeFactory(id=2)]
    mock_tracker.route = route.copy()
    mock_tracker.entire_route = route.copy()
    mock_tracker.action_breadcrumbs = [1, 2, 3]
    mock_tracker.skipped = [2]

    milestone_route = [factories.NodeFactory(id=3), factories.NodeFactory(id=4)]
    milestone = factories.MilestoneFactory()
    milestone_tracker = mocker.Mock(spec=ProgressTracker)
    milestone_tracker.route = milestone_route.copy()
    milestone_tracker.entire_route = milestone_route.copy()
    milestone_tracker.action_breadcrumbs = [4, 5, 6]
    milestone_tracker.skipped = [3]

    ProgressTracker.add_milestone(mock_tracker, milestone, milestone_tracker, complete=completed)

    assert mock_tracker.entire_route == route + milestone_route
    assert mock_tracker.action_breadcrumbs == [1, 2, 3, 4, 5, 6]
    assert mock_tracker.skipped == [2, 3]
    assert mock_tracker.milestones == [{
        'id': 1,
        'title': 'Test Milestone',
        'progress': 100 if completed else milestone_tracker,
        'completed': completed
    }]


def test_add_node(mock_tracker):
    previous_node = factories.NodeFactory(id=1)
    node = factories.NodeFactory(id=2)

    mock_tracker.route = [previous_node]
    mock_tracker.entire_route = [previous_node]

    ProgressTracker.add_node(mock_tracker, node)

    mock_tracker.drop_action_breadcrumb.assert_called_once()
    assert mock_tracker.entire_route == [previous_node, node]
    assert mock_tracker.route == [previous_node, node]


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


def test_get_root_node(mock_tracker):
    nodes = [
        factories.NodeFactory(conditional=factories.ConditionalFactory(id=1), conditional_id=1),
        factories.NodeFactory(action=factories.ActionFactory(id=1), action_id=1),
        factories.NodeFactory(action=factories.ActionFactory(id=2), action_id=2)
    ]
    mock_tracker.network = networkx.DiGraph()
    mock_tracker.network.add_edges_from([
        (nodes[0], nodes[1], {'type': True}),
        (nodes[0], nodes[2], {'type': False})
    ])
    result = ProgressTracker.get_root_node(mock_tracker)
    assert result == nodes[0]


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


def test_drop_action_breadcrumb(mock_tracker, simple_network):
    nodes = [
        factories.NodeFactory(id=1, conditional=factories.ConditionalFactory(id=1), conditional_id=1),
        factories.NodeFactory(id=2, conditional=factories.ConditionalFactory(id=2), conditional_id=2),
        factories.NodeFactory(id=3, action=factories.ActionFactory(id=2), action_id=2)
    ]
    mock_tracker.network = networkx.DiGraph()
    mock_tracker.network.add_edges_from([
        (nodes[0], nodes[1], {'type': True}),
        (nodes[0], nodes[2], {'type': False})
    ])
    mock_tracker.route = [nodes[0], nodes[1]]
    ProgressTracker.drop_action_breadcrumb(mock_tracker)
    assert mock_tracker.action_breadcrumbs == [3]
