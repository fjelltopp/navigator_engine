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
                'completedTasks': [
                    "task1",
                    "task2",
                    "task3"
                ]
            }
        }
    }
    result = conditionals.check_manual_confirmation(action_id, mock_engine)
    assert result == expected


@pytest.mark.parametrize("resource_type,key,value,expected", [
    ('navigator-workflow-state', 'format', '.*JSON', True),
    ('navigator-workflow-state', 'format', 'PJNZ', False),
    ('navigator-workflow-state', 'url', '..*', True),
    ('art-data', 'title', 'ART', True),
    ('art-data', 'url', '.*', False),
    ('art-data', 'private', False, True),
    ('anc-data', 'format', 'PJNZ', False)

])
def test_check_resource_key(mock_engine, resource_type, key, value, expected):
    source_data = {
        'dataset': {
            'data': {
                'result': {
                    'name': 'test-dataset',
                    'resources': [{
                        'resource_type': 'navigator-workflow-state',
                        'title': 'Navigator Workflow State',
                        'format': 'GeoJSON',
                        'url': 'https://example.com/test-navigator-workflow-state'
                    }, {
                        'resource_type': 'art-data',
                        'title': 'ART',
                        'format': 'CSV',
                        'private': False
                    }]
                }
            }
        }
    }
    mock_engine.data = source_data
    result = conditionals.check_resource_key(resource_type, key, value, mock_engine)
    assert result == expected


@pytest.mark.parametrize("resources, expected", [
    ([{'validation_status': 'success'}, {'validation_status': 'success'}], True),
    ([{'validation_status': 'success'}, {'validation_status': 'error'}], False),
    ([{}, {'validation_status': 'failure'}], False),
])
def test_check_dataset_valid(resources, expected, mock_engine):
    with pytest.raises(TypeError, match='123'):
        conditionals.check_not_skipped(123, mock_engine)
