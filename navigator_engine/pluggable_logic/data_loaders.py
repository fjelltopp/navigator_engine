from navigator_engine.common import register_loader
import requests
from typing import Hashable
from navigator_engine.common.decision_engine import DecisionEngine


@register_loader
def return_empty(engine: DecisionEngine) -> dict:
    return {}


@register_loader
def dict_value(key: Hashable, engine: DecisionEngine) -> Hashable:
    return engine.data[key]


@register_loader
def json_url(url_key: Hashable,
             authorization_header_key: Hashable, engine: DecisionEngine) -> dict:
    url = engine.data[url_key]
    headers = {"Authorization": engine.data[authorization_header_key]}
    response = requests.get(url, headers=headers)
    loaded_data = response.json()
    loaded_data['navigator_engine_source_url'] = url
    loaded_data['navigator_engine_auth_headers'] = headers
    return loaded_data
