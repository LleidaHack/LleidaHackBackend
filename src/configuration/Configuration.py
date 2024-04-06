# import configparser
import types
import os
import yaml


class Configuration:
    _FILE = None

    def __init__(self, file='src/configuration/local.yaml') -> None:
        '''loads the config and returs if already loaded'''
        if Configuration._FILE is None:
            Configuration._FILE = file
            Configuration.__instanciate()

    @staticmethod
    def __instanciate():
        # Configuration.CONFIG = types.SimpleNamespace()
        # here = os.path.abspath(os.path.dirname(__file__))
        with open(Configuration._FILE) as f:
            data = yaml.safe_load(f)
            for k, v in data.items():
                if type(v) == dict:
                    setattr(Configuration, k, types.SimpleNamespace())
                    for kk, vv in v.items():
                        setattr(getattr(Configuration, k), kk, vv)
                        # setattr(Configuration.CONFIG, k, v)
                else:
                    setattr(Configuration, k, v)


Configuration()
