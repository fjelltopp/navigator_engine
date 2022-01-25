from navigator_engine import healthz


def test_db_available(mocker):
    mocker.patch(
        'navigator_engine.model.db.session.execute',
        return_value=None
    )
    check = healthz.db_available()
    assert check == (True, 'db ok')


def test_db_available_raises(mocker):
    mocker.patch('navigator_engine.model.db.session.execute',
                 side_effect=Exception('Mock Exception: DB not available'))

    check = healthz.db_available()
    assert check == (False, 'Mock Exception: DB not available')
