from flask import Blueprint, jsonify, request
from navigator_engine.common.decision_engine import DecisionEngine
from navigator_engine.model import load_graph
from navigator_engine.common import DATA_LOADERS
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

    graph = load_graph(1)
    data = DATA_LOADERS['json_url']('url', 'authorization_header', input_data['data'])
    skip_actions = input_data.get('skipActions', [])

    engine = DecisionEngine(graph, data, skip=skip_actions)
    engine.decide()

    result = {
        "decision": engine.decision,
        "actions": engine.progress.action_breadcrumbs(),
        "skipped": engine.progress.skipped,
        "progress": engine.progress.report_progress(),
    }
    return result


@api_blueprint.route('/action/<action_id>')
def action(action_id):
    """
    Return the contents of a particular action.
    """
    return jsonify({
        "id": "xxx",
        "content": {
            "title": "Node Title",
            "displayHTML": "<p>Lorem Ipsum</p>",
            "skippable": True,
            "actionURL": "http://fjelltopp.org"
        }
    })
