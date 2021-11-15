from navigator_engine.common import register_conditional
from navigator_engine.common.decision_engine import DecisionEngine
from typing import Hashable


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
