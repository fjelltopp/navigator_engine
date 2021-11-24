import json
import pytest
import navigator_engine.tests.util as test_util
"""
Endpoint tests use the client fixture, which requires the db, meaning they should
be treated as integration tests.
"""


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json['status'] == 'Navigator Engine Running'


@pytest.mark.usefixtures('with_app_context')
def test_decide_complete(client, mocker):
    data = {
        '1': True,
        '2': True,
        'data': {'1': True, '2': True, '3': False, '4': True}
    }
    setup_endpoint_test(mocker, data)
    response = client.post("/api/decide", data=json.dumps({
        'data': {
            'url': 'https://example.ckan/api/3/action/package_show?id=example',
            'authorization_header': "example-api-key"
        },
        'skipActions': ['tst-1-5-a', 'tst-1-6-a']
    }))
    assert response.json == {
        'decision': {
            'id': 'tst-2-5-a',
            'content': {
                'title': 'Complete',
                'displayHTML': 'Action Complete',
                'skippable': False,
                'terminus': True,
                'helpURLs': []
            }
        },
        'actions': [
            {'id': 'tst-2-3-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
            {'id': 'tst-1-4-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False},
            {'id': 'tst-1-5-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False},
            {'id': 'tst-1-6-a', 'milestoneID': 'tst-2-1-m', 'skipped': True, 'manualConfirmationRequired': False},
            {'id': 'tst-1-7-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False},
            {'id': 'tst-2-4-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
            {'id': 'tst-2-5-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False}
        ],
        'removeSkipActions': ['tst-1-5-a'],
        'progress': {
            'progress': 100,
            'currentMilestoneID': None,
            'milestoneListFullyResolved': True,
            'milestones': [{'id': 'tst-2-1-m', 'title': 'ADR Data', 'progress': 100, 'completed': True}]
        }
    }


@pytest.mark.usefixtures('with_app_context')
def test_decide_incomplete(client, mocker):
    data = {
        '1': True,
        '2': True,
        'data': {'1': True, '2': True, '3': False, '4': True}
    }
    setup_endpoint_test(mocker, data)
    response = client.post("/api/decide", data=json.dumps({
        'data': {
            'url': 'https://example.ckan/api/3/action/package_show?id=example',
            'authorization_header': "example-api-key"
        },
        'skipActions': ['tst-1-5-a']
    }))
    assert response.json == {
        'actions': [
            {'id': 'tst-2-3-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
            {'id': 'tst-1-4-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False},
            {'id': 'tst-1-5-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False},
            {'id': 'tst-1-6-a', 'milestoneID': 'tst-2-1-m', 'skipped': False, 'manualConfirmationRequired': False}
        ],
        'removeSkipActions': ['tst-1-5-a'],
        'decision': {
            'id': 'tst-1-6-a',
            'content': {
                'title': 'Upload your survey data',
                'terminus': False,
                'displayHTML': 'Upload survey data html',
                'skippable': True,
                'helpURLs': [
                    {'label': 'The AIDS Data Repository', 'url': 'https://adr.unaids.org'},
                    {'label': 'Naomi', 'url': 'https://naomi.unaids.org'}
                ]
            }
        },
        'progress': {
            'currentMilestoneID': 'tst-2-1-m',
            'milestoneListFullyResolved': True,
            'progress': 33,
            'milestones': [{'completed': False, 'id': 'tst-2-1-m', 'progress': 50, 'title': 'ADR Data'}]
        }
    }


def test_decide_without_data_raises_bad_request(client, mocker):
    response = client.post("/api/decide", data=json.dumps({}))
    assert 400 == response.status_code
    assert "No data specified in request" in response.json['message']


def test_decide_without_url_raises_bad_request(client, mocker):
    response = client.post("/api/decide", data=json.dumps({
        'data': {'authorization_header': 'api-key-here'}
    }))
    assert 400 == response.status_code
    assert "No url to data specified in request" in response.json['message']


@pytest.mark.parametrize("node_id, expected_result", [
    ('tst-2-3-a', {
        'id': 'tst-2-3-a',
        'content': {
            'displayHTML': 'Action 1 HTML',
            'helpURLs': [],
            'skippable': False,
            'terminus': False,
            'title': 'Action 1'
        }
    }),
    ('tst-1-5-a', {
        'id': 'tst-1-5-a',
        'content': {
            'displayHTML': 'Validate geographic data html',
            'helpURLs': [
                {'label': 'The AIDS Data Repository', 'url': 'https://adr.unaids.org'},
                {'label': 'HIV Tools', 'url': 'https://hivtools.unaids.org'}
            ],
            'skippable': True,
            'terminus': False,
            'title': 'Validate your geographic data'
        }
    }),
    ('tst-2-5-a', {
        'id': 'tst-2-5-a',
        'content': {
            'displayHTML': 'Action Complete',
            'helpURLs': [],
            'skippable': False,
            'terminus': True,
            'title': 'Complete'
        }
    })
])
@pytest.mark.usefixtures('with_app_context')
def test_action(client, mocker, node_id, expected_result):
    setup_endpoint_test(mocker)
    response = client.get(f"/api/action/{node_id}")
    assert response.json == expected_result


@pytest.mark.usefixtures('with_app_context')
def test_action_bad_node_id(client, mocker):
    setup_endpoint_test(mocker)
    response = client.get("/api/action/wrong-id")
    assert 400 == response.status_code
    assert "Please specify a valid action ID." in response.json['message']


def setup_endpoint_test(mocker, data=None):
    if not data:
        data = {
            '1': True,
            '2': True,
            'data': {'1': True, '2': True, '3': True, '4': True}
        }
    mocker.patch(
        'navigator_engine.api.choose_graph',
        return_value=2
    )
    mocker.patch(
        'navigator_engine.api.choose_data_loader',
        return_value=f'load_dict_from_json({json.dumps(json.dumps(data))})'
    )
    test_util.create_demo_data()


@pytest.mark.usefixtures('with_app_context')
def test_action_list(client, mocker):
    data = {
        '1': True,
        '2': True,
        'data': {'1': True, '2': True, '3': False, '4': True}
    }
    setup_endpoint_test(mocker, data)
    response = client.post("/api/actionlist", data=json.dumps({
        'data': {
            'url': 'https://example.ckan/api/3/action/package_show?id=example',
            'authorization_header': "example-api-key"
        },
        'skipActions': ['tst-1-5-a', 'tst-1-6-a']
    }))
    assert response.json == {
        'progress': 100,
        'fullyResolved': False,
        'actionList': [{
            'id': 'tst-2-3-a',
            'manualConfirmationRequired': False,
            'milestoneID': None,
            'reached': True,
            'skipped': False,
            'title': 'Action 1'
        }, {
            'id': 'tst-1-4-a',
            'manualConfirmationRequired': False,
            'milestoneID': 'tst-2-1-m',
            'reached': True,
            'skipped': False,
            'title': 'Upload your geographic data'
        }, {
            'id': 'tst-1-5-a',
            'manualConfirmationRequired': False,
            'milestoneID': 'tst-2-1-m',
            'reached': True,
            'skipped': False,
            'title': 'Validate your geographic data'
        }, {
            'id': 'tst-1-6-a',
            'manualConfirmationRequired': False,
            'milestoneID': 'tst-2-1-m',
            'reached': True,
            'skipped': True,
            'title': 'Upload your survey data'
        }, {
            'id': 'tst-1-7-a',
            'manualConfirmationRequired': False,
            'milestoneID': 'tst-2-1-m',
            'reached': True,
            'skipped': False,
            'title': 'Validate your survey data'
        }, {
            'id': 'tst-2-4-a',
            'manualConfirmationRequired': False,
            'milestoneID': None,
            'reached': True,
            'skipped': False,
            'title': 'Action 2'
        }, {
            'id': 'tst-2-5-a',
            'manualConfirmationRequired': False,
            'milestoneID': None,
            'reached': True,
            'skipped': False,
            'title': 'Complete'
        }],
        'milestones': [{
            'completed': True,
            'id': 'tst-2-1-m',
            'progress': 100,
            'title': 'ADR Data'
        }],
    }
