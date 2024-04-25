import os
import types

import yaml


class Configuration:
    _FILE = None
    __CONFIG_PATH = os.path.join('src', 'configuration')
    __CONFIG_FILES = None

    @staticmethod
    def __get_yaml_files():
        yaml_files = []
        for file in os.listdir(Configuration.__CONFIG_PATH):
            if file.endswith('.yaml'):
                yaml_files.append(file)
        return yaml_files

    def __init__(self, file=None) -> None:
        '''loads the config and returs if already loaded'''

        if Configuration._FILE is None:
            Configuration.__CONFIG_FILES = Configuration.__get_yaml_files()
            if file is None:
                if len(Configuration.__CONFIG_FILES) > 1:
                    raise Exception(
                        'Please select a configuration file to load')
                file = Configuration.__CONFIG_FILES[0]
            Configuration._FILE = os.path.join(Configuration.__CONFIG_PATH,
                                               file)
            Configuration.__instanciate__()

    @staticmethod
    def __instanciate_nested(k, v):
        setattr(Configuration, k, types.SimpleNamespace())
        for kk, vv in v.items():
            if type(vv) == dict:
                Configuration.__instanciate_nested(kk, vv)
            else:
                setattr(getattr(Configuration, k), kk, vv)

    @staticmethod
    def __instanciate__():
        # Configuration.CONFIG = types.SimpleNamespace()
        # here = os.path.abspath(os.path.dirname(__file__))
        with open(Configuration._FILE) as f:
            data = yaml.safe_load(f)
            for k, v in data.items():
                if type(v) == dict:
                    Configuration.__instanciate_nested(k, v)
                    # for kk, vv in v.items():
                    # setattr(getattr(Configuration, k), kk, vv)
                    # setattr(Configuration.CONFIG, k, v)
                else:
                    setattr(Configuration, k, v)

Configuration()