import pytest
import json
import os


@pytest.mark.vcr()
@pytest.mark.parametrize('language,title', [
    ('', 'Welcome to the UNAIDS HIV Estimates Navigator'),
    ('en', 'Welcome to the UNAIDS HIV Estimates Navigator'),
    ('fr', 'Bienvenue dans le navigateur des estimations du VIH de l\'ONUSIDA'),
    ('pt_PT', 'Bem-vindo ao Navegador da UNAIDS HIV')
])
def test_estimates_start(test_production_client, language, title):
    response = test_production_client.post(
        "/api/decide",
        data=json.dumps({
            'data': {
                'url': 'https://dev.adr.fjelltopp.org/api/3/action/package_show'
                       '?id=czechia-country-estimates-2022',
                'authorization_header': os.getenv('ADR_SYSADMIN_KEY')
            },
            'skipActions': ['EST-OVV-01-10-A']
        }),
        headers={'Accept-Language': language}
    )
    data = json.loads(response.data)
    assert response.status_code == 200
    assert response.json['decision']['id'] == 'EST-OVV-01-10-A'
    assert data['actions'][0]['title'] == title
    assert 'EST-OVV-01-10-A' in response.json['removeSkipActions']


@pytest.mark.vcr()
def test_estimates_complete(test_production_client):
    response = test_production_client.post("/api/decide", data=json.dumps({
        'data': {
            'url': 'https://dev.adr.fjelltopp.org/api/3/action/package_show'
                   '?id=slovakia-country-estimates-2022',
            'authorization_header': os.getenv('ADR_SYSADMIN_KEY')
        }
    }))
    assert response.status_code == 200
    assert response.json['decision']['id'] == 'EST-MIL-CPLT-A'
