import navigator_engine.model as model
from navigator_engine.common import (
    CONDITIONAL_FUNCTIONS,
    DATA_LOADERS,
    DecisionError,
    get_pluggable_function_and_args
)
from navigator_engine.common.progress_tracker import ProgressTracker
from navigator_engine.common.network import Network
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


class DecisionEngine():

    def __init__(self, graph: model.Graph, source_data: object, data_loader: str = None,
                 stop: str = "", skip_requests: list[str] = [], route: list[model.Node] = [],
                 skipped_actions: list[str] = []) -> None:
        self.graph: model.Graph = graph
        self.network: Network = Network(self.graph.to_networkx())
        self.data: Any = source_data
        self.skip_requests: list[str] = skip_requests
        self.remove_skip_requests: list[str] = []
        self.progress: ProgressTracker = ProgressTracker(self.network, route=route, skipped_actions=skipped_actions)
        self.decision: dict[str, Any] = {}
        self.stop_action: str = stop
        if data_loader:
            self.data = self.run_pluggable_logic(data_loader, DATA_LOADERS)

    def decide(self, data: object = None, skip_requests: list[str] = None, stop=None) -> dict:
        if data is not None:
            self.data = data
        if skip_requests is not None:
            self.skip_requests = skip_requests
        if stop is not None:
            self.stop_action = stop
        self.progress.reset()
        next_action = self.process_node(self.network.get_root_node())
        self.decision = {
            "id": next_action.ref,
            "content": next_action.action.to_dict(),
            "node": next_action
        }
        self.progress.report_progress()
        self.remove_skip_requests_not_needed()
        return self.decision

    def process_node(self, node: model.Node) -> model.Node:
        self.progress.add_node(node)
        if getattr(node, 'conditional_id'):
            return self.process_conditional(node)
        elif getattr(node, 'milestone_id'):
            return self.process_milestone(node)
        elif getattr(node, 'action_id'):
            return self.process_action(node)
        raise DecisionError(f"Node {node.ref} is not a conditional, action or milestone")

    def process_conditional(self, node: model.Node) -> model.Node:
        edge_type = self.run_pluggable_logic(node.conditional.function)
        next_node = self.get_next_node(node, edge_type)
        return self.process_node(next_node)

    def process_action(self, node: model.Node) -> model.Node:
        stop_action = node.ref == self.stop_action
        in_skip_requests = node.ref in self.skip_requests
        skippable = node.action.skippable
        if not stop_action and in_skip_requests and skippable:
            return self.skip_action(node)
        elif stop_action and in_skip_requests and skippable:
            self.progress.skipped_actions.append(node.ref)
        elif in_skip_requests and not skippable:
            self.remove_skip_requests.append(node.ref)
        return node

    def process_milestone(self, node: model.Node) -> model.Node:
        milestone_engine = engine_factory(
            model.load_graph(node.milestone.graph_id),
            self.data.copy(),
            data_loader=node.milestone.data_loader,
            skip_requests=self.skip_requests,
            skipped_actions=self.progress.skipped_actions,
            stop=self.stop_action
        )
        milestone_result = milestone_engine.decide()
        self.remove_skip_requests += milestone_engine.remove_skip_requests
        if milestone_result['node'].action.complete:
            self.progress.add_milestone(node, milestone_engine.progress, complete=True)
            next_node = self.get_next_node(node, True)
            return self.process_node(next_node)
        else:
            self.progress.add_milestone(node, milestone_engine.progress)
            return milestone_result['node']

    def get_next_node(self, node: model.Node, edge_type: bool) -> model.Node:
        new_node = None
        for node, child_node, type in self.network.networkx.out_edges(node, data="type"):
            if type == edge_type:
                new_node = child_node
            if child_node.ref == self.stop_action:
                return child_node
        if not new_node:
            raise DecisionError(f"No outgoing '{edge_type}' edge for node {node.ref}")
        return new_node

    def run_pluggable_logic(self, function_string: str,
                            functions: dict[str, Callable] = CONDITIONAL_FUNCTIONS) -> Any:
        function_name, function_args = get_pluggable_function_and_args(function_string)
        try:
            function = functions[function_name]
        except KeyError:
            raise DecisionError(f"No pluggable logic for {function_name}")
        try:
            return function(*function_args, self)
        except Exception as e:
            logger.exception(e)
            raise DecisionError(
                f"Error running pluggable logic {function_string}: {type(e).__name__} {e}"
            )

    def skip_action(self, node: model.Node) -> model.Node:
        previous_node = self.progress.entire_route[-2]
        for previous_node, new_node in self.network.networkx.out_edges(previous_node):
            if node != new_node:
                self.progress.skipped_actions.append(node.ref)
                self.progress.pop_node()
                return self.process_node(new_node)
        raise DecisionError(f"Only one outgoing edge for node: {previous_node}")

    def remove_skip_requests_not_needed(self) -> None:
        action_breadcrumbs_ref = [a['id'] for a in self.progress.action_breadcrumbs]
        ignored_skips = [ref for ref in self.skip_requests if ref not in self.progress.skipped_actions]
        ignored_skips_in_path = [ref for ref in ignored_skips if ref in action_breadcrumbs_ref]
        self.remove_skip_requests.extend(ref for ref in ignored_skips_in_path if ref not in self.remove_skip_requests)


def engine_factory(graph, data, data_loader=None, skip_requests=[],
                   stop=None, skipped_actions=[]) -> DecisionEngine:
    # Used to mock out engine creation in tests
    return DecisionEngine(
        graph,
        data,
        skip_requests=skip_requests,
        data_loader=data_loader,
        stop=stop,
        skipped_actions=skipped_actions
    )
