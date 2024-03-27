from functools import wraps
from inspect import getfullargspec


def t(test):

    def wrapper(f):
        argspec = getfullargspec(f)
        argument_index = argspec.args.index('data')

        def get_service(*argc, **kwargs):
            print(argc[argument_index])
            print(kwargs)

        return get_service

    return wrapper


@t('data')
def te(t, u, data='Hola'):
    pass


te(1, 2, 3)
