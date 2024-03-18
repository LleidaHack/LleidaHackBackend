from src.utils.Singleton import Singleton


class BaseService(metaclass=Singleton):
    def needs_service(service):
        def wrapper(f):
            def get_service(*args):
                s = args[0]
                if getattr(s, service.name) is None:
                    setattr(s, service.name, service())
            return get_service
        return wrapper  