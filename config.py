import configparser

class Configuration:
    CONFIG = None
    @staticmethod
    def setUp():
        if Configuration.CONFIG is None:
            Configuration.__instanciate__()
        return Configuration.CONFIG
    
    @staticmethod
    def __instanciate__():
        Configuration.CONFIG = configparser.ConfigParser()
        Configuration.CONFIG.read('config.ini')
    # config = ConfigParser.ConfigParser()
    @staticmethod
    def get(section, option):
        Configuration.setUp()
        return Configuration.CONFIG.get(section, option)