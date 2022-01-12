from navigator_engine.common.network import Network
from typing import Any
import navigator_engine.model as model
import copy


class ProgressTracker():

    def __init__(self, network: Network,
                 route: list[model.Node] = [], skipped_actions: list[str] = []) -> None:
        self.network = network
        self.previous_route: list[model.Node] = route.copy()
        self.entire_route: list[model.Node] = route.copy()
        self.route: list[model.Node] = []
        self.milestones: list[dict] = []
        self.previously_skipped_actions: list[str] = skipped_actions.copy()
        self.skipped_actions: list[str] = skipped_actions.copy()
        self.action_breadcrumbs: list[dict[str, Any]] = []
        self.report: dict = {}

    def report_progress(self) -> dict:
        milestones = copy.deepcopy(self.milestones)
        current_milestone = None
        if milestones and not milestones[-1]['completed']:
            # Calculate percentage progress for current milestone
            milestones[-1]['progress'] = milestones[-1]['progress'].percentage_progress()
            current_milestone = milestones[-1]['id']
        milestones_to_complete, milestone_list_resolved = self.milestones_to_complete()
        for node in milestones_to_complete:
            milestones.append({
                'id': node.ref,
                'title': node.milestone.title,
                'progress': 0,
                'completed': False
            })
        self.report = {
            'progress': self.percentage_progress(),
            'currentMilestoneID': current_milestone,
            'milestoneListFullyResolved': milestone_list_resolved,
            'milestones': milestones
        }
        return self.report

    def reset(self) -> None:
        self.entire_route = self.previous_route
        self.route = []
        self.skipped_actions = self.previously_skipped_actions

    def add_milestone(self, milestone_node: model.Node, milestone_progress) -> None:
        self.entire_route = milestone_progress.entire_route
        self.skipped_actions = milestone_progress.skipped_actions
        milestone_complete = self.entire_route[-1].action.complete
        self.milestones.append({
            'id': milestone_node.ref,
            'title': milestone_node.milestone.title,
            'progress': 100 if milestone_complete else milestone_progress,
            'completed': milestone_complete
        })

        def add_milestone_id(breadcrumb):
            breadcrumb['milestoneID'] = milestone_node.ref
            return breadcrumb
        self.action_breadcrumbs += list(map(
            add_milestone_id,
            milestone_progress.action_breadcrumbs
        ))

        if milestone_complete:
            # Don't include the complete action in the action_breadcrumbs
            self.action_breadcrumbs.pop()

    def add_node(self, node: model.Node) -> None:
        self.entire_route.append(node)
        self.route.append(node)
        self.drop_action_breadcrumb()

    def drop_action_breadcrumb(self) -> None:
        if len(self.route) < 2:
            return
        parent_node = self.route[-2]
        current_node = self.route[-1]

        manual_confirmation = False
        if getattr(parent_node, 'conditional_id'):
            function = parent_node.conditional.function
            manual_confirmation = function.startswith("check_manual_confirmation")

        # If the current node is a conditional, add the child node that is an action
        for parent_node, child_node in self.network.networkx.out_edges(parent_node):
            if (child_node != current_node
                    and getattr(child_node, 'action_id')
                    and not child_node.action.complete):
                self.action_breadcrumbs.append({
                    'id': child_node.ref,
                    'milestoneID': None,  # Updated under self.add_milestone
                    'skipped': child_node.ref in self.skipped_actions,
                    'manualConfirmationRequired': manual_confirmation,
                    'reached': True,
                    'title': child_node.action.title,
                    'terminus': child_node.action.complete
                })

        # If the current node is an action, add it to the breadcrumbs.
        if getattr(current_node, 'action_id'):
            self.action_breadcrumbs.append({
                'id': current_node.ref,
                'milestoneID': None,  # Updated under self.add_milestone
                'skipped': False,
                'manualConfirmationRequired': manual_confirmation,
                'reached': True,
                'terminus': current_node.action.complete,
                'title': current_node.action.title
            })

    def pop_node(self) -> str:
        node_ref = self.entire_route[-1]
        self.entire_route = self.entire_route[:-1]
        self.route = self.route[:-1]
        self.action_breadcrumbs = self.action_breadcrumbs[:-1]
        return node_ref

    def percentage_progress(self) -> int:
        route = self.route.copy()
        if getattr(route[-1], "action_id"):
            if route[-1].action.complete:
                return 100
            route = route[:-1]  # If we're on an action don't count it
        current_node = route[-1]
        distance_travelled = len(route) - 1
        all_possible_paths = self.network.all_possible_paths(current_node)
        longest_path_length = len(max(all_possible_paths, key=len)) - 1
        progress = distance_travelled / (longest_path_length + distance_travelled)
        percentage_progress = int(round(progress * 100))
        return percentage_progress

    def milestones_to_complete(self):
        if getattr(self.route[-1], "action_id"):
            current_node = self.route[-2]
        else:
            current_node = self.route[-1]
        return self.network.milestone_path(current_node)
