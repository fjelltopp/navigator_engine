from flask import Blueprint, jsonify

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
            "skip_actions": ["<action_id>", "<action_id>"]
        }
    ```
    """

    return jsonify({
        "actions": ["<action_id>", "<action_id>", "<action_id>", "<action_id>"],
        "skipped": ["<action_id>", "<action_id>"],
        "progress": {
            "overallProgress": 35,
            "milestoneListFullyResolved": False,
            "milestones": [
                {
                    "id": "xxx",
                    "title": "Naomi Data Prep",
                    "completed": True,
                    "progress": 100
                }, {
                    "id": "yyy",
                    "title": "Shiny 90 Data Prep",
                    "completed": False,
                    "progress": 50
                }, {
                    "id": "zzz",
                    "title": "Update Spectrum",
                    "completed": False,
                    "progress": 0
                }
            ]
        },
        "decision": {
            "id": "xxx",
            "content": {
                "title": "Node Title",
                "display_html": "<p>Lorem Ipsum</p>",
                "skippable": True,
                "action_url": "http://fjelltopp.org"
            }
        }
    })


@api_blueprint.route('/action/<action_id>')
def action(action_id):
    """
    Return the contents of a particular action.
    """
    return jsonify({
        "id": "xxx",
        "content": {
            "title": "Node Title",
            "display_html": "<p>Lorem Ipsum</p>",
            "skippable": True,
            "action_url": "http://fjelltopp.org"
        }
    })
