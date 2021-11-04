import pytest
import navigator_engine.model as model
from navigator_engine.common.decision_engine import DecisionEngine
from navigator_engine.common import DecisionError
import navigator_engine.tests.util as test_util


@pytest.mark.parametrize("data, expected_node_id", [
    ({1: False, 2: True, 3: True, 4: True}, 5),
    ({1: True, 2: False, 3: True, 4: True}, 6),
    ({1: True, 2: True, 3: False, 4: True}, 7),
    ({1: True, 2: True, 3: True, 4: False}, 8),
    ({1: True, 2: True, 3: True, 4: True}, 9),
])
@pytest.mark.usefixtures('with_app_context')
def test_graph_processing(data, expected_node_id):
    test_util.create_demo_data()
    graph = model.load_graph(1)
    engine = DecisionEngine(graph, data)
    result = engine.decide()
    assert result['node_id'] == expected_node_id


@pytest.mark.parametrize("data, skip_steps, expected_node_id", [
    ({1: True, 2: False, 3: False, 4: True}, [6], 7),
    ({1: True, 2: False, 3: False, 4: False}, [6, 7], 8),
])
@pytest.mark.usefixtures('with_app_context')
def test_with_skip_steps(data, skip_steps, expected_node_id):
    test_util.create_demo_data()
    graph = model.load_graph(1)
    engine = DecisionEngine(graph, data, skip=skip_steps)
    result = engine.decide()
    assert result['node_id'] == expected_node_id


@pytest.mark.parametrize("data, skip_steps", [
    ({1: False, 2: False, 3: False, 4: False}, [5]),
    ({1: True, 2: True, 3: True, 4: True}, [9])
])
@pytest.mark.usefixtures('with_app_context')
def test_skipping_unskippable_step_raises_error(data, skip_steps):
    test_util.create_demo_data()
    graph = model.load_graph(1)
    engine = DecisionEngine(graph, data, skip=skip_steps)
    with pytest.raises(DecisionError):
        engine.decide()
