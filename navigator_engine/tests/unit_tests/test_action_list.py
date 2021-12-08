import navigator_engine.common.action_list as action_list
import navigator_engine.tests.factories as factories
from navigator_engine.common.network import Network
import networkx
import pytest


@pytest.mark.parametrize('sources, expected_breadcrumbs', [
    (
        [],
        [{'id': 'tst-0-4-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'mini-2', 'milestoneID': 'tst-0-8-m', 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'tst-0-12-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'tst-0-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}]
    ),
    (
        [12],
        [{'id': 'tst-0-12-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'tst-0-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}]
    ),
    (
        [14],
        [{'id': 'tst-0-14-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'tst-0-16-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'tst-0-18-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'tst-0-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}]
    ),
    (
        [3],
        [{'id': 'tst-0-5-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'mini-2', 'milestoneID': 'tst-0-10-m', 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'tst-0-6-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'tst-0-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}]
    ),
    (
        [9, 20],
        [{'id': 'mini-2', 'milestoneID': 'tst-0-8-m', 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'tst-0-12-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
         {'id': 'tst-0-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}]
    )
])
def test_step_through_common_path(mocker, simple_network, sources, expected_breadcrumbs):
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
    assert result.action_breadcrumbs == expected_breadcrumbs
