import importlib

from src.utils.singleton import Singleton


class BaseService(metaclass=Singleton):
    def needs_service(self):
        def wrapper(f):
            def get_service(*args):
                s = args[0]
                ser = self
                if type(self) is str:
                    # equiv. of your `import matplotlib.text as text`
                    ser = importlib.import_module(
                        'src.impl.' + self.replace('Service', '') + '.service'
                    )
                    ser = getattr(ser, self)

                if getattr(s, ser.name) is None:
                    setattr(s, ser.name, ser())
                return f(*args)

            return get_service

        return wrapper
