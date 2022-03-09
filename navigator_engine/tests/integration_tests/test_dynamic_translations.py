import pytest
import json
import os


@pytest.mark.vcr()
def test_estimates_start(test_production_client):
    response = test_production_client.post(
        "/api/decide",
        data=json.dumps({
            'data':
                {
                    'url': 'https://dev.adr.fjelltopp.org/api/3/action/package_show'
                           '?id=czechia-country-estimates-2022',
                    'authorization_header': os.getenv('ADR_SYSADMIN_KEY')
                },
                'skipActions': ['EST-OVV-01-10-A']
            }),
        headers={'Accept-Language': 'fr'}
    )
    data = json.loads(response.data)
    assert response.status_code == 200
    assert response.json['decision']['id'] == 'EST-OVV-01-10-A'
    assert data['actions'][0]['title'] == 'Bienvenue dans le navigateur des estimations du VIH de l\'ONUSIDA'
    assert 'EST-OVV-01-10-A' in response.json['removeSkipActions']