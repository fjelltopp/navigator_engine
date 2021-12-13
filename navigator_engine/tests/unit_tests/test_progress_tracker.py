from navigator_engine.common.progress_tracker import ProgressTracker
from navigator_engine.common.network import Network
import navigator_engine.tests.factories as factories
import networkx
import pytest


@pytest.mark.parametrize("completed", [True, False])
def test_add_milestone(mock_tracker, mocker, completed):
    route = [factories.NodeFactory(id=1), factories.NodeFactory(id=2)]
    mock_tracker.route = route.copy()
    mock_tracker.entire_route = route.copy()
    mock_tracker.action_breadcrumbs = [
        {'actionID': 1, 'milestoneID': None},
        {'actionID': 2, 'milestoneID': None},
        {'actionID': 3, 'milestoneID': None}
    ]
    mock_tracker.skipped_actions = [2]

    action = factories.ActionFactory(complete=completed)
    milestone_route = [factories.NodeFactory(id=3), factories.NodeFactory(id=4, action=action)]
    milestone_node = factories.NodeFactory(id=5, milestone=factories.MilestoneFactory())
    milestone_tracker = mocker.Mock(spec=ProgressTracker)
    milestone_tracker.route = milestone_route.copy()
    milestone_tracker.entire_route = route.copy() + milestone_route.copy()
    milestone_tracker.action_breadcrumbs = [
        {'actionID': 4, 'milestoneID': None},
        {'actionID': 5, 'milestoneID': None},
        {'actionID': 6, 'milestoneID': None}
    ]
    milestone_tracker.skipped_actions = [2, 3]

    ProgressTracker.add_milestone(mock_tracker, milestone_node, milestone_tracker)

    if completed:
        assert mock_tracker.action_breadcrumbs == [
            {'actionID': 1, 'milestoneID': None},
            {'actionID': 2, 'milestoneID': None},
            {'actionID': 3, 'milestoneID': None},
            {'actionID': 4, 'milestoneID': milestone_node.ref},
            {'actionID': 5, 'milestoneID': milestone_node.ref},
        ]
    else:
        assert mock_tracker.action_breadcrumbs == [
            {'actionID': 1, 'milestoneID': None},
            {'actionID': 2, 'milestoneID': None},
            {'actionID': 3, 'milestoneID': None},
            {'actionID': 4, 'milestoneID': milestone_node.ref},
            {'actionID': 5, 'milestoneID': milestone_node.ref},
            {'actionID': 6, 'milestoneID': milestone_node.ref}
        ]
    assert mock_tracker.entire_route == route + milestone_route
    assert mock_tracker.skipped_actions == [2, 3]
    assert mock_tracker.milestones == [{
        'id': milestone_node.ref,
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
    mock_tracker.network = Network(simple_network['network'])
    mock_tracker.entire_route = [simple_network['nodes'][i] for i in route]
    mock_tracker.route = [simple_network['nodes'][i] for i in route]
    mock_tracker.complete_node = simple_network['nodes'][8]
    result = ProgressTracker.percentage_progress(mock_tracker)
    assert result == expected_result


@pytest.mark.parametrize("route,expected_arg", [
    ([1, 5], 1),
    ([1, 9, 12], 12),
    ([1, 9, 12, 2, 3, 6], 3)
])
def test_milestones_to_complete(mock_tracker, simple_network, route, expected_arg):
    mock_tracker.route = [simple_network['nodes'][i] for i in route]
    ProgressTracker.milestones_to_complete(mock_tracker)
    assert mock_tracker.network.milestone_path.called_once_with(expected_arg)


@pytest.mark.parametrize('function_name, manual', [
    ('check_other_confirmation("test")', False),
    ('check_manual_confirmation("test")', True)
])
def test_drop_action_breadcrumb(mock_tracker, function_name, manual):
    conditional = factories.ConditionalFactory(id=1, function=function_name)
    nodes = [
        factories.NodeFactory(id=1, conditional=conditional, conditional_id=1),
        factories.NodeFactory(id=2, conditional=factories.ConditionalFactory(id=2), conditional_id=2),
        factories.NodeFactory(id=3, action=factories.ActionFactory(id=2), action_id=2)
    ]
    mock_tracker.network.networkx = networkx.DiGraph()
    mock_tracker.network.networkx.add_edges_from([
        (nodes[0], nodes[1], {'type': True}),
        (nodes[0], nodes[2], {'type': False})
    ])
    mock_tracker.route = [nodes[0], nodes[1]]
    mock_tracker.skipped_actions = [nodes[2].ref]
    ProgressTracker.drop_action_breadcrumb(mock_tracker)
    assert mock_tracker.action_breadcrumbs == [{
        'id': nodes[2].ref,
        'milestoneID': None,
        'skipped': True,
        'manualConfirmationRequired': manual
    }]


def test_drop_action_breadcrumb_after_milestone(mock_tracker):
    # The terminus node may be an action node immediately following a milestone
    # This regression test checks that the node is properly added to the breadcrumbs
    nodes = [
        factories.NodeFactory(id=1, milestone=factories.MilestoneFactory()),
        factories.NodeFactory(id=2, action=factories.ActionFactory(id=2, complete=True), action_id=2)
    ]
    mock_tracker.network.networkx = networkx.DiGraph()
    mock_tracker.network.networkx.add_edges_from([
        (nodes[0], nodes[1], {'type': True}),
    ])
    mock_tracker.route = nodes
    ProgressTracker.drop_action_breadcrumb(mock_tracker)
    assert mock_tracker.action_breadcrumbs == [{
        'id': nodes[1].ref,
        'milestoneID': None,
        'skipped': False,
        'manualConfirmationRequired': False
    }]


def test_report_progress(mocker, mock_tracker):
    node = factories.NodeFactory(id=1, milestone=factories.MilestoneFactory())
    milestone_tracker = mocker.Mock(spec=ProgressTracker)
    milestone_tracker.percentage_progress.return_value = 70
    mock_tracker.milestones = [
        {'id': '2-m', 'title': 'Mock', 'completed': False, 'progress': milestone_tracker}
    ]
    mock_tracker.percentage_progress.return_value = 50
    mock_tracker.milestones_to_complete.return_value = [node], False

    result = ProgressTracker.report_progress(mock_tracker)
    assert result == {
        'progress': 50,
        'currentMilestoneID': '2-m',
        'milestoneListFullyResolved': False,
        'milestones': [
            {'id': '2-m', 'title': 'Mock', 'completed': False, 'progress': 70},
            {'id': node.ref, 'title': node.milestone.title, 'progress': 0, 'completed': False}
        ]
    }
