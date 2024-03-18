import configparser
'''Module used to parse the config on the config.ini file'''


class Configuration:
    '''Used to parse tphe actual configuration'''
    CONFIG = None

    @staticmethod
    def set_up():
        '''loads the config and returs if already loaded'''
        if Configuration.CONFIG is None:
            Configuration.__instanciate__()
        return Configuration.CONFIG

    @staticmethod
    def __instanciate__():
        '''actually loads the config file'''
        Configuration.CONFIG = configparser.ConfigParser()
        Configuration.CONFIG.read('config.ini')

    # config = ConfigParser.ConfigParser()
    @staticmethod
    def get(section, option):
        '''returns a value from a section on the config'''
        Configuration.set_up()
        return Configuration.CONFIG.get(section, option)
