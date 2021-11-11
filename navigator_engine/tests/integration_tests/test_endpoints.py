import json
import pytest
import navigator_engine.tests.util as test_util
from requests import Response
from werkzeug.exceptions import BadRequest
"""
Endpoint tests use the client fixture, which requires the db, meaning they should
be treated as integration tests.
"""


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.data == b"Navigator Engine Running"


@pytest.mark.usefixtures('with_app_context')
def test_decide_complete(client, mocker):
    data = {
        '1': True,
        '2': True,
        'data': {'1': True, '2': True, '3': False, '4': True}
    }
    mock_response = mocker.Mock(spec=Response)
    mock_response.json.return_value = data
    mocker.patch(
        'navigator_engine.pluggable_logic.data_loaders.requests.get',
        return_value=mock_response
    )
    mocker.patch(
        'navigator_engine.api.choose_graph',
        return_value=2
    )
    test_util.create_demo_data()
    response = client.post("/api/decide", data=json.dumps({
        'data': {
            'url': 'https://example.ckan/api/3/action/package_show?id=example',
            'authorization_header': "example-api-key"
        },
        'skipActions': [5, 7]
    }))
    assert response.json == {
        'decision': {
            'id': 15,
            'content': {
                'title': 'Complete',
                'displayHTML': 'Action Complete',
                'skippable': False,
                'complete': True,
                'helpURLs': []
            }
        },
        'actions': [11, 3, 5, 7, 9, 14],
        'skippedActions': [7],
        'progress': {
            'progress': 100,
            'milestoneListFullyResolved': True,
            'milestones': [{'id': 12, 'title': 'ADR Data', 'progress': 100, 'completed': True}]
        }
    }


@pytest.mark.usefixtures('with_app_context')
def test_decide_incomplete(client, mocker):
    data = {
        '1': True,
        '2': True,
        'data': {'1': True, '2': True, '3': False, '4': True}
    }
    mock_response = mocker.Mock(spec=Response)
    mock_response.json.return_value = data
    mocker.patch(
        'navigator_engine.pluggable_logic.data_loaders.requests.get',
        return_value=mock_response
    )
    mocker.patch(
        'navigator_engine.api.choose_graph',
        return_value=2
    )
    test_util.create_demo_data()
    response = client.post("/api/decide", data=json.dumps({
        'data': {
            'url': 'https://example.ckan/api/3/action/package_show?id=example',
            'authorization_header': "example-api-key"
        },
        'skipActions': [5]
    }))
    assert response.json == {
        'actions': [11, 3, 5],
        'skippedActions': [],
        'decision': {
            'id': 7,
            'content': {
                'title': 'Upload your survey data',
                'complete': False,
                'displayHTML': 'Upload survey data html',
                'skippable': True,
                'helpURLs': [
                    {'label': 'The AIDS Data Repository', 'url': 'https://adr.unaids.org'},
                    {'label': 'Naomi', 'url': 'https://naomi.unaids.org'}
                ]
            }
        },
        'progress': {
            'milestoneListFullyResolved': True,
            'progress': 33,
            'milestones': [{'completed': False, 'id': 12, 'progress': 50, 'title': 'ADR Data'}]
        }
    }


def test_decide_without_data_raises_bad_request(client, mocker):
    response = client.post("/api/decide", data=json.dumps({}))
    assert 400 == response.status_code
    assert b"No data specified in request" in response.data


def test_decide_without_url_raises_bad_request(client, mocker):
    response = client.post("/api/decide", data=json.dumps({
        'data': {'authorization_header': 'api-key-here'}
    }))
    assert 400 == response.status_code
    assert b"No url to data specified in request" in response.data


@pytest.mark.parametrize("node_id, expected_action", [
    (11, {'skippable': False, 'complete': False, 'helpURLs': [],
          'displayHTML': 'Action 1 HTML', 'title': 'Action 1'}),
    (5, {'skippable': True, 'displayHTML': 'Validate geographic data html',
         'complete': False, 'title': 'Validate your geographic data',
         'helpURLs': [
            {'label': 'The AIDS Data Repository', 'url': 'https://adr.unaids.org'},
            {'label': 'HIV Tools', 'url': 'https://hivtools.unaids.org'}
         ]}),
    (15, {'skippable': False, 'complete': True, 'helpURLs': [],
          'displayHTML': 'Action Complete', 'title': 'Complete'})
])
@pytest.mark.usefixtures('with_app_context')
def test_action(client, mocker, node_id, expected_action):
    test_util.create_demo_data()
    response = client.get(f"/api/action/{node_id}")
    assert response.json == {'id': str(node_id), 'content': expected_action}


@pytest.mark.usefixtures('with_app_context')
def test_action_for_conditional_raises_bad_request(client, mocker):
    test_util.create_demo_data()
    response = client.get("/api/action/6")
    assert 400 == response.status_code
    assert b"Node 6 is not an action" in response.data


@pytest.mark.usefixtures('with_app_context')
def test_action_for_nonexistant_node_raises_bad_request(client, mocker):
    test_util.create_demo_data()
    response = client.get("/api/action/999")
    assert 400 == response.status_code
    assert b"Invalid node ID: 999" in response.data
