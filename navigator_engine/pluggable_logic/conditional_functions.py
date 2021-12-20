import navigator_engine.common
from navigator_engine.common import register_conditional, get_resource_from_dataset
from navigator_engine.common.decision_engine import DecisionEngine
from typing import Hashable, Union, Any
import re


@register_conditional
def return_true(engine: DecisionEngine) -> bool:
    return True


@register_conditional
def return_false(engine: DecisionEngine) -> bool:
    return False


@register_conditional
def dict_value(key: Hashable, engine: DecisionEngine) -> bool:
    return bool(engine.data[key])


@register_conditional
def check_dict_value(key: Hashable, value: Hashable, engine: DecisionEngine) -> bool:
    return engine.data[key] == value


@register_conditional
def check_not_skipped(actions: list[str], engine: DecisionEngine) -> bool:

    if type(actions) is not list:
        raise TypeError(f"Must specify an list of node IDs instead of {actions}")

    skipped_actions = [action for action in actions if action in engine.progress.skipped_actions]
    engine.remove_skip_requests += list(skipped_actions)

    return not bool(skipped_actions)


@register_conditional
def check_manual_confirmation(action_id: int, engine: DecisionEngine) -> bool:
    return action_id in _get_completed_actions(engine)


@register_conditional
def check_resource_key(resource_types: Union[list[str], str], key: Hashable, value: Hashable, engine: DecisionEngine) -> bool:

    if type(resource_types) is str:
        resource_types = [resource_types]

    dataset = engine.data['dataset']['data']['result']
    results = []

    for resource_type in resource_types:
        resource = get_resource_from_dataset(resource_type, dataset)

        if type(value) is str and type(resource.get(key)) is str:
            regex = re.compile(value)
            match_result = bool(regex.match(resource.get(key, "")))
        else:
            match_result = resource.get(key) == value

        results.append(match_result)

    return all(results)


@register_conditional
def check_dataset_valid(engine: DecisionEngine) -> bool:

    dataset = engine.data['dataset']['data']['result']

    for resource in dataset.get('resources', []):

        if resource.get('validation_status', 'success') != 'success':
            return False

    return True


@register_conditional
def check_spectrum_file(indicators: list[str], engine: DecisionEngine) -> bool:
    return _check_validation_file(
        indicators,
        'spectrum-validation-file',
        'ID',
        'Status',
        engine
    )


@register_conditional
def check_naomi_file(indicators: list[str], engine: DecisionEngine) -> bool:
    return _check_validation_file(
        indicators,
        'naomi-validation-file',
        'NaomiCheckPermPrimKey',
        'TrueFalse',
        engine
    )


def _check_validation_file(indicators: list[str], data_source: str,
                           id_column: str, result_column: str, engine: DecisionEngine) -> bool:

    checklist = engine.data[data_source]['data']

    if checklist is None:
        return False

    indicators = [indicator.lower() for indicator in indicators]

    indicator_checks = checklist[checklist[id_column].str.lower().isin(indicators)]
    indicator_results = indicator_checks[result_column].replace(
        [0, 'FALSE', 'F', 'false', 'f'],
        value=False
    )
    indicator_results[indicator_results.ne(False)] = True

    return indicator_results.eq(True).all()


def _get_completed_actions(engine: DecisionEngine) -> dict[str, dict[str, Any]]:

    workflow_state = engine.data['navigator-workflow-state'].get('data')

    if not workflow_state:
        return {}
    else:
        return {task['id']: task for task in workflow_state.get('completedTasks', [])}
