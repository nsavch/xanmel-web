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
        for server in XDFServer.select().where(XDFServer.server_db_path.is_null(False)):
            print('Processing server', server.name)
            sdb = ServerDB.parse_server(server)
            changed_maps = changed_maps.union(sdb.save(server))
            sdb.pull_video(server)
        print(changed_maps)
        print('Updating global pos')
        # XDFTimeRecord.update_global_physics_pos(changed_maps)
        XDFTimeRecord.update_global_pos(changed_maps)

