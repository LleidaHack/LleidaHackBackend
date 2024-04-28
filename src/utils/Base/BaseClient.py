import importlib
from typing import Any, overload

from generated_src.lleida_hack_api_client.client import (AuthenticatedClient,
                                                         Client)


#TODO: must be singleton
class BaseClient():

    def needs_client(client):

        def wrapper(f):

            def get_client(*args):
                s = args[0]
                cli = client
                if type(cli) is str:
                    # equiv. of your `import matplotlib.text as text`
                    cli = importlib.import_module('src.Clients.' + client)
                    cli = getattr(cli, client)
                if getattr(s, cli.name) is None:
                    setattr(s, cli.name, cli())

            return get_client

        return wrapper

    def __init__(self) -> Any:
        self.__client = None

    @overload
    def __init__(self, url, token) -> Any:
        if token is None:
            self.__client = Client(base_url=url)
        self.__client = AuthenticatedClient(base_url=url, token=token)

    @property
    def client(self):
        if self.client is None or self.url is None:
            raise Exception()
        return self.__client
