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
    assert response.data == b"Navigator Engine Running"


@pytest.mark.usefixtures('with_app_context')
def test_decide(client):
    test_util.create_demo_data()
    response = client.post("/api/decide", data=json.dumps({'test': 'data'}))
