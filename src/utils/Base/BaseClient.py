import importlib
from typing import Any

from generated_src.lleida_hack_mail_api_client.client import AuthenticatedClient, Client
from src.utils.singleton import Singleton


# TODO: must be singleton
class BaseClient(metaclass=Singleton):
    def needs_client(self):
        def wrapper(f):
            def get_client(*args):
                s = args[0]
                cli = self
                if type(cli) is str:
                    # equiv. of your `import matplotlib.text as text`
                    cli = importlib.import_module('src.Clients.' + self)
                    cli = getattr(cli, self)
                if getattr(s, cli.name) is None:
                    setattr(s, cli.name, cli())
                return f(*args)

            return get_client

        return wrapper

    def __init__(self, url, token) -> Any:
        self._url = url
        self._token = token
        if token is None:
            self.__client = Client(base_url=url)
        else:
            self.__client = AuthenticatedClient(base_url=url, token=token)

    @property
    def client(self) -> AuthenticatedClient:
        if self.__client is None or self._url is None:
            raise Exception()
        return self.__client
