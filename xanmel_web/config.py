class BaseConfig:
    pass


class Dev(BaseConfig):
    DEBUG = True
    XANMEL_CONFIG = '../xanmel/xanmel.yaml'
