from navigator_engine.common import register_conditional


@register_conditional
def return_true(data):
    return True


@register_conditional
def check_dict_value(key, value, data):
    return data[key] == value
