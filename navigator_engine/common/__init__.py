CONDITIONAL_FUNCTIONS = {}
DATA_LOADERS = {}


def choose_graph(file_url):
    # TODO:  choose the graph for a given file url
    # For now only one graph type
    return 1


def register_conditional(f):
    CONDITIONAL_FUNCTIONS[f.__name__] = f


def register_loader(f):
    DATA_LOADERS[f.__name__] = f


class DecisionError(Exception):
    """Raised when there is an error in the decision logic."""
    pass
