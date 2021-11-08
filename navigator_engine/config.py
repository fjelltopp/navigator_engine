import logging
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    PRODUCTION = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGGING_LEVEL = logging.INFO


class Testing(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234567890@db/test_navigator_engine'


class Development(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite://'
    INITIAL_GRAPH_CONFIG = 'Estimates_Navigator_BDG_Validations.xlsx'


class Production(Config):
    PRODUCTION = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234567890@db/engine'
    LOGGING_LEVEL = logging.WARNING
