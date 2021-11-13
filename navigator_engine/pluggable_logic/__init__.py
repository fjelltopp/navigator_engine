from os.path import dirname, basename, isfile, join
from typing import Callable
import glob

# This code loads all modules in the package and makes them available to the importer
modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]

from . import *

CONDITIONAL_FUNCTIONS: dict[str, Callable] = {}
DATA_LOADERS: dict[str, Callable] = {}

"""
The expected use case is to import the registering decorator:
    ```
    from navigator_engine.common import register_conditional
    ```
Then write your function always with the final argument being "data":
    ```
    def check_dict_value(key, value, data):
        return data[key] == value
    ```
Then register your function with with the appropriate decorator:
    ```
    @register_conditional
    def check_dict_value(key, value, data):
        return data[key] == value
    ```
Your function should then be available to the DecisionEngine.
"""
