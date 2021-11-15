import navigator_engine.pluggable_logic.conditional_functions as conditionals
import pytest


@pytest.mark.parametrize("actions,expected,remove_skips", [
    (['1'], True, []),
    (['2'], False, ['2']),
    (['1', '2', '3'], False, ['2', '3'])
])
def test_check_not_skipped(mock_engine, actions, expected, remove_skips):
    mock_engine.progress.skipped = ['2', '3', '4']
    result = conditionals.check_not_skipped(actions, mock_engine)
    assert result == expected
    assert mock_engine.remove_skips == remove_skips


def test_check_not_skipped_raises_error(mock_engine):
    with pytest.raises(TypeError, match='123'):
        conditionals.check_not_skipped(123, mock_engine)


@pytest.mark.parametrize("action_id,expected", [
    ('task1', True),
    ('task5', False)
])
def test_check_manual_confirmation(mock_engine, action_id, expected):
    mock_engine.data = {
        'navigator-workflow-state': {
            'data': {
                'completedSteps': [
                    "task1",
                    "task2",
                    "task3"
                ]
            }
        }
    }
    result = conditionals.check_manual_confirmation(action_id, mock_engine)
    assert result == expected
