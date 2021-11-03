from navigator_engine.common import register_loader


@register_loader
def return_empty(data):
    return {}
