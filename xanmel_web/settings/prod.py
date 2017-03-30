from .default import *

DEBUG = False
TEMPLATE_DEBUG = False

with open('/etc/xanmel.yaml', 'r') as f:
    XANMEL_CONFIG = yaml.safe_load(f)

XONOTIC_SERVERS = XANMEL_CONFIG['modules']['xanmel.modules.xonotic.XonoticModule']['servers']
