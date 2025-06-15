import os
import re
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
                # Check environment variable for config selection
                env = os.environ.get('ENV', 'main')
                config_file = f'config.{env}.yaml'
                
                if config_file in Configuration.__CONFIG_FILES:
                    file = config_file
                elif len(Configuration.__CONFIG_FILES) == 1:
                    file = Configuration.__CONFIG_FILES[0]
                else:
                    raise Exception(
                        f'Configuration file config.{env}.yaml not found. Available files: {Configuration.__CONFIG_FILES}')
            Configuration._FILE = os.path.join(Configuration.__CONFIG_PATH,
                                               file)
            Configuration.__instanciate__()

    @staticmethod
    def __instanciate_nested(k, v, c):
        setattr(c, k, types.SimpleNamespace())
        for kk, vv in v.items():
            if type(vv) == dict:
                Configuration.__instanciate_nested(kk, vv, getattr(c, k))
            else:
                setattr(getattr(c, k), kk, vv)

    @staticmethod
    def __substitute_env_vars(value):
        """Substitute environment variables in string values"""
        if isinstance(value, str):
            # Replace ${VAR_NAME} with environment variable value
            pattern = r'\$\{([^}]+)\}'
            def replace_env_var(match):
                env_var = match.group(1)
                return os.environ.get(env_var, match.group(0))
            return re.sub(pattern, replace_env_var, value)
        elif isinstance(value, dict):
            return {k: Configuration.__substitute_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [Configuration.__substitute_env_vars(item) for item in value]
        else:
            return value

    @staticmethod
    def __instanciate__():
        # Configuration.CONFIG = types.SimpleNamespace()
        # here = os.path.abspath(os.path.dirname(__file__))
        with open(Configuration._FILE) as f:
            data = yaml.safe_load(f)
            # Substitute environment variables
            data = Configuration.__substitute_env_vars(data)
            for k, v in data.items():
                if type(v) == dict:
                    Configuration.__instanciate_nested(k, v, Configuration)
                    # for kk, vv in v.items():
                    # setattr(getattr(Configuration, k), kk, vv)
                    # setattr(Configuration.CONFIG, k, v)
                else:
                    setattr(Configuration, k, v)


Configuration()