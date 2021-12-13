import navigator_engine.common.action_list as action_list
import navigator_engine.tests.factories as factories
from navigator_engine.common.network import Network
import networkx
import pytest


@pytest.mark.parametrize('sources, expected_result', [
    (
        [], (
            [{'id': 'tst-0-4-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'mini-2', 'milestoneID': 'tst-0-8-m', 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'tst-0-12-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'tst-0-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}],
            False
        )
    ),
    (
        [12], (
            [{'id': 'tst-0-12-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'tst-0-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}],
            False
        )
    ),
    (
        [14], (
            [{'id': 'tst-0-14-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'tst-0-16-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'tst-0-18-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'tst-0-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}],
            True
        )
    ),
    (
        [3], (
            [{'id': 'tst-0-5-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'mini-2', 'milestoneID': 'tst-0-10-m', 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'tst-0-6-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'tst-0-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}],
            True
        )
    ),
    (
        [9, 20], (
            [{'id': 'mini-2', 'milestoneID': 'tst-0-8-m', 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'tst-0-12-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
             {'id': 'tst-0-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}],
            False
        )
    )
])
def test_step_through_common_path(mocker, simple_network, sources, expected_result):
    mini_network = networkx.DiGraph()
    nodes = [
        factories.NodeFactory(id=20, conditional=factories.ConditionalFactory(id=1), conditional_id=1),
        factories.NodeFactory(id=21, action=factories.ActionFactory(id=1, complete=True), action_id=1, ref='mini-1'),
        factories.NodeFactory(id=22, action=factories.ActionFactory(id=2), action_id=2, ref='mini-2')
    ]
    mini_network.add_edges_from([
        (nodes[0], nodes[1], {'type': True}),
        (nodes[0], nodes[2], {'type': False})
    ])

    mock_graph = mocker.Mock()
    mock_graph.to_networkx.return_value = mini_network
    mock_load_graph = mocker.patch(
        'navigator_engine.common.action_list.model.load_graph',
        return_value=mock_graph
    )

    all_nodes = simple_network['nodes']
    for node in nodes:
        all_nodes[node.id] = node

    sources = [all_nodes[node_id] for node_id in sources]
    network = Network(simple_network['network'])
    result = action_list.step_through_common_path(network, sources=sources)

    assert mock_load_graph.called_once_with(1)
    assert result[0].action_breadcrumbs == expected_result[0]
    assert result[1] == expected_result[1]


@pytest.mark.parametrize('milestone_id', [(None), ('milestone-id')])
def test_create_action_list(mock_engine, mock_tracker, mocker, milestone_id):
    mock_engine.progress.action_breadcrumbs = [
        {'id': 'tst-0-14-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
        {'id': 'tst-0-16-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
        {'id': 'tst-0-18-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
    ]
    mock_engine.progress.report = {'currentMilestoneID': milestone_id}
    mock_engine.progress.entire_route = [
        factories.NodeFactory(),
        factories.NodeFactory(action=factories.ActionFactory())
    ]
    mock_tracker.action_breadcrumbs = [
        {'id': 'tst-0-18-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
        {'id': 'tst-0-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}
    ]
    milestone_node = factories.NodeFactory(ref=milestone_id, milestone=factories.MilestoneFactory())

    def side_effect(node_ref=""):
        if node_ref == milestone_id:
            return milestone_node
        else:
            action = factories.ActionFactory(title=node_ref.upper())
            return factories.NodeFactory(action=action)
    mock_load_node = mocker.patch(
        'navigator_engine.common.action_list.model.load_node',
        side_effect=side_effect
    )
    mock_step_through_common_path = mocker.patch(
        'navigator_engine.common.action_list.step_through_common_path',
        return_value=(mock_tracker, False)
    )
    result = action_list.create_action_list(mock_engine)
    expected_result = [{
        'id': 'tst-0-14-a',
        'milestoneID': None,
        'skipped': False,
        'manualConfirmationRequired': False,
        'title': 'TST-0-14-A',
        'reached': True
    }, {
        'id': 'tst-0-16-a',
        'milestoneID': None,
        'skipped': False,
        'manualConfirmationRequired': False,
        'title': 'TST-0-16-A',
        'reached': True
    }, {
        'id': 'tst-0-18-a',
        'milestoneID': None,
        'skipped': False,
        'manualConfirmationRequired': False,
        'title': 'TST-0-18-A',
        'reached': True
    }, {
        'id': 'tst-0-7-a',
        'milestoneID': None,
        'skipped': False,
        'manualConfirmationRequired': False,
        'title': 'TST-0-7-A',
        'reached': False
    }]
    expected_sources = [mock_engine.progress.entire_route[-2]]
    if milestone_id:
        expected_sources = [milestone_node, mock_engine.progress.entire_route[-2]]
        mock_load_node.assert_any_call(node_ref=milestone_id)
    mock_step_through_common_path.assert_called_once_with(
        mock_engine.network,
        sources=expected_sources
    )
    for breadcrumb in expected_result:
        mock_load_node.assert_any_call(node_ref=breadcrumb['id'])
    assert result[0] == expected_result
    assert not result[1]
