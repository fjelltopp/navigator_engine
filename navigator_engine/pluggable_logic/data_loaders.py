from navigator_engine.common import register_loader


@register_loader
def return_empty(data):
    return {}


@register_loader
def dict_value(key, data):
    return data[key]
