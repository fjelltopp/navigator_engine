import ast
from navigator_engine import model
from navigator_engine.common.progress_tracker import ProgressTracker
from navigator_engine.common.network import Network
from navigator_engine.common.decision_engine import DecisionEngine
from typing import Any, Callable

CONDITIONAL_FUNCTIONS: dict[str, Callable] = {}
DATA_LOADERS: dict[str, Callable] = {}


def choose_graph(file_url):
    # TODO:  choose the graph for a given file url
    # For now only one graph type
    return 1


def choose_data_loader(file_url):
    # TODO:  choose a data loader for the given file_url
    # For now only one type of file, so only one type of loader
    return "load_estimates_dataset('url', 'authorization_header')"


def register_conditional(f):
    CONDITIONAL_FUNCTIONS[f.__name__] = f
    return f


def register_loader(f):
    DATA_LOADERS[f.__name__] = f
    return f


def get_resource_from_dataset(resource_type: str, dataset: dict) -> dict:
    dataset_name = dataset['name']
    matching_resources = list(filter(
        lambda r: r['resource_type'] == resource_type,
        dataset.get('resources', [])
    ))
    if len(matching_resources) > 1:
        raise DecisionError(
            f"Multiple resources with type {resource_type} were found in the {dataset_name} dataset."
        )
    if matching_resources:
        return matching_resources[0]
    else:
        return {}


def get_pluggable_function_and_args(function_string: str) -> tuple[str, tuple]:
    function_name = function_string.split("(")[0]
    function_args = function_string.split(function_name)[1]
    eval_function_args = ast.literal_eval(function_args)
    if type(eval_function_args) is not tuple:
        eval_function_args = (eval_function_args,)
    return function_name, eval_function_args


def step_through_common_path(network: Network, sources: list[model.Node] = []) -> ProgressTracker:
    source = None if not sources else sources.pop(0)
    progress = ProgressTracker(network)
    for node in network.common_path(source):
        if getattr(node, 'milestone_id'):
            milestone_graph = model.load_graph(node.milestone.graph_id)
            milestone_network = Network(milestone_graph.to_networkx())
            milestone_progress = step_through_common_path(milestone_network, sources)
            progress.add_milestone(node, milestone_progress)
        else:
            progress.add_node(node)
    return progress


def create_action_list(engine: DecisionEngine) -> list[dict[str, Any]]:
    engine.decide()

    reached_actions = engine.progress.action_breadcrumbs
    for action in reached_actions:
        action['title'] = model.load_node(node_ref=action['id']).action.title
        action['reached'] = True

    ongoing_milestone_id = engine.progress.report.get('currentMilestoneID')
    if ongoing_milestone_id:
        ongoing_milestone_node = model.load_node(node_ref=ongoing_milestone_id)
        sources = [ongoing_milestone_node, engine.decision['node']]
    else:
        sources = [engine.decision['node']]
    progress = step_through_common_path(engine.network, sources=sources)

    unreached_actions = progress.action_breadcrumbs
    for action in unreached_actions:
        action['title'] = model.load_node(node_ref=action['id']).action.title
        action['reached'] = False

    return reached_actions + unreached_actions


class DecisionError(Exception):
    """Raised when there is an error in the decision logic."""
    pass
