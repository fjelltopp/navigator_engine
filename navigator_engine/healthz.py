from flask import Blueprint
from healthcheck import HealthCheck

from navigator_engine import model

healthz_bp = Blueprint('healthz', __name__)


def db_available():
    try:
        model.db.session.execute("SELECT 1")
    except Exception as e:
        return False, str(e)
    return True, "db ok"


health = HealthCheck()
health.add_check(db_available)


@healthz_bp.route('/healthz', methods=['GET'])
def healthz():
    return health.run()
