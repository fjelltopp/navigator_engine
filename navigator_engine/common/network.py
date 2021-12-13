import networkx
from navigator_engine.common import DecisionError
from navigator_engine import model


class Network():

    def __init__(self, networkx):

        self.networkx = networkx
        self.root_node = None
        self.complete_node = None
        self.milestones = None

    def get_complete_node(self) -> model.Node:

        if not self.complete_node:

            for node in self.networkx.nodes():

                if getattr(node, 'action') and node.action.complete:
                    self.complete_node = node
                    break

            else:
                raise DecisionError("Network has no complete node")

        return self.complete_node

    def get_root_node(self) -> model.Node:

        if not self.root_node:

            for node, in_degree in self.networkx.in_degree():

                if in_degree == 0:
                    self.root_node = node
                    break

            else:
                raise DecisionError("Network has no root node")

        return self.root_node

    def get_milestones(self) -> list[model.Node]:

        if not self.milestones:
            milestones = []

            for node in self.networkx.nodes():

                if getattr(node, 'milestone_id'):
                    milestones.append(node)

            self.milestones = milestones

        return self.milestones

    def all_possible_paths(self, source: model.Node = None,
                           target: model.Node = None) -> list[list[model.Node]]:

        if not target:
            target = self.get_complete_node()

        if not source:
            source = self.get_root_node()

        return list(networkx.all_simple_paths(
            self.networkx,
            source=source,
            target=target
        ))

    def common_path(self, source: model.Node = None,
                    target: model.Node = None, all_paths=None) -> tuple[list[model.Node], bool]:

        if not all_paths:
            all_paths = self.all_possible_paths(source, target)

        if not all_paths:
            return [], True

        path_fully_resolved = len(all_paths) == 1
        longest_path = max(all_paths, key=len)
        all_paths_as_sets = [set(path) for path in all_paths]
        nodes_common_to_all_paths = set.intersection(*all_paths_as_sets)
        common_path = list(filter(
            lambda node: node in nodes_common_to_all_paths,
            longest_path
        ))

        return common_path, path_fully_resolved

    def milestone_path(self, source: model.Node) -> tuple[list[model.Node], bool]:

        milestone_paths = []

        for path in self.all_possible_paths(source=source):
            path = path[1:]
            milestone_path = [node for node in path if getattr(node, 'milestone_id')]
            milestone_paths.append(milestone_path)

        return self.common_path(all_paths=milestone_paths)
