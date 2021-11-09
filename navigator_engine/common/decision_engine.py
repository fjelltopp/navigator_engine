import ast
import navigator_engine.model as model
from navigator_engine.common import CONDITIONAL_FUNCTIONS, DATA_LOADERS, DecisionError
from navigator_engine.common.progress_tracker import ProgressTracker
from typing import Callable
from flask import current_app


class DecisionEngine():

    def __init__(self, graph: model.Graph, data: object,
                 skip: list[str] = [], route: list[str] = []) -> None:
        self.graph = graph
        self.network = self.graph.to_networkx()
        self.data = data
        self.skip = skip
        self.progress = ProgressTracker(self.network, route=route)
        self.decision = {}

    def decide(self, data: object = None, skip: list[str] = None) -> dict:
        if data:
            self.data = data
        if skip:
            self.skip = skip
        self.progress.reset()
        self.decision = self.process_node(self.progress.root_node)
        self.progress.report_progress()
        return self.decision

    def process_node(self, node: model.Node) -> model.Action:
        self.progress.add_node(node)
        if getattr(node, 'conditional_id'):
            return self.process_conditional(node)
        elif getattr(node, 'action_id'):
            return self.process_action(node)
        elif getattr(node, 'milestone_id'):
            return self.process_milestone(node)

    def process_conditional(self, node: model.Node) -> model.Node:
        edge_type = self.run_pluggable_logic(node.conditional.function)
        next_node = self.get_next_node(node, edge_type)
        return self.process_node(next_node)

    def process_action(self, node: model.Node) -> dict:
        if node.id in self.skip:
            return self.skip_action(node)
        return {
            "id": node.id,
            "content": node.action.to_dict(),
            "node": node
        }

    def process_milestone(self, node: model.Node) -> model.Node:
        nested_graph = model.load_graph(node.milestone.graph_id)
        nested_graph_data = self.run_pluggable_logic(node.milestone.data_loader, DATA_LOADERS)
        milestone_engine = engine_factory(
            nested_graph,
            nested_graph_data,
            skip=self.skip
        )
        milestone_result = milestone_engine.decide()
        if milestone_result['node'].action.complete:
            self.progress.add_milestone(node, milestone_engine.progress, complete=True)
            next_node = self.get_next_node(node, True)
            return self.process_node(next_node)
        else:
            self.progress.add_milestone(node, milestone_engine.progress)
            return milestone_result

    def get_next_node(self, node: model.Node, edge_type: bool) -> model.Node:
        for node, new_node, type in self.network.out_edges(node, data="type"):
            if type == edge_type:
                return new_node
        raise DecisionError(f"No outgoing '{edge_type}' edge for node {node.id}")

    def run_pluggable_logic(self, function_string: str,
                            functions: dict[str, Callable] = CONDITIONAL_FUNCTIONS):
        function_name = function_string.split("(")[0]
        try:
            function = functions[function_name]
        except KeyError:
            raise DecisionError(f"No pluggable logic for function {function_name}")
        function_args = function_string.split(function_name)[1]
        function_args = function_args[:-1] + ",)"
        function_args = ast.literal_eval(function_args)
        try:
            return function(*function_args, self.data)
        except Exception as e:
            raise DecisionError(
                f"Error running pluggable logic {function_string} for "
                f"node {self.progress.route[-1].id}: {type(e).__name__} {e}"
            )

    def skip_action(self, node: model.Node) -> dict:
        action = node.action
        if not action.skippable:
            raise DecisionError(f"Action cannot be skipped: {action.id} ({action.title})")
        previous_node = self.progress.entire_route[-2]
        for previous_node, new_node in self.network.out_edges(previous_node):
            if node != new_node:
                self.progress.skipped.append(node.id)
                self.progress.pop_node()
                return self.process_node(new_node)
        raise DecisionError(f"Only one outgoing edge for node: {previous_node.id}")


def engine_factory(graph, data, skip=[]) -> DecisionEngine:
    # Needed because mocking recursive object creation in tests is difficult!
    # There may be a better way?
    return DecisionEngine(
        graph,
        data,
        skip=skip
    )
