class BaseConfig:
    pass


class Dev(BaseConfig):
    DEBUG = True
    XANMEL_CONFIG = '../xanmel/xanmel.yaml'


class Prod(BaseConfig):
    DEBUG = False
    XANMEL_CONFIG = '/etc/xanmel.yaml'
