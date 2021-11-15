CONDITIONAL_FUNCTIONS = {}
DATA_LOADERS = {}


def choose_graph(file_url):
    # TODO:  choose the graph for a given file url
    # For now only one graph type
    return 1


def choose_data_loader(file_url):
    # TODO:  choose a data loader for the given file_url
    # For now only one type of file, so only one type of loader
    return "load_estimates_dataset('url', 'authorization_header')"


def register_conditional(f):
    CONDITIONAL_FUNCTIONS[f.__name__] = f
    return f


def register_loader(f):
    DATA_LOADERS[f.__name__] = f
    return f


class DecisionError(Exception):
    """Raised when there is an error in the decision logic."""
    pass


class DataLoadingError(Exception):
    """Raised when there is an error in loading data."""
    pass
