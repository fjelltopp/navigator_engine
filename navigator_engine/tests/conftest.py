import pytest
from navigator_engine.tests.util import app
from navigator_engine.model import db


@pytest.fixture
def client():
    """
    Passes as a test_client to the test (as arg "client"), used to fetch
    end points from the flask app.  e.g. client.get("/")
    """
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
        yield client


@pytest.fixture
def with_app_context():
    """
    Runs the test within the flask app context.  This should probably be used if
    the test is failing with a RuntimeError "No application found".
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield
