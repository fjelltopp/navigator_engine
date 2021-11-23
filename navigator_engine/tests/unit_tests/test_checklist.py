from navigator_engine.common import checklist_builder
from navigator_engine.tests import factories


def test_get_milestones(mocker):
    progress_report = {
        'milestones': [
            {'id': 'test-m-1', 'complete': True, 'progress': 100},
            {'id': 'test-m-2', 'complete': False, 'progress': 67},
            {'id': 'test-m-3', 'complete': False, 'progress': 0}
        ]
    }

    def side_effect(node_ref=''):
        titles = {
            'test-m-1': 'Milestone 1',
            'test-m-2': 'Milestone 2',
            'test-m-3': 'Milestone 3'
        }
        milestone = factories.MilestoneFactory(title=titles[node_ref])
        return factories.NodeFactory(ref=node_ref, milestone=milestone)
    mocker.patch(
        'navigator_engine.common.checklist_builder.model.load_node',
        side_effect=side_effect
    )
    milestones = checklist_builder.get_milestones(progress_report)
    assert milestones == {
        'test-m-1': {
            'id': 'test-m-1',
            'complete': True,
            'progress': 100,
            'title': 'Milestone 1',
            'checklist': []
        },
        'test-m-2': {
            'id': 'test-m-2',
            'complete': False,
            'progress': 67,
            'title': 'Milestone 2',
            'checklist': []
        },
        'test-m-3': {
            'id': 'test-m-3',
            'complete': False,
            'progress': 0,
            'title': 'Milestone 3',
            'checklist': []
        }
    }


def test_add_action_breadcrumbs(mocker):
    milestones = {
        'test-m-1': {
            'id': 'test-m-1',
            'complete': True,
            'progress': 100,
            'title': 'Milestone 1',
            'checklist': []
        },
        'test-m-2': {
            'id': 'test-m-2',
            'complete': False,
            'progress': 67,
            'title': 'Milestone 2',
            'checklist': []
        },
        'test-m-3': {
            'id': 'test-m-3',
            'complete': False,
            'progress': 0,
            'title': 'Milestone 3',
            'checklist': []
        }
    }
    action_breadcrumbs = [
        {'actionID': 'tst-2-3-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
        {'actionID': 'tst-1-4-a', 'milestoneID': 'test-m-1', 'skipped': False, 'manualConfirmationRequired': False},
        {'actionID': 'tst-1-5-a', 'milestoneID': 'test-m-1', 'skipped': False, 'manualConfirmationRequired': False},
        {'actionID': 'tst-1-6-a', 'milestoneID': 'test-m-1', 'skipped': False, 'manualConfirmationRequired': False},
        {'actionID': 'tst-1-7-a', 'milestoneID': None, 'skipped': False, 'manualConfirmationRequired': False},
        {'actionID': 'tst-2-4-a', 'milestoneID': 'test-m-2', 'skipped': False, 'manualConfirmationRequired': False},
        {'actionID': 'tst-2-5-a', 'milestoneID': 'test-m-2', 'skipped': False, 'manualConfirmationRequired': False}
    ]

    def side_effect(node_ref=''):
        action = factories.ActionFactory(title=node_ref.upper())
        return factories.NodeFactory(ref=node_ref, action=action)
    mocker.patch(
        'navigator_engine.common.checklist_builder.model.load_node',
        side_effect=side_effect
    )

    result = checklist_builder.add_action_breadcrumbs([], milestones, action_breadcrumbs)
    assert result == [{
        'id': 'tst-2-3-a',
        'skipped': False,
        'manualConfirmationRequired': False,
        'title': 'TST-2-3-A',
        'complete': True,
        'reached': True
    }, {
        'id': 'test-m-1',
        'complete': True,
        'progress': 100,
        'title': 'Milestone 1',
        'checklist': [{
            'id': 'tst-1-4-a',
            'skipped': False,
            'manualConfirmationRequired': False,
            'title': 'TST-1-4-A',
            'complete': True,
            'reached': True
        }, {
            'id': 'tst-1-5-a',
            'skipped': False,
            'manualConfirmationRequired': False,
            'title': 'TST-1-5-A',
            'complete': True,
            'reached': True
        }, {
            'id': 'tst-1-6-a',
            'skipped': False,
            'manualConfirmationRequired': False,
            'title': 'TST-1-6-A',
            'complete': True,
            'reached': True
        }]
    }, {
        'id': 'tst-1-7-a',
        'skipped': False,
        'manualConfirmationRequired': False,
        'title': 'TST-1-7-A',
        'complete': True,
        'reached': True
    }, {
        'id': 'test-m-2',
        'complete': False,
        'progress': 67,
        'title': 'Milestone 2',
        'checklist': [{
            'id': 'tst-2-4-a',
            'skipped': False,
            'manualConfirmationRequired': False,
            'title': 'TST-2-4-A',
            'complete': True,
            'reached': True
        }, {
            'id': 'tst-2-5-a',
            'skipped': False,
            'manualConfirmationRequired': False,
            'title': 'TST-2-5-A',
            'complete': False,
            'reached': True
        }]
    }]
