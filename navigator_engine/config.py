import logging
import os


class Config(object):
    DEBUG = False
    TESTING = False
    PRODUCTION = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234567890@db/engine'
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
    LOGGING_LEVEL = logging.WARNING
