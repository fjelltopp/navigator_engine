from flask import Blueprint, jsonify, request, abort
from navigator_engine.common.decision_engine import DecisionEngine
from navigator_engine.model import load_graph
from navigator_engine.common import choose_graph, choose_data_loader
from navigator_engine import model
import json

api_blueprint = Blueprint('main', __name__, url_prefix='/api/')


@api_blueprint.route('/decide', methods=['POST'])
def decide():
    """
    Decide what needs to happen next for a given data file.

    POST Request takes the following json input:
    ```
        {
            "data": {
                "url": "<url from estimates dataset json datadict>",
                "authorization_header": "<optional value to be supplied as the Authorization header tag>"
            },
            "skipActions": ["<action_id>", "<action_id>"]
        }
    ```
    """
    input_data = json.loads(request.data)

    if not input_data.get('data'):
        abort(400, "No data specified in request")
    if not input_data['data'].get('url'):
        abort(400, "No url to data specified in request")

    graph = load_graph(choose_graph(input_data['data']['url']))
    data_loader = choose_data_loader(input_data['data']['url'])
    source_data = input_data['data']
    skip_requests = input_data.get('skipActions', [])
    stop_action = input_data.get('actionID')

    engine = DecisionEngine(
        graph,
        source_data,
        data_loader=data_loader,
        skip_requests=skip_requests,
        stop=stop_action
    )
    engine.decide()
    del engine.decision['node']

    if stop_action and stop_action != engine.decision['id']:
        abort(
            400,
            f"Please specify a valid actionID. The actionID {stop_action}"
            f" is not found in the action path {engine.progress.action_breadcrumbs}"
        )

    return jsonify({
        "decision": engine.decision,
        "actions": engine.progress.action_breadcrumbs,
        "removeSkipActions": engine.remove_skip_requests,
        "progress": engine.progress.report
    })


@api_blueprint.route('/action/<action_id>')
def action(action_id):
    """
    Get the details of a specific action in the task breadcrumbs.
    """

    node = model.load_node(node_ref=action_id)
    action = getattr(node, 'action', None)
    if not action:
        abort(400, f"Please specify a valid action ID. Action {action_id} not found.")

    return jsonify({
        'id': action_id,
        'content': action.to_dict()
    })


@api_blueprint.route('/actionlist', methods=['POST'])
def action_list():
    """
    Get a list of actions that need to be completed.

    POST Request takes the following json input:
    ```
        {
            "data": {
                "url": "<url from estimates dataset json datadict>",
                "authorization_header": "<optional value to be supplied as the Authorization header tag>"
            },
            "skipActions": ["<action_id>", "<action_id>"]
        }
    ```
    """
    decide_response = decide().json
    reached_actions = decide_response['actions']
    for action in reached_actions:
        action['title'] = model.load_node(node_ref=action['id']).action.title
        action['reached'] = True

    return jsonify({
        'milestones': decide_response['progress']['milestones'],
        'progress': decide_response['progress']['progress'],
        'actionList': reached_actions,
        'actionListFullyResolved': False
    })
