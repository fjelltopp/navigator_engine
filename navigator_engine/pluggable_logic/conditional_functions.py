from navigator_engine.common import register_conditional, get_resource_from_dataset
from navigator_engine.common.decision_engine import DecisionEngine
from typing import Hashable
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
    skipped_actions = [action for action in actions if action in engine.progress.skipped]
    engine.remove_skips += list(skipped_actions)
    return not bool(skipped_actions)


@register_conditional
def check_manual_confirmation(action_id: int, engine: DecisionEngine) -> bool:
    return action_id in engine.data['navigator-workflow-state']['data']['completedSteps']


@register_conditional
def check_resource_key(resource_type: str, key: Hashable, value: Hashable, engine: DecisionEngine) -> bool:
    regex = re.compile(value)
    dataset = engine.data['dataset']['data']['result']
    resource = get_resource_from_dataset(resource_type, dataset)
    if type(resource.get(key)) is str:
        match_result = regex.match(resource.get(key, ""))
        return bool(match_result)
    else:
        return resource.get(key) == value
