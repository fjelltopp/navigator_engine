from navigator_engine.common import DecisionError
import navigator_engine.model as model
import networkx
import copy


class ProgressTracker():

    def __init__(self, network: networkx.DiGraph, route: list[str] = []) -> None:
        self.network = network
        self.previous_route = route.copy()
        self.entire_route = route.copy()
        self.route = []
        self.milestones = []
        self.skipped = []
        self.complete_node = self.get_complete_node()
        self.root_node = self.get_root_node()

    def report_progress(self) -> dict:
        milestones = copy.deepcopy(self.milestones)
        if milestones and not milestones[-1]['completed']:
            # Calculate percentage progress for current milestone
            milestones[-1]['progress'] = milestones[-1]['progress'].percentage_progress()
        milestones_to_complete, milestone_list_is_complete = self.milestones_to_complete()
        for node in milestones_to_complete:
            milestones.append({
                'id': node.milestone.id,
                'title': node.milestone.title,
                'progress': 0,
                'completed': False
            })
        return {
            'progress': self.percentage_progress(),
            'milestone_list_is_complete': milestone_list_is_complete,
            'milestones': milestones
        }

    def reset(self) -> None:
        self.entire_route = self.previous_route
        self.route = []
        self.skipped = []

    def add_milestone(self, milestone: model.Milestone,
                      milestone_progress, complete: bool = False) -> None:
        self.entire_route += milestone_progress.entire_route
        self.milestones.append({
            'id': milestone.id,
            'title': milestone.title,
            'progress': 100 if complete else milestone_progress,
            'completed': complete
        })

    def add_node(self, node: model.Node) -> None:
        self.entire_route.append(node)
        self.route.append(node)

    def pop_node(self) -> model.Node:
        node = self.entire_route[-1]
        self.entire_route = self.entire_route[:-1]
        self.route = self.route[:-1]
        return node

    def get_complete_node(self) -> model.Node:
        for node in self.network.nodes():
            if getattr(node, 'action') and node.action.complete:
                return node
        raise DecisionError("Network has no complete node")

    def get_root_node(self) -> model.Node:
        for node, in_degree in self.network.in_degree():
            if in_degree == 0:
                return node
        raise DecisionError("Network has no root node")

    def get_milestones(self) -> None:
        for node in self.network.nodes():
            if getattr(node, 'milestone_id'):
                self.milestones.append(node.milestone)

    def percentage_progress(self) -> int:
        route = self.route.copy()
        if getattr(self.route[-1], "action_id"):
            if self.route[-1].action.complete:
                return 100
            route = route[:-1]  # If we're on an action don't count it
        current_node = route[-1]
        distance_travelled = len(route) - 1
        all_possible_path_lengths = map(len, networkx.all_simple_paths(
            self.network,
            source=current_node,
            target=self.complete_node
        ))
        longest_path_length = max(list(all_possible_path_lengths)) - 1
        progress = distance_travelled / (longest_path_length + distance_travelled)
        percentage_progress = int(round(progress*100))
        return percentage_progress

    def milestones_to_complete(self) -> tuple[list[model.Node], bool]:
        if getattr(self.route[-1], "action_id"):
            current_node = self.route[-2]
        else:
            current_node = self.route[-1]
        all_possible_paths = networkx.all_simple_paths(
            self.network,
            source=current_node,
            target=self.complete_node
        )
        milestone_paths = []
        # Get all "milestone" paths
        for path in all_possible_paths:
            path = path[1:]
            milestone_paths.append([node for node in path if getattr(node, 'milestone_id')])
        # The first n elements that are the same in every milestone path consitute "known" milestones
        milestones_to_complete = [x[0] for x in zip(*milestone_paths) if len(x) == x.count(x[0])]
        # If all paths are equal, we know we have the complete list of remaining milestones
        milestone_list_is_complete = False
        if len(milestone_paths) == milestone_paths.count(milestone_paths[0]):
            milestone_list_is_complete = True
        return milestones_to_complete, milestone_list_is_complete
