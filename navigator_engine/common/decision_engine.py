import navigator_engine.model as model
from navigator_engine.common import (
    CONDITIONAL_FUNCTIONS,
    DATA_LOADERS,
    DecisionError,
    get_pluggable_function_and_args
)
from navigator_engine.common.progress_tracker import ProgressTracker
from typing import Callable, Any
import networkx
import logging

logger = logging.getLogger(__name__)


class DecisionEngine():

    def __init__(self, graph: model.Graph, source_data: object, data_loader: str = None,
                 stop: str = "", skip: list[str] = [], route: list[model.Node] = []) -> None:
        self.graph: model.Graph = graph
        self.network: networkx.DigGraph = self.graph.to_networkx()
        self.data: Any = source_data
        self.skip: list[str] = skip
        self.progress: ProgressTracker = ProgressTracker(self.network, route=route)
        self.decision: dict[str, Any] = {}
        self.stop_action: str = stop
        self.remove_skips: list[str] = []
        if data_loader:
            self.data = self.run_pluggable_logic(data_loader, DATA_LOADERS)

    def decide(self, data: object = None, skip: list[str] = None, stop=None) -> dict:
        if data:
            self.data = data
        if skip:
            self.skip = skip
        if stop:
            self.stop_action = stop
        self.progress.reset()
        next_action = self.process_node(self.progress.root_node)
        manual_confirmation_required = self.requires_manual_confirmation(next_action)
        self.decision = {
            "id": next_action.ref,
            "content": next_action.action.to_dict(),
            "node": next_action,
            "manualConfirmationRequired": manual_confirmation_required
        }
        self.progress.report_progress()
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
        if node.ref != self.stop_action and node.ref in self.skip:
            return self.skip_action(node)
        self.progress.action_breadcrumbs.append(node.ref)
        return node

    def process_milestone(self, node: model.Node) -> model.Node:
        milestone_engine = engine_factory(
            model.load_graph(node.milestone.graph_id),
            self.data.copy(),
            data_loader=node.milestone.data_loader,
            skip=self.skip,
            stop=self.stop_action
        )
        milestone_result = milestone_engine.decide()
        if milestone_result['node'].action.complete:
            self.progress.add_milestone(node, milestone_engine.progress, complete=True)
            next_node = self.get_next_node(node, True)
            return self.process_node(next_node)
        else:
            self.progress.add_milestone(node, milestone_engine.progress)
            return milestone_result['node']

    def get_next_node(self, node: model.Node, edge_type: bool) -> model.Node:
        new_node = None
        for node, child_node, type in self.network.out_edges(node, data="type"):
            if type == edge_type:
                new_node = child_node
            if child_node.ref == self.stop_action:
                return child_node
        if not new_node:
            raise DecisionError(f"No outgoing '{edge_type}' edge for node {node.ref}")
        return new_node

    def run_pluggable_logic(self, function_string: str,
                            functions: dict[str, Callable] = CONDITIONAL_FUNCTIONS):
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
        action = node.action
        if not action.skippable:
            raise DecisionError(f"Action cannot be skipped: {action.id} ({action.title})")
        previous_node = self.progress.entire_route[-2]
        for previous_node, new_node in self.network.out_edges(previous_node):
            if node != new_node:
                self.progress.skipped.append(node.ref)
                self.progress.pop_node()
                return self.process_node(new_node)
        raise DecisionError(f"Only one outgoing edge for node: {previous_node}")

    def requires_manual_confirmation(self, node: model.Node) -> bool:
        manual_confirmation = False
        parent_node = self.progress.entire_route[-2]
        if getattr(parent_node, 'conditional'):
            function = parent_node.conditional.function
            manual_confirmation = function.startswith("check_manual_confirmation")
        return manual_confirmation


def engine_factory(graph, data, data_loader=None, skip=[], stop=None) -> DecisionEngine:
    # Used to mock out engine creation in tests
    return DecisionEngine(
        graph,
        data,
        skip=skip,
        data_loader=data_loader,
        stop=stop
    )
