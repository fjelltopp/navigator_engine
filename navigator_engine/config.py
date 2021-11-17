import logging
import os
base_directory = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    PRODUCTION = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234567890@db/navigator_engine'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGGING_LEVEL = logging.INFO


class Testing(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = f'sqlite+pysqlite:////{base_directory}/../testing.db'
    TEST_DATA_SPREADSHEET = f'{base_directory}/tests/test_data/Estimates_Navigator_BDG_Validations.xlsx'
    TEST_DATA_GRAPH_JSON = f'{base_directory}/tests/test_data/test_graphs.json'


class Development(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f'sqlite+pysqlite:////{base_directory}/../app.db'
    TEST_DATA_SPREADSHEET = f'{base_directory}/tests/test_data/Estimates_Navigator_BDG_Validations.xlsx'


class Production(Config):
    PRODUCTION = True
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "not-set")
    LOGGING_LEVEL = logging.ERROR
