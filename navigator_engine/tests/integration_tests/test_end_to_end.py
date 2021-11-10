from navigator_engine.common.graph_loader import graph_loader
import pytest
import json


@pytest.mark.usefixtures('with_app_context')
def test_end_to_end(client):
    graph_loader('Estimates_Navigator_BDG_Validations.xlsx')
    response = client.post("/api/decide", data=json.dumps({
        'data': {
            'url': 'https://dev.adr.fjelltopp.org/api/3/action/package_show?id=antarctica-country-estimates-2022-1-2',
            'authorization_header': "example-api-key"
        },
        'skipActions': [16]
    }))
    assert response.status_code == 200
    assert response.json['decision']['id'] == 30
    for node_id in response.json['actions']:
        response = client.get(f"/api/action/{node_id}")
        assert response.status_code == 200
        assert response.json['content'].get('title', False)
