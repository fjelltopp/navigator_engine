from navigator_engine.common.decision_engine import DecisionEngine
import navigator_engine.common as common
import navigator_engine.tests.factories as factories
import networkx
import pytest


@pytest.mark.parametrize("node,function_called", [
    (factories.NodeFactory(conditional_id=1), 'process_conditional'),
    (factories.NodeFactory(action_id=1), 'process_action'),
    (factories.NodeFactory(milestone_id=1), 'process_milestone'),
])
def test_process_node(mocker, node, function_called):
    engine = mocker.Mock(spec=DecisionEngine)
    engine.progress = mocker.patch('navigator_engine.common.progress_tracker.ProgressTracker', auto_spec=True)
    DecisionEngine.process_node(engine, node)
    getattr(engine, function_called).assert_called_once_with(node)
    engine.progress.add_node.assert_called_once_with(node)


def test_run_pluggable_logic(mocker):
    def test_function(*args):
        return args
    mocker.patch.dict(
        'navigator_engine.common.CONDITIONAL_FUNCTIONS',
        {'test_function': test_function},
        clear=True
    )
    engine = mocker.Mock(spec=DecisionEngine)
    engine.data = {'key': 'value'}
    function_string = "test_function('hello', 1)"
    result = DecisionEngine.run_pluggable_logic(engine, function_string)
    assert result == ('hello', 1, engine)


@pytest.mark.parametrize("edge_type,node", [(True, 1), (False, 2)])
def test_get_next_node(mocker, edge_type, node):
    nodes = [
        factories.NodeFactory(conditional=factories.ConditionalFactory(id=1), conditional_id=1),
        factories.NodeFactory(action=factories.ActionFactory(id=1), action_id=1),
        factories.NodeFactory(action=factories.ActionFactory(id=2), action_id=2)
    ]
    network = networkx.DiGraph()
    network.add_edges_from([
        (nodes[0], nodes[1], {'type': True}),
        (nodes[0], nodes[2], {'type': False})
    ])
    engine = mocker.Mock(spec=DecisionEngine)
    engine.network = network
    engine.stop_action = None
    result = DecisionEngine.get_next_node(engine, nodes[0], edge_type)
    assert result == nodes[node]


def test_get_next_node_stop(mocker):
    nodes = [
        factories.NodeFactory(id=0, conditional=factories.ConditionalFactory(id=1), conditional_id=1),
        factories.NodeFactory(id=1, action=factories.ActionFactory(id=1), action_id=1),
        factories.NodeFactory(id=2, action=factories.ActionFactory(id=2), action_id=2)
    ]
    network = networkx.DiGraph()
    network.add_edges_from([
        (nodes[0], nodes[1], {'type': True}),
        (nodes[0], nodes[2], {'type': False})
    ])
    engine = mocker.Mock(spec=DecisionEngine)
    engine.network = network
    engine.stop_action = nodes[1].ref
    result = DecisionEngine.get_next_node(engine, nodes[0], False)
    assert result == nodes[1]


def test_get_next_node_raises_error(mocker):
    conditional = factories.ConditionalFactory(id=1, function="function")
    node = factories.NodeFactory(conditional=conditional, conditional_id=1)
    network = networkx.DiGraph()
    network.add_node(node)
    engine = mocker.Mock(spec=DecisionEngine)
    engine.network = network

    with pytest.raises(common.DecisionError, match=f"node {node.ref}"):
        DecisionEngine.get_next_node(engine, node, True)


def test_process_conditional(mocker):
    conditional = factories.ConditionalFactory(id=1, function="function()")
    node = factories.NodeFactory(conditional=conditional, conditional_id=1)
    next_node = factories.NodeFactory(action=factories.ActionFactory(id=1), action_id=1),
    engine = mocker.Mock(spec=DecisionEngine)
    engine.run_pluggable_logic.return_value = True
    engine.get_next_node.return_value = next_node
    engine.process_node.return_value = "processed_action"

    result = DecisionEngine.process_conditional(engine, node)

    assert result == "processed_action"
    engine.run_pluggable_logic.assert_called_once_with("function()")
    engine.get_next_node.assert_called_once_with(node, True)
    engine.process_node.assert_called_once_with(next_node)


def test_skip_action(mocker):
    nodes = [
        factories.NodeFactory(id=56, conditional=factories.ConditionalFactory(id=1), conditional_id=1),
        factories.NodeFactory(id=57, action=factories.ActionFactory(id=1, skippable=True), action_id=1),
        factories.NodeFactory(id=58, action=factories.ActionFactory(id=2, skippable=False), action_id=2)
    ]
    network = networkx.DiGraph()
    network.add_edges_from([
        (nodes[0], nodes[1], {'type': True}),
        (nodes[0], nodes[2], {'type': False})
    ])
    engine = mocker.Mock(spec=DecisionEngine)
    engine.progress = mocker.patch('navigator_engine.common.progress_tracker.ProgressTracker', auto_spec=True)
    engine.network = network
    engine.progress.route = [nodes[0], nodes[1]]
    engine.progress.entire_route = [nodes[0], nodes[1]]
    engine.progress.skipped = []
    engine.process_node.return_value = 'processed_action'

    result = DecisionEngine.skip_action(engine, nodes[1])

    assert result == 'processed_action'
    assert engine.progress.skipped == [nodes[1].ref]
    engine.progress.pop_node.assert_called_once()
    engine.process_node.assert_called_once_with(nodes[2])


def test_skip_action_unskippable(mocker):
    node = factories.NodeFactory(
        action_id=2,
        action=factories.ActionFactory(title="Test Action", id=2, skippable=False)
    )
    engine = mocker.Mock(spec=DecisionEngine)
    with pytest.raises(common.DecisionError, match="Action cannot be skipped"):
        DecisionEngine.skip_action(engine, node)


def test_process_milestone_incomplete(mocker, mock_engine):
    milestone = factories.MilestoneFactory()
    milestone_graph = factories.GraphFactory()
    node1 = factories.NodeFactory(milestone=milestone, milestone_id=1)
    node2 = factories.NodeFactory(action=factories.ActionFactory(id=1, complete=False), action_id=1)

    mock_engine.run_pluggable_logic.return_value = True
    mock_engine.process_action.return_value = "processed_action"
    mocker.patch('navigator_engine.model.load_graph', return_value=milestone_graph)

    milestone_engine = mocker.Mock(spec=DecisionEngine)
    milestone_engine.progress = mocker.patch(
        'navigator_engine.common.progress_tracker.ProgressTracker',
        auto_spec=True
    )
    milestone_engine.progress.route = [1, 2, 3]
    milestone_engine.decide.return_value = {'node': node2}
    mocker.patch(
        'navigator_engine.common.decision_engine.engine_factory',
        return_value=milestone_engine
    )

    result = DecisionEngine.process_milestone(mock_engine, node1)
    mock_engine.progress.add_milestone.assert_called_once_with(node1, milestone_engine.progress)
    assert result == {'node': node2}


def test_process_milestone_complete(mocker, mock_engine):
    milestone = factories.MilestoneFactory(data_loader="")
    node1 = factories.NodeFactory(milestone=milestone, milestone_id=1)
    node2 = factories.NodeFactory(action=factories.ActionFactory(id=1, complete=True), action_id=1)
    node3 = factories.NodeFactory(
        conditional=factories.ConditionalFactory(id=1),
        conditional_id=1
    )
    mock_engine.data = {'test': 'data'}
    mock_engine.run_pluggable_logic.return_value = {}
    mock_engine.get_next_node.return_value = node3
    mock_engine.process_node.return_value = "processed_action"
    mocker.patch('navigator_engine.model.load_graph')

    milestone_engine = mocker.Mock(spec=DecisionEngine)
    milestone_engine.progress = mocker.patch(
        'navigator_engine.common.progress_tracker.ProgressTracker',
        auto_spec=True
    )
    milestone_engine.progress.route = [1, 2, 3]
    milestone_engine.decide.return_value = {'node': node2}
    mocker.patch(
        'navigator_engine.common.decision_engine.engine_factory',
        return_value=milestone_engine
    )
    result = DecisionEngine.process_milestone(mock_engine, node1)

    assert result == "processed_action"
    mock_engine.progress.add_milestone.assert_called_once_with(
        node1,
        milestone_engine.progress,
        complete=True
    )
    mock_engine.get_next_node.assert_called_once_with(node1, True)
    mock_engine.process_node.assert_called_once_with(node3)


def test_decide(mocker):
    root_node = factories.NodeFactory(id=1)
    engine = mocker.Mock(spec=DecisionEngine)
    engine.data = {}
    engine.skip = []

    engine.progress = mocker.patch('navigator_engine.common.progress_tracker.ProgressTracker', auto_spec=True)
    engine.progress.root_node = root_node
    engine.progress.skipped = [1, 2, 3]
    engine.process_node.return_value = 'processed_action'
    result = DecisionEngine.decide(engine, data={'test': 'data'}, skip=[4, 5])
    engine.process_node.assert_called_once_with(root_node)
    engine.progress.reset.assert_called_once()
    assert result == 'processed_action'
    assert engine.data == {'test': 'data'}
    assert engine.skip == [4, 5]


def test_process_action_unskipped(mock_engine):
    action = factories.ActionFactory(
        id=1,
        complete=True,
        title='Test Action',
        html='Test HTML',
        skippable=True
    )
    nodes = [
        factories.NodeFactory(id=1, conditional=factories.ConditionalFactory()),
        factories.NodeFactory(id=2, action_id=1, action=action)
    ]
    mock_engine.progress.entire_route = nodes

    result = DecisionEngine.process_action(mock_engine, nodes[1])
    assert result == {
        "id": nodes[1].ref,
        "content": nodes[1].action.to_dict(),
        "node": nodes[1],
        "manualConfirmationRequired": False
    }


def test_process_action_manual(mock_engine):
    action = factories.ActionFactory(
        id=1,
        complete=True,
        title='Test Action',
        html='Test HTML',
        skippable=True
    )
    conditional = factories.ConditionalFactory(function='check_manual_confirmation()')
    nodes = [
        factories.NodeFactory(id=1, conditional=conditional),
        factories.NodeFactory(id=2, action_id=1, action=action)
    ]
    mock_engine.progress.entire_route = nodes
    result = DecisionEngine.process_action(mock_engine, nodes[1])
    assert result == {
        "id": nodes[1].ref,
        "content": nodes[1].action.to_dict(),
        "node": nodes[1],
        "manualConfirmationRequired": True
    }


def test_process_action_skipped(mocker):
    node = factories.NodeFactory(id=1)
    engine = mocker.Mock(spec=DecisionEngine)
    engine.skip = [node.ref]
    DecisionEngine.process_action(engine, node)
    engine.skip_action.assert_called_once_with(node)
