from navigator_engine.common import DecisionError
import networkx


class ProgressTracker():

    def __init__(self, network, route = []):
        self.network = network
        self.previous_route = route.copy()
        self.complete_route = route.copy()
        self.milestone_route = []
        self.milestones = self.get_milestones()
        self.complete_node = self.get_complete_node()

    def reset(self):
        self.complete_route = self.previous_route
        self.milestone_route = []

    def add_node(self, node):
        self.complete_route.append(node)
        self.milestone_route.append(node)

    def pop_node(self):
        node = self.complete_route[-1]
        self.complete_route = self.complete_route[:-1]
        self.milestone_route = self.milestone_route[:-1]
        return node

    def get_complete_node(self):
        for node in self.network.nodes():
            if getattr(node, 'action') and node.action.complete:
                return node
        raise DecisionError("Graph {graph.id} ({graph.title}) has no complete node")

    def get_milestones(self):
        for node in self.network.nodes():
            if getattr(node, 'milestone_id'):
                self.milestones.append(node.milestone)

    def progress(self):
        if not self.milestone_route or not getattr(self.milestone_route[-1], "action_id"):
            raise DecisionError("Can only calculate progress for action nodes.")
        current_node = self.milestone_route[-2]
        distance_travelled = len(self.milestone_route[:-1])

        all_possible_path_lengths = map(len, networkx.all_simple_paths(
            self.network,
            source=current_node,
            target=self.complete_node
        ))
        longest_path_length = max(list(all_possible_path_lengths)) - 1
        progress = distance_travelled / (longest_path_length + distance_travelled)
        percentage_progress = int(round(progress*100))
        return percentage_progress

    def milestones_to_complete(self):
        if not self.milestone_route or not getattr(self.milestone_route[-1], "action_id"):
            raise DecisionError("Can only calculate milestones to complete for action nodes.")
        current_node = self.milestone_route[-2]
        all_possible_paths = networkx.all_simple_paths(
            self.network,
            source=current_node,
            target=self.complete_node
        )
        milestone_paths = []
        # Get all "milestone" paths
        for path in all_possible_paths:
            milestone_paths.append([node for node in path if getattr(node, 'milestone_id')])
        # The first n elements that are the same in every milestone path consitute "known" milestones
        milestones_to_complete = [x[0] for x in zip(*milestone_paths) if len(x) == x.count(x[0])]
        # If all paths are equal, we know we have the complete list of remaining milestones
        milestone_list_is_complete = False
        if len(milestone_paths) == milestone_paths.count(milestone_paths[0]):
            milestone_list_is_complete = True
        return milestones_to_complete, milestone_list_is_complete
