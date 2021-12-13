from navigator_engine import model
from navigator_engine.common.progress_tracker import ProgressTracker
from navigator_engine.common.network import Network
from navigator_engine.common.decision_engine import DecisionEngine
from typing import Any


def step_through_common_path(network: Network, sources: list[model.Node] = []) -> ProgressTracker:
    source = None if not sources else sources.pop(0)
    progress = ProgressTracker(network)
    common_path, path_fully_resolved = network.common_path(source)
    for node in common_path:
        progress.add_node(node)
        if getattr(node, 'milestone_id'):
            milestone_graph = model.load_graph(node.milestone.graph_id)
            milestone_network = Network(milestone_graph.to_networkx())
            milestone_progress, milestone_path_fully_resolved = step_through_common_path(milestone_network, sources)
            if not milestone_path_fully_resolved:
                path_fully_resolved = False
            progress.add_milestone(node, milestone_progress)
    return progress, path_fully_resolved


def create_action_list(engine: DecisionEngine) -> list[dict[str, Any]]:
    engine.decide()

    reached_actions = engine.progress.action_breadcrumbs
    for action in reached_actions:
        action['title'] = model.load_node(node_ref=action['id']).action.title
        action['reached'] = True

    if engine.progress.entire_route[-1].action.complete:
        return reached_actions

    ongoing_milestone_id = engine.progress.report.get('currentMilestoneID')
    if ongoing_milestone_id:
        ongoing_milestone_node = model.load_node(node_ref=ongoing_milestone_id)
        sources = [ongoing_milestone_node, engine.progress.entire_route[-2]]
    else:
        sources = [engine.progress.entire_route[-2]]
    progress, path_fully_resolved = step_through_common_path(engine.network, sources=sources)

    unreached_actions = progress.action_breadcrumbs[1:]
    for action in unreached_actions:
        action['title'] = model.load_node(node_ref=action['id']).action.title
        action['reached'] = False

    action_list = reached_actions + unreached_actions
    return action_list, path_fully_resolved
