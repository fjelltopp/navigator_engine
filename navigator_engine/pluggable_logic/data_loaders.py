from navigator_engine.common import register_loader
import requests
import json


@register_loader
def return_empty(engine):
    return {}


@register_loader
def dict_value(key, engine):
    return engine.data[key]


@register_loader
def json_url(url_key, authorization_header_key, engine):
    url = engine.data[url_key]
    headers = {"Authorization": engine.data[authorization_header_key]}
    response = requests.get(url, headers=headers)
    loaded_data = response.json()
    loaded_data['navigator_engine_source_url'] = url
    loaded_data['navigator_engine_auth_headers'] = headers
    return loaded_data
