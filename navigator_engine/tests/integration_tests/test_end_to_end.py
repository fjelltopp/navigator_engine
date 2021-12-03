import pytest
import json
import os


# Once the blob storage bug stopping people from downloading old files is fixed
# This complete end to end test should work for the navigator test datasets
@pytest.mark.vcr()
@pytest.mark.parametrize("release, skip_requests, expected_decision", [
    ("v1 Empty Dataset", [], 'EST-OVV-01-10-A')
    ("v2 Estimates 22 Process Beginning", [], 'EST-OVV-01-10-A')
    ("v3 Preparing Input Data for HIV Estimates", [], 'EST-GEN-01-10-A')
    ("v4 Upload Estimates Input Data to ADR", [], 'EST-ADR-01-11-A')
    ("v5 Review Quality of Data Inputs using Naomi", [], 'EST-ROB-02-01-A')
    ("v6 Enter Data Into Spectrum", [], 'EST-SPE-01-10-A')
    ("v7 Generate HIV incidence", [], 'EST-EPP-01-10-A')
    ("v8 Generate knowledge of HIV status", [], 'EST-S90-01-10-A')
    ("v9 Finalize National HIV Estimates in Spectrum", [], 'EST-SPF-01-10-A')
    ("v10 Generate district HIV Estimates", [], 'EST-NAO-01-10-A')
    ("v11 Estimates Complete", [], 'EST-OVV-CPLT-A'),
])
def test_entire_estimates_process(test_production_client, release, skip_requests, expected_decision):
    dataset_url = 'https://adr.unaids.org/api/3/action/package_show?id=vanuatu-country-estimates-2022'
    release = release.replace(" ", "%20")
    response = test_production_client.post("/api/decide", data=json.dumps({
        'data': {
            'url': f"{dataset_url}&release={release}",
            'authorization_header': os.getenv('ADR_SYSADMIN_KEY')
        },
        'skipActions': ['EST-OVV-01-10-A'] + skip_requests
    }))
    assert response.status_code == 200
    assert response.json['decision']['id'] == expected_decision
    assert 'EST-OVV-01-10-A' in response.json['removeSkipActions']


@pytest.mark.vcr()
def test_end_to_end(test_production_client):
    response = test_production_client.post("/api/decide", data=json.dumps({
        'data': {
            'url': 'https://dev.adr.fjelltopp.org/api/3/action/package_show'
                   '?id=antarctica-country-estimates-2022-1-2-3',
            'authorization_header': os.getenv('ADR_SYSADMIN_KEY')
        },
        'skipActions': ['EST-OVV-01-10-A']
    }))
    assert response.status_code == 200
    assert response.json['decision']['id'] == 'EST-OVV-01-10-A'
    assert 'EST-OVV-01-10-A' in response.json['removeSkipActions']


@pytest.mark.vcr()
def test_spectrum_file_check(test_production_client):
    response = test_production_client.post("/api/decide", data=json.dumps({
        'data': {
            'url': 'https://dev.adr.fjelltopp.org/api/3/action/package_show'
                   '?id=slovakia-country-estimates-2022',
            'authorization_header': os.getenv('ADR_SYSADMIN_KEY')
        }
    }))

    assert response.status_code == 200
    assert response.json['decision']['id'] == 'EST-NAO-01-10-A'
