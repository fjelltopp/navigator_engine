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


def get_resource_from_dataset(resource_type: str, dataset: dict) -> dict:
    dataset_name = dataset['name']
    matching_resources = list(filter(
        lambda r: r['resource_type'] == resource_type,
        dataset.get('resources', [])
    ))
    if len(matching_resources) > 1:
        raise DecisionError(
            f"Multiple resources with type {resource_type} were found in the {dataset_name} dataset."
        )
    if matching_resources:
        return matching_resources[0]
    else:
        return {}


class DecisionError(Exception):
    """Raised when there is an error in the decision logic."""
    pass
