from navigator_engine.common import register_conditional


@register_conditional
def return_true(data):
    return True


@register_conditional
def return_false(data):
    return False


@register_conditional
def dict_value(key, data):
    return bool(data[key])


@register_conditional
def check_dict_value(key, value, data):
    return data[key] == value
