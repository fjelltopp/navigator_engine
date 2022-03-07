import logging
import os
base_directory = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    ENV_TYPE = os.getenv("ENV_TYPE")
    DEBUG = False
    TESTING = False
    PRODUCTION = False
    JSON_LOGGING = (os.getenv("JSON_LOGGING", 'false').lower() == 'true')
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234567890@db/navigator_engine'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGGING_LEVEL = logging.INFO
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    DASH_REROUTE_PREFIX = '/engine'
    DEFAULT_DECISION_GRAPH = f'{base_directory}/../Estimates 22 BDG [Final].xlsx'
    # LANGUAGES is hosted as an environment variable NAVIGATOR_LANGUAGES
    # DEFAULT_LANGUAGE is hosted as an environment variable NAVIGATOR_DEFAULT_LANGUAGE


class Testing(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = f'sqlite+pysqlite:////{base_directory}/../testing.db'
    DEFAULT_DECISION_GRAPH = f'{base_directory}/tests/test_data/Estimates Test Data.xlsx'
    DECISION_GRAPH_FOLDER = f'{base_directory}/tests/test_data/test_graphs/'
    DASH_REROUTE_PREFIX = ''


class Development(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f'sqlite+pysqlite:////{base_directory}/../app.db'
    DEFAULT_DECISION_GRAPH = f'{base_directory}/tests/test_data/Simple Development BDG.xlsx'


class Production(Config):
    PRODUCTION = True
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "not-set")
    LOGGING_LEVEL = logging.ERROR
    JSON_LOGGING = (os.getenv("JSON_LOGGING", 'true').lower() == 'true')
