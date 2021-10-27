import logging


class Config(object):
    DEBUG = False
    TESTING = False
    PRODUCTION = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234567890@db/engine'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGGING_LEVEL = logging.INFO


class Testing(Config):
    TESTING = True


class Production(Config):
    PRODUCTION = True
    LOGGING_LEVEL = logging.WARNING
