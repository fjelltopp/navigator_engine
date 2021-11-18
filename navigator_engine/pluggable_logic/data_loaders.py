from navigator_engine.common import register_loader
import requests
from typing import Hashable
from navigator_engine.common.decision_engine import DecisionEngine
from navigator_engine.common import get_resource_from_dataset
import json
import logging

logger = logging.getLogger(__name__)


@register_loader
def load_empty(engine: DecisionEngine) -> dict:
    return {}


@register_loader
def load_dict_from_json(json_data: str, engine: DecisionEngine) -> Hashable:
    return json.loads(json_data)


@register_loader
def load_dict_value(key: Hashable, engine: DecisionEngine) -> Hashable:
    return engine.data[key]


@register_loader
def load_url(url: str, auth_header: str, name: str, engine: DecisionEngine) -> dict:
    data = engine.data
    headers = {"Authorization": auth_header}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logger.error(f"HTTP Error loading URL {response.status_code}: {response.content!r}")
        raise IOError(f"HTTP Error {response.status_code} whilst loading {name}: {url}")
    data[name] = {'source_url': url, 'auth_header': headers, 'data': response.content}
    return data


@register_loader
def load_json_url(url: str, auth_header: str, name: str, engine: DecisionEngine) -> dict:
    data = load_url(url, auth_header, name, engine)
    data[name]['data'] = json.loads(data[name]['data'])
    return data


@register_loader
def load_estimates_dataset_resource(resource_type: str, auth_header: str, engine: DecisionEngine) -> dict:
    dataset = engine.data['dataset']['data']['result']
    resource = get_resource_from_dataset(resource_type, dataset)
    if not resource:
        raise IOError(f"No resource of type {resource_type} found in {dataset['name']}")
    if not resource['url']:
        raise IOError(f"Resource {resource_type} exists but has no data")
    if 'json' in resource['format'].lower():
        data = load_json_url(
            resource['url'],
            auth_header,
            resource_type,
            engine
        )
    else:
        data = load_url(
            resource['url'],
            auth_header,
            resource_type,
            engine
        )
    return data


@register_loader
def load_estimates_dataset(url_key: Hashable, auth_header_key: Hashable, engine: DecisionEngine) -> dict:
    dataset_url = engine.data[url_key]
    auth_header = engine.data[auth_header_key]
    engine.data = {}
    data = load_json_url(dataset_url, auth_header, 'dataset', engine)
    try:
        data = load_estimates_dataset_resource(
            'navigator-workflow-state',
            auth_header,
            engine
        )
    except IOError:
        data['navigator-workflow-state'] = {
            'url': None,
            'auth_header': None,
            'data': {'completedTasks': []}
        }
    return data
