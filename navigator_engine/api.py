from flask import Blueprint, jsonify, request
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
    graph = load_graph(choose_graph(input_data['data']['url']))
    data_loader = choose_data_loader(input_data['data']['url'])
    data = data_loader('url', 'authorization_header', input_data['data'])
    skip_actions = input_data.get('skipActions', [])

    engine = DecisionEngine(graph, data, skip=skip_actions)
    engine.decide()
    del engine.decision['node']

    return jsonify({
        "decision": engine.decision,
        "actions": engine.progress.action_breadcrumbs,
        "skippedActions": engine.progress.skipped,
        "progress": engine.progress.report,
    })


@api_blueprint.route('/action/<node_id>')
def action(node_id):
    """
    Return the contents of a particular action.
    """
    action = load_node(node_id).action
    return jsonify({
        "id": node_id,
        "content": action.to_dict()
    })
