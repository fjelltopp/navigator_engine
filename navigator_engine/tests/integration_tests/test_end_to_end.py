from navigator_engine.common.graph_loader import graph_loader, validate_graph
import pytest
import json
import os


@pytest.mark.vcr()
@pytest.mark.usefixtures('with_app_context')
def test_end_to_end(client):
    base_directory = os.path.abspath(os.path.dirname(__file__))
    graph_loader(f'{base_directory}/../../../Estimates 22 BDG [Final].xlsx')
    validate_graph(1)
    # For the time being the following code is ignored
    # It will be updated once the production graph is loading properly
    response = client.post("/api/decide", data=json.dumps({
        'data': {
            'url': 'https://dev.adr.fjelltopp.org/api/3/action/package_show'
                   '?id=antarctica-country-estimates-2022-1-2-3',
            'authorization_header': os.getenv('ADR_SYSADMIN_KEY')
        },
        'skipActions': []
    }))
    assert response.status_code == 200
    assert response.json['decision']['id'] == 'EST-OVV-02-A'
