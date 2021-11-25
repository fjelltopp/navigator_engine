from navigator_engine.common import register_loader
import requests
from typing import Hashable
from navigator_engine.common.decision_engine import DecisionEngine
from navigator_engine.common import get_resource_from_dataset
import json
import logging
import pandas as pd
import zipfile
import re
import io

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
    response.raise_for_status()
    data[name] = {'source_url': url, 'auth_header': auth_header, 'data': response.content}
    return data


@register_loader
def load_json_url(url: str, auth_header: str, name: str, engine: DecisionEngine) -> dict:
    data = load_url(url, auth_header, name, engine)
    data[name]['data'] = json.loads(data[name]['data'])
    return data


@register_loader
def load_dataset_resource(resource_type: str, engine: DecisionEngine) -> dict:
    dataset = engine.data['dataset']['data']['result']
    auth_header = engine.data['dataset']['auth_header']
    resource = get_resource_from_dataset(resource_type, dataset)
    if not resource or not resource['url']:
        engine.data[resource_type] = {
            'data': None,
            'auth_header': auth_header,
            'url': None
        }
        return engine.data
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
    data = load_dataset_resource(
        'navigator-workflow-state',
        engine
    )
    return data


@register_loader
def load_csv_from_zipped_resource(resource_type: str, csv_filename_regex: str,
                                  name: str, engine: DecisionEngine) -> dict:
    data = load_dataset_resource(resource_type, engine)
    auth_header = data[resource_type]['auth_header']

    if not data[resource_type]['data']:
        data[name] = {
            'data': None,
            'auth_header': auth_header,
            'url': data[resource_type]['url']
        }
        return data

    filename_re = re.compile(csv_filename_regex, flags=re.IGNORECASE)
    matching_filenames = []

    try:
        with zipfile.ZipFile(io.BytesIO(data[resource_type]['data'])) as zip_file:
            for filename in zip_file.namelist():
                if filename_re.match(filename):
                    matching_filenames.append(filename)
            if len(matching_filenames) > 1:
                raise ValueError(
                    f"Multiple files match filename regex {csv_filename_regex}"
                    f"in: {data[resource_type]['url']}"
                )
            elif len(matching_filenames) == 0:
                dataframe = None
            else:
                with zip_file.open(matching_filenames[0], 'r') as csv_file:
                    dataframe = pd.read_csv(csv_file)
    except zipfile.BadZipFile:
        raise zipfile.BadZipFile(
            f"Bad zip file for {resource_type}: {data[resource_type]['url']}"
        )

    data[name] = {
        'data': dataframe,
        'auth_header': auth_header,
        'url': data[resource_type]['url']
    }
    del data[resource_type]
    return data
