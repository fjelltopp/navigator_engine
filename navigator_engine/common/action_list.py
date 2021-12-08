from navigator_engine import model
from navigator_engine.common.progress_tracker import ProgressTracker
from navigator_engine.common.network import Network
from navigator_engine.common.decision_engine import DecisionEngine
from typing import Any


def step_through_common_path(network: Network, sources: list[model.Node] = []) -> ProgressTracker:
    source = None if not sources else sources.pop(0)
    progress = ProgressTracker(network)
    for node in network.common_path(source):
        progress.add_node(node)
        if getattr(node, 'milestone_id'):
            milestone_graph = model.load_graph(node.milestone.graph_id)
            milestone_network = Network(milestone_graph.to_networkx())
            milestone_progress = step_through_common_path(milestone_network, sources)
            progress.add_milestone(node, milestone_progress)
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
        sources = [ongoing_milestone_node, engine.route[-2]]
    else:
        sources = [engine.route[-2]]
    progress = step_through_common_path(engine.network, sources=sources)

    unreached_actions = progress.action_breadcrumbs[1:]
    for action in unreached_actions:
        action['title'] = model.load_node(node_ref=action['id']).action.title
        action['reached'] = False

    return reached_actions + unreached_actions
