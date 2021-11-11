from flask import Blueprint, jsonify, request, abort
from navigator_engine.common.decision_engine import DecisionEngine
from navigator_engine.model import load_graph, load_node
from navigator_engine.common import choose_graph, choose_data_loader
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
    skip_actions = input_data.get('skipActions', [])

    engine = DecisionEngine(
        graph,
        source_data,
        data_loader=data_loader,
        skip=skip_actions
    )
    engine.decide()
    del engine.decision['node']

    return jsonify({
        "decision": engine.decision,
        "actions": engine.progress.action_breadcrumbs,
        "skippedActions": engine.progress.skipped,
        "removeSkipActions": engine.remove_skips,
        "progress": engine.progress.report
    })


@api_blueprint.route('/action/<node_id>')
def action(node_id):
    """
    Return the contents of a particular action.
    """
    node = load_node(node_id)
    if not node:
        abort(400, f"Invalid node ID: {node_id}")

    action = node.action
    if not action:
        abort(400, f"Node {node_id} is not an action")

    return jsonify({
        "id": node_id,
        "content": action.to_dict()
    })
