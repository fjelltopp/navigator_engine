class Config(object):
    DEBUG = False
    TESTING = False
    PRODUCTION = False


class Production(Config):
    PRODUCTION = True


class Development(Config):
    DEBUG = True
    TESTING = True


class Testing(Config):
    TESTING = True
