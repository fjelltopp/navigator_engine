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
def test_decide(client, mocker):
    data = {
        '1': True,
        '2': True,
        'data': {'1': True, '2': True, '3': False, '4': True}
    }
    mock_response = mocker.Mock(spec=Response)
    mock_response.data = json.dumps(data)
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
                'actionURL': None,
                'complete': True
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
    (11, {'skippable': False, 'actionURL': None, 'complete': False,
          'displayHTML': 'Action 1 HTML', 'title': 'Action 1'}),
    (5, {'skippable': True, 'displayHTML': 'Validate geographic data html',
         'complete': False, 'actionURL': 'url', 'title': 'Validate your geographic data'}),
    (15, {'skippable': False, 'actionURL': None, 'complete': True,
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
