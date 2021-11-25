import navigator_engine.pluggable_logic.data_loaders as data_loaders
import json
from requests import Response
from copy import deepcopy


def test_load_empty(mock_engine):
    assert data_loaders.load_empty(mock_engine) == {}


def test_load_dict_value(mock_engine):
    mock_engine.data = {'key': 'value'}
    assert data_loaders.load_dict_value('key', mock_engine) == 'value'


def test_load_dict_from_json(mock_engine):
    test_data = {'key': 'value'}
    result = data_loaders.load_dict_from_json(
        json.dumps(test_data),
        mock_engine
    )
    assert result == test_data


def test_load_url(mock_engine, mocker):
    mock_response = mocker.Mock(spec=Response)
    mock_response.content = json.dumps({'key': 'value'})
    mock_response.status_code = 200
    mock_requests_get = mocker.patch(
        'navigator_engine.pluggable_logic.data_loaders.requests.get',
        return_value=mock_response
    )
    args = [
        'https://example.com/test-data',
        'xxxx-xxxx-xxxx-xxxx',
        'test-url',
        mock_engine
    ]
    result = data_loaders.load_url(*args)
    mock_requests_get.assert_called_once_with(args[0], headers={'Authorization': args[1]})
    assert result == {
        args[2]: {
            'source_url': args[0],
            'auth_header': {'Authorization': args[1]},
            'data': mock_response.content
        }
    }


def test_load_json_url(mock_engine, mocker):
    test_data = {'key': 'value'}
    args = [
        'https://example.com/test-data',
        'xxxx-xxxx-xxxx-xxxx',
        'test-url',
        mock_engine
    ]
    mock_load_url = mocker.patch(
        'navigator_engine.pluggable_logic.data_loaders.load_url',
        return_value={args[2]: {'data': json.dumps(test_data)}}
    )
    result = data_loaders.load_json_url(*args)
    mock_load_url.assert_called_once_with(*args)
    assert result[args[2]]['data'] == test_data


def test_estimates_dataset_core_resource(mock_engine, mocker):
    resource_url = 'https://example.com/test-navigator-workflow-state',
    auth_header = 'xxxx-xxxx-xxxx-xxxx'
    resource_type = 'navigator-workflow-state'
    source_data = {
        'dataset': {
            'url': 'https://example.com/test-data',
            'auth_header': auth_header,
            'data': {
                'success': True,
                'result': {
                    'name': 'test-dataset',
                    'resources': [{
                        'resource_type': resource_type,
                        'title': 'Navigator Workflow State',
                        'format': 'GeoJSON',
                        'url': resource_url
                    }, {
                        'resource_type': 'art-data',
                        'title': 'ART',
                        'format': 'CSV',
                        'url': 'https://example.com/test-art'
                    }]
                }
            }
        }
    }
    mock_engine.data = deepcopy(source_data)
    mock_load_json_url = mocker.patch(
        'navigator_engine.pluggable_logic.data_loaders.load_json_url',
        return_value={
            **source_data,
            **{resource_type: {'test': 'data'}}
        }
    )
    result = data_loaders.load_dataset_resource(
        resource_type,
        mock_engine
    )
    mock_load_json_url.assert_called_once_with(
        resource_url,
        auth_header,
        resource_type,
        mock_engine
    )
    assert result == mock_load_json_url.return_value


def test_load_estimates_dataset(mock_engine, mocker):
    source_data = {
        'url': 'https://example.com/test-data',
        'auth_header': 'xxxx-xxxx-xxxx-xxxx'
    }
    mock_engine.data = deepcopy(source_data)
    mock_load_json_url = mocker.patch(
        'navigator_engine.pluggable_logic.data_loaders.load_json_url'
    )
    mock_load_dataset_resource = mocker.patch(
        'navigator_engine.pluggable_logic.data_loaders.load_dataset_resource',
        return_value={
            'dataset': {
                'data': {'test': 'dataset'},
                'auth_header': 'xxxx-xxxx-xxxx-xxxx',
                'url': 'https://example.com/dataset'
            },
            'navigator-workflow-state': {
                'data': {'test': 'workflow'},
                'auth_header': 'xxxx-xxxx-xxxx-xxxx',
                'url': 'https://example.com/workflow'
            }
        }
    )
    result = data_loaders.load_estimates_dataset('url', 'auth_header', mock_engine)

    mock_load_json_url.assert_called_once_with(
        source_data['url'],
        source_data['auth_header'],
        'dataset',
        mock_engine
    )
    mock_load_dataset_resource.assert_called_once_with(
        'navigator-workflow-state',
        mock_engine
    )
    assert result == mock_load_dataset_resource.return_value


def test_load_csv_from_zipped_resource(mock_engine, mocker):

    with open('navigator_engine/tests/test_data/test_spectrum_file.pjnz', 'rb') as f:
        spectrum_file = f.read()

    mock_load_dataset_resource = mocker.patch(
        'navigator_engine.pluggable_logic.data_loaders.load_dataset_resource',
        return_value={
            'spectrum-file': {
                'data': spectrum_file,
                'auth_header': 'test-auth-header',
                'url': 'https://example.com/test-data'
            }
        }
    )
    result = data_loaders.load_csv_from_zipped_resource(
        "spectrum-file",
        "(.*)_check.CSV",
        "spectrum-file-check",
        mock_engine
    )
    mock_load_dataset_resource.assert_called_once_with(
        'spectrum-file',
        mock_engine
    )
    data = result['spectrum-file-check']['data']
    assert all(i for i in data.columns == ['Condition checked', 'Status']), \
        "Unexpected column names in Spectrum check file"
    assert data.shape == (28, 2), "Unexpected shape of Spectrum check file"


def test_load_csv_from_zipped_resource_returns_empty_on_http_error(mock_engine, mocker):

    mocker.patch(
        'navigator_engine.pluggable_logic.data_loaders.load_dataset_resource',
        return_value={
            'spectrum-file': {
                'data': None,
                'auth_header': None,
                'url': None
            }
        }
    )
    result = data_loaders.load_csv_from_zipped_resource(
        "spectrum-file",
        "(.*)_check.CSV",
        "spectrum-file-check",
        mock_engine
    )
    assert result['spectrum-file-check'] == {
        'data': None,
        'auth_header': None,
        'url': None
    }
