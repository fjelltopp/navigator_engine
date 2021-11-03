CONDITIONAL_FUNCTIONS = {}
DATA_LOADERS = {}


def register_conditional(f):
    CONDITIONAL_FUNCTIONS[f.__name__] = f


def register_loader(f):
    DATA_LOADERS[f.__name__] = f
