from navigator_engine import model
from navigator_engine.common.decision_engine import DecisionEngine
from typing import Any


def get_milestones(progress_report: dict[str, Any]) -> dict[str, Any]:
    milestones = {}
    for milestone_dict in progress_report['milestones']:
        milestone = model.load_node(node_ref=milestone_dict['id']).milestone
        milestone_dict = milestone_dict.copy()
        milestone_dict['title'] = milestone.title
        milestone_dict['checklist'] = []
        milestones[milestone_dict['id']] = milestone_dict
    return milestones


def add_action_breadcrumbs(checklist: list[dict[str, Any]], milestones: dict[str, Any],
                           action_breadcrumbs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for index, action_dict in enumerate(action_breadcrumbs):
        is_last_breadcrumb = (index + 1) == len(action_breadcrumbs)
        action = model.load_node(node_ref=action_dict['actionID']).action
        action_dict = action_dict.copy()
        action_dict['title'] = action.title
        action_dict['reached'] = True
        action_dict['complete'] = not action_dict['skipped'] and not is_last_breadcrumb
        action_dict['id'] = action_dict['actionID']
        if index > 0:
            last_breadcrumb_milestone = action_breadcrumbs[index - 1]['milestoneID']
            if last_breadcrumb_milestone and last_breadcrumb_milestone != action_dict['milestoneID']:
                checklist.append(milestones[action_breadcrumbs[index - 1]['milestoneID']])
        if not action_dict['milestoneID']:
            checklist.append(action_dict)
        else:
            milestones[action_dict['milestoneID']]['checklist'].append(action_dict)
        del action_dict['milestoneID']
        del action_dict['actionID']
    if action_breadcrumbs and action_breadcrumbs[-1]['milestoneID']:
        checklist.append(milestones[action_breadcrumbs[-1]['milestoneID']])
    return checklist


def build_checklist(engine: DecisionEngine) -> dict[str, Any]:
    checklist: list[dict[str, Any]] = []
    engine.decide()
    milestones = get_milestones(engine.progress.report)
    checklist = add_action_breadcrumbs(
        checklist,
        milestones,
        engine.progress.action_breadcrumbs
    )
    return {'checklist': checklist, 'progress': engine.progress.report['progress']}
