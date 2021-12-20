import pandas as pd
import navigator_engine.pluggable_logic.conditional_functions as conditionals
import pytest


@pytest.mark.parametrize("actions,expected,remove_skips", [
    (['1'], True, []),
    (['2'], False, ['2']),
    (['1', '2', '3'], False, ['2', '3'])
])
def test_check_not_skipped(mock_engine, actions, expected, remove_skips):
    mock_engine.progress.skipped_actions = ['2', '3', '4']
    result = conditionals.check_not_skipped(actions, mock_engine)
    assert result == expected
    assert mock_engine.remove_skip_requests == remove_skips


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
                    {"id": "task1", "completedAt": "2021-12-10 15:22:12.640480"},
                    {"id": "task1", "completedAt": "2021-12-10 15:22:12.640480"},
                    {"id": "task1", "completedAt": "2021-12-10 15:22:12.640480"}
                ]
            }
        }
    }
    result = conditionals.check_manual_confirmation(action_id, mock_engine)
    assert result == expected


def test_check_manual_confirmation_for_missing_workflow_state(mock_engine):
    mock_engine.data = {'navigator-workflow-state': {'data': None}}
    result = conditionals.check_manual_confirmation('test-id', mock_engine)
    assert result is False


@pytest.mark.parametrize("resource_type,key,value,expected", [
    ('navigator-workflow-state', 'format', '.*JSON', True),
    ('navigator-workflow-state', 'format', 'PJNZ', False),
    ('navigator-workflow-state', 'url', '..*', True),
    ('art-data', 'title', 'ART', True),
    ('art-data', 'url', '.*', False),
    ('art-data', 'private', False, True),
    ('anc-data', 'format', 'PJNZ', False),
    (['art-data', 'navigator-workflow-state'], 'format', '.*', True),
    (['art-data', 'navigator-workflow-state'], 'url', '.*', False),
    (['anc-data', 'navigator-workflow-state'], 'format', '.*', False)
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


@pytest.mark.parametrize("checklist, dataframe, expected", [
    (['MaleART_current', 'AdultARTcovLT100'], pd.read_csv('spectrum_check_list.csv'), True),
    (['UAvalid', 'ARTMortNoART_default'], pd.read_csv('spectrum_check_list.csv'), False),
    (['MaleART_current', 'AdultARTcovLT100'], None, False),
    (['MaleART_current', 'CurrentYear'], pd.read_csv('spectrum_check_list.csv'), True),
    (['MaleART_current', 'This indicator does not exist'], pd.read_csv('spectrum_check_list.csv'), True)
])
def test_check_spectrum_file(checklist, dataframe, expected, mock_engine):

    mock_engine.data = {
        'spectrum-validation-file': {
            'data': dataframe
        }
    }
    check_result = conditionals.check_spectrum_file(checklist, mock_engine)
    assert check_result == expected


@pytest.mark.parametrize("checklist, dataframe, expected", [
    (['Package_created', 'Package_has_all_data'], pd.read_csv('naomi_check_list.csv'), True),
    (['Package_created', 'Opt_ANC_data'], pd.read_csv('naomi_check_list.csv'), False),
    (['Package_created', 'Package_has_all_data'], None, False),
    (['Package_created', 'Opt_ART_data'], pd.read_csv('naomi_check_list.csv'), True),
    (['Package_created', 'This indicator does not exist'], pd.read_csv('naomi_check_list.csv'), True)
])
def test_check_naomi_file(checklist, dataframe, expected, mock_engine):

    mock_engine.data = {
        'naomi-validation-file': {
            'data': dataframe
        }
    }
    check_result = conditionals.check_naomi_file(checklist, mock_engine)
    assert check_result == expected
