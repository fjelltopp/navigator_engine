from flask import Blueprint, jsonify, request

api_blueprint = Blueprint('main', __name__, url_prefix='/api/')


@api_blueprint.route('/decision-engine/create', methods=['POST'])
def decision_engine_create():
    return jsonify({"message": "success"})


@api_blueprint.route('/decision-engine/<engine_id>/progress')
def decision_engine_progress(engine_id):
    return jsonify({
        "overallProgress": 35,
        "milestoneListFullyResolved": False,
        "milestones":
            [
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
    })


@api_blueprint.route('/decision-engine/<engine_id>/action-path')
def decision_engine_action_path(engine_id):
    return jsonify({
        "actions":
            ["<action_id>", "<action_id>", "<action_id>", "<action_id>"]
    })


@api_blueprint.route('/decision-engine/<engine_id>/decide')
def decision_engine_decide(engine_id):
    _skip_actions = request.args.get('skip-actions', default='')
    if len(_skip_actions) == 0:
        skip_actions = []
    else:
        skip_actions = _skip_actions.split(',')

    return jsonify({
        "id": "xxx",
        "skipped": False,
        "content": {
            "title": "Node Title",
            "display_html": "<p>Display HTML</p>",
            "skippable": True,
            "action_url": "http://fjelltopp.org"
        }
    })


@api_blueprint.route('/decision-engine/<engine_id>/action/<action_id>')
def decision_engine_action(engine_id, action_id):
    return jsonify({
        "id": "xxx",
        "skipped": True,
        "content": {
            "title": "Node Title",
            "display_html": "<p>Lorem Ipsum</p>",
            "skippable": True,
            "action_url": "http://fjelltopp.org"
        }
    })
