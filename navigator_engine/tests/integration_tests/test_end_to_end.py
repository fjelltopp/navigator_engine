from navigator_engine.common.graph_loader import graph_loader
import pytest
import json
import os


@pytest.mark.vcr()
@pytest.mark.usefixtures('with_app_context')
def test_end_to_end(client):
    graph_loader('Estimates_Navigator_BDG_Validations.xlsx')
    response = client.post("/api/decide", data=json.dumps({
        'data': {
            'url': 'https://dev.adr.fjelltopp.org/api/3/action/package_show'
                   '?id=antarctica-country-estimates-2022-1-2-3',
            'authorization_header': os.getenv('ADR_SYSADMIN_KEY')
        },
        'skipActions': ['EST-1-4-A', 'EST-2-2-A']
    }))
    assert response.status_code == 200
    assert response.json['decision']['id'] == 'EST-0-C-A'
