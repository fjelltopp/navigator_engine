import ast
import navigator_engine.model as model
from navigator_engine.common import CONDITIONAL_FUNCTIONS, DATA_LOADERS, DecisionError
from navigator_engine.common.progress_tracker import ProgressTracker
from typing import Callable


class DecisionEngine():

    def __init__(self, graph: model.Graph, source_data: object, data_loader: str = None,
                 stop: str = None, skip: list[str] = [], route: list[str] = []) -> None:
        self.graph = graph
        self.network = self.graph.to_networkx()
        self.data = source_data
        self.skip = skip
        self.progress = ProgressTracker(self.network, route=route)
        self.decision = {}
        self.stop_action = stop
        self.remove_skips = []
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
        milestone_engine = engine_factory(
            model.load_graph(node.milestone.graph_id),
            self.data,
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
            return milestone_result

    def get_next_node(self, node: model.Node, edge_type: bool) -> model.Node:
        new_node = None
        for node, child_node, type in self.network.out_edges(node, data="type"):
            if type == edge_type:
                new_node = child_node
            if child_node.id == self.stop_action:
                return child_node
        if not new_node:
            raise DecisionError(f"No outgoing '{edge_type}' edge for node {node.id}")
        return new_node

    def run_pluggable_logic(self, function_string: str,
                            functions: dict[str, Callable] = CONDITIONAL_FUNCTIONS):
        function_name = function_string.split("(")[0]
        try:
            function = functions[function_name]
        except KeyError:
            raise DecisionError(f"No pluggable logic for function {function_name}")
        function_args = function_string.split(function_name)[1]
        function_args = ast.literal_eval(function_args)
        if type(function_args) is not tuple:
            function_args = (function_args,)
        try:
            return function(*function_args, self)
        except Exception as e:
            raise DecisionError(
                f"Error running pluggable logic {function_string} for: {type(e).__name__} {e}"
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


def engine_factory(graph, data, data_loader=None, skip=[], stop=None) -> DecisionEngine:
    # Used to mock out engine creation in tests
    return DecisionEngine(
        graph,
        data,
        skip=skip,
        data_loader=data_loader,
        stop=stop
    )
