from .default import *

ALLOWED_HOSTS = ['xon.teichisma.info', 'portal.exe.pub']
DEBUG = False
TEMPLATE_DEBUG = False

with open('/etc/xanmel.yaml', 'r') as f:
    XANMEL_CONFIG = yaml.safe_load(f)

XONOTIC_SERVERS = XANMEL_CONFIG['modules']['xanmel.modules.xonotic.XonoticModule']['servers']

XONOTIC_XDF_DATABASES = {
    4: '/home/xonotic/infra/xonotic/data_defrag/data/server.db.defrag'
}
