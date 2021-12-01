import pytest
import navigator_engine.model as model
from navigator_engine.common.decision_engine import DecisionEngine
import navigator_engine.tests.util as test_util


@pytest.mark.parametrize("data, expected_node_id", [
    ({'1': False, '2': True, '3': True, '4': True}, 'tst-1-4-a'),
    ({'1': True, '2': False, '3': True, '4': True}, 'tst-1-5-a'),
    ({'1': True, '2': True, '3': False, '4': True}, 'tst-1-6-a'),
    ({'1': True, '2': True, '3': True, '4': False}, 'tst-1-7-a'),
    ({'1': True, '2': True, '3': True, '4': True}, 'tst-1-8-a'),
])
@pytest.mark.usefixtures('with_app_context')
def test_graph_processing(data, expected_node_id):
    test_util.create_demo_data()
    graph = model.load_graph(1)
    engine = DecisionEngine(graph, data)
    result = engine.decide()
    assert result['id'] == expected_node_id


@pytest.mark.parametrize("data, skip_steps, expected_node_id", [
    ({'1': True, '2': False, '3': False, '4': True}, ['tst-1-5-a'], 'tst-1-6-a'),
    ({'1': True, '2': False, '3': False, '4': False}, ['tst-1-5-a', 'tst-1-6-a'], 'tst-1-7-a'),
])
@pytest.mark.usefixtures('with_app_context')
def test_with_skip_steps(data, skip_steps, expected_node_id):
    test_util.create_demo_data()
    graph = model.load_graph(1)
    engine = DecisionEngine(graph, data, skip_requests=skip_steps)
    result = engine.decide()
    assert result['id'] == expected_node_id
    assert engine.progress.skipped_actions == skip_steps


@pytest.mark.parametrize("data, skip_steps", [
    ({'1': False, '2': False, '3': False, '4': False}, ['tst-1-4-a']),
    ({'1': True, '2': True, '3': True, '4': True}, ['tst-1-8-a'])
])
@pytest.mark.usefixtures('with_app_context')
def test_skipping_unskippable_step_raises_error(data, skip_steps):
    test_util.create_demo_data()
    graph = model.load_graph(1)
    engine = DecisionEngine(graph, data, skip_requests=skip_steps)
    engine.decide()
    assert engine.remove_skip_requests == skip_steps
    assert engine.progress.skipped_actions == []
    assert engine.decision['id'] == skip_steps[0]


@pytest.mark.parametrize("data, expected_node_id", [
    ({'1': True, '2': True, 'data': {'1': True, '2': True, '3': False, '4': True}, 'naomi': {'1': True}}, 'tst-1-6-a'),
    ({'1': True, '2': True, 'data': {'1': False, '2': True, '3': True, '4': True}, 'naomi': {'1': True}}, 'tst-1-4-a'),
    ({'1': True, '2': True, 'data': {'1': True, '2': True, '3': True, '4': True}, 'naomi': {'1': True}}, 'tst-2-5-a')
])
@pytest.mark.usefixtures('with_app_context')
def test_graph_processing_with_milestones(data, expected_node_id):
    test_util.create_demo_data()
    graph = model.load_graph(2)
    engine = DecisionEngine(graph, data)
    result = engine.decide()
    assert result['id'] == expected_node_id


@pytest.mark.parametrize("data, expected_breadcrumbs", [
    ({'1': True, '2': True, 'data': {'1': True, '2': True, '3': False, '4': True}, 'naomi': {'1': True}},
     [{'id': 'tst-2-3-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-1-4-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-1-5-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-1-6-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False}]),
    ({'1': True, '2': True, 'data': {'1': False, '2': True, '3': True, '4': True}, 'naomi': {'1': True}},
     [{'id': 'tst-2-3-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-1-4-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False}]),
    ({'1': True, '2': True, 'data': {'1': True, '2': True, '3': True, '4': True}, 'naomi': {'1': True}},
     [{'id': 'tst-2-3-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-1-4-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-1-5-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-1-6-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-1-7-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-3-1-a', 'milestoneID': 'tst-2-6-m', 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-2-4-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-2-5-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}])
])
@pytest.mark.usefixtures('with_app_context')
def test_action_breadcrumbs(data, expected_breadcrumbs):
    test_util.create_demo_data()
    graph = model.load_graph(2)
    engine = DecisionEngine(graph, data)
    engine.decide()
    assert engine.progress.action_breadcrumbs == expected_breadcrumbs


@pytest.mark.parametrize("data, skip, expected_breadcrumbs", [
    ({'1': True, '2': False, '3': False, '4': True}, ['tst-1-5-a'],
     [{'id': 'tst-1-4-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-1-5-a', 'milestoneID': None, 'skipped': True, 'manualConfirmationRequired': False},
      {'id': 'tst-1-6-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}]),
    ({'1': True, '2': False, '3': False, '4': False}, ['tst-1-5-a', 'tst-1-6-a'],
     [{'id': 'tst-1-4-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-1-5-a', 'milestoneID': None, 'skipped': True, 'manualConfirmationRequired': False},
      {'id': 'tst-1-6-a', 'milestoneID': None, 'skipped': True, 'manualConfirmationRequired': False},
      {'id': 'tst-1-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}]),
    ({'1': True, '2': False, '3': False, '4': False}, ['tst-1-5-a', 'tst-1-6-a', 'tst-1-7-a'],
     [{'id': 'tst-1-4-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
      {'id': 'tst-1-5-a', 'milestoneID': None, 'skipped': True, 'manualConfirmationRequired': False},
      {'id': 'tst-1-6-a', 'milestoneID': None, 'skipped': True, 'manualConfirmationRequired': False},
      {'id': 'tst-1-7-a', 'milestoneID': None, 'skipped': True, 'manualConfirmationRequired': False},
      {'id': 'tst-1-8-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}])
])
@pytest.mark.usefixtures('with_app_context')
def test_action_breadcrumbs_with_skips(data, skip, expected_breadcrumbs):
    test_util.create_demo_data()
    graph = model.load_graph(1)
    engine = DecisionEngine(graph, data, skip_requests=skip)
    engine.decide()
    assert engine.progress.action_breadcrumbs == expected_breadcrumbs


@pytest.mark.parametrize("skip, expected_remove_skips", [
    (['tst-1-4-a', 'tst-1-5-a'], ['tst-1-4-a']),
    (['tst-1-5-a', 'tst-1-8-a'], []),
    (['tst-1-5-a', 'tst-1-6-a', 'tst-1-7-a', 'tst-1-8-a'], ['tst-1-8-a', 'tst-1-7-a'])
])
@pytest.mark.usefixtures('with_app_context')
def test_action_breadcrumbs_with_remove_skips(skip, expected_remove_skips):
    test_util.create_demo_data()
    graph = model.load_graph(1)
    data = {'1': True, '2': False, '3': False, '4': True}
    engine = DecisionEngine(graph, data, skip_requests=skip)
    engine.decide()
    assert engine.remove_skip_requests == expected_remove_skips


@pytest.mark.usefixtures('with_app_context')
def test_progress_during_milestone():
    test_util.create_demo_data()
    graph = model.load_graph(2)
    data = {
        '1': True,
        '2': True,
        'data': {'1': True, '2': True, '3': False, '4': True}
    }
    engine = DecisionEngine(graph, data)
    engine.decide()
    progress = engine.progress.report_progress()
    assert progress == {
        'progress': 25,
        'milestoneListFullyResolved': True,
        'currentMilestoneID': 'tst-2-1-m',
        'milestones': [{
            'id': 'tst-2-1-m',
            'title': 'ADR Data',
            'progress': 50,
            'completed': False
        }, {
            'completed': False,
            'id': 'tst-2-6-m',
            'progress': 0,
            'title': 'Naomi Data Review'
        }]
    }


@pytest.mark.usefixtures('with_app_context')
def test_progress_prior_milestone():
    test_util.create_demo_data()
    graph = model.load_graph(2)
    data = {
        '1': False,
        '2': True,
        'data': {'1': True, '2': True, '3': False, '4': True}
    }
    engine = DecisionEngine(graph, data)
    engine.decide()
    progress = engine.progress.report_progress()
    assert progress == {
        'progress': 0,
        'milestoneListFullyResolved': True,
        'currentMilestoneID': None,
        'milestones': [{
            'id': 'tst-2-1-m',
            'title': 'ADR Data',
            'progress': 0,
            'completed': False
        }, {
            'completed': False,
            'id': 'tst-2-6-m',
            'progress': 0,
            'title': 'Naomi Data Review'
        }]
    }


@pytest.mark.usefixtures('with_app_context')
def test_progress_after_milestone():
    test_util.create_demo_data()
    graph = model.load_graph(2)
    data = {
        '1': True,
        '2': False,
        'data': {'1': True, '2': True, '3': True, '4': True},
        'naomi': {'1': True}
    }
    engine = DecisionEngine(graph, data)
    engine.decide()
    progress = engine.progress.report_progress()
    assert progress == {
        'progress': 75,
        'milestoneListFullyResolved': True,
        'currentMilestoneID': None,
        'milestones': [{
            'id': 'tst-2-1-m',
            'title': 'ADR Data',
            'progress': 100,
            'completed': True
        }, {
            'completed': True,
            'id': 'tst-2-6-m',
            'progress': 100,
            'title': 'Naomi Data Review'
        }]
    }


@pytest.mark.usefixtures('with_app_context')
def test_skip_check_logic():
    test_util.create_demo_data()
    node = model.load_node(node_ref='tst-3-0-c')
    node.conditional.function = "check_not_skipped(['tst-1-5-a'])"
    model.db.session.add(node)
    model.db.session.commit()
    graph = model.load_graph(2)
    data = {
        '1': True,
        '2': True,
        'data': {'1': True, '2': False, '3': True, '4': True},
        'naomi': {}
    }
    engine = DecisionEngine(graph, data, skip_requests=['tst-1-5-a'])
    engine.decide()
    assert engine.decision['id'] == 'tst-3-1-a'
    assert engine.remove_skip_requests == ['tst-1-5-a']
