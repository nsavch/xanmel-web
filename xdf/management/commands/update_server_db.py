from django.core.management.base import BaseCommand
from django.conf import settings

from xanmel.db import XanmelDB
from xdf.server_db import ServerDB
from xanmel.modules.xonotic.models import *


class Command(BaseCommand):
    help = 'Pull updates server.db files to database'

    def handle(self, *args, **kwargs):
        XanmelDB(settings.XANMEL_CONFIG['settings']['db_url'])
        changed_maps = set()
        for server_id in settings.XONOTIC_XDF_DATABASES:
            print('Processing server', server_id)
            sdb = ServerDB.parse_server(server_id)
            changed_maps = changed_maps.union(sdb.save(server_id))
            sdb.pull_video(server_id)
        print(changed_maps)
        print('Updating global pos')
        XDFTimeRecord.update_global_physics_pos(changed_maps)
        XDFTimeRecord.update_global_pos(changed_maps)

