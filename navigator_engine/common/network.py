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

    def get_milestones(self) -> None:
        if not self.milestones:
            milestones = []
            for node in self.networkx.nodes():
                if getattr(node, 'milestone_id'):
                    milestones.append(node)
            self.milestones = milestones
        return self.milestones

    def all_possible_paths(self, source=None, target=None):
        if not target:
            target = self.get_complete_node()
        if not source:
            source = self.get_root_node()
        return list(networkx.all_simple_paths(
            self.networkx,
            source=source,
            target=target
        ))

    def common_path(self, source):
        all_possible_paths = self.all_possible_paths(source)
        if not all_possible_paths:
            return []
        longest_path = max(all_possible_paths, key=len)
        nodes_common_to_all_paths = set.intersection(*map(set, all_possible_paths))
        common_path = list(filter(
            lambda node: node in nodes_common_to_all_paths,
            longest_path
        ))
        return common_path

    def milestone_path(self, source):
        common_path = self.common_path(source)[1:]
        milestone_path = [node for node in common_path if getattr(node, 'milestone_id')]
        return milestone_path
