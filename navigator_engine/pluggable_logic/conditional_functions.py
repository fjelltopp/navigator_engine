from navigator_engine.common import register_conditional


@register_conditional
def return_true(engine):
    return True


@register_conditional
def return_false(engine):
    return False


@register_conditional
def dict_value(key, engine):
    return bool(engine.data[key])


@register_conditional
def check_dict_value(key, value, engine):
    return engine.data[key] == value
