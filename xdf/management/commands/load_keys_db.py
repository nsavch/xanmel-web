from django.core.management.base import BaseCommand
from django.conf import settings

from xanmel.db import XanmelDB
from xdf.server_db import ServerDB
from xanmel.modules.xonotic.models import *


class Command(BaseCommand):
    help = 'Pull updates server.db files to database'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='+')

    def handle(self, *args, **kwargs):
        XanmelDB(settings.XANMEL_CONFIG['settings']['db_url'])
        fn = kwargs['file'][0]
        servers = list(XDFServer.select())
        with open(fn, 'r') as f:
            for line in f.readlines():
                old, current = line.strip().split(' ')
                prefix = ''
                old = old[len(prefix):]
                current = current[len(prefix):]
                try:
                    old_key = XDFPlayerKey.get(crypto_idfp=old)
                    current_key = XDFPlayerKey.get(crypto_idfp=current)
                except DoesNotExist:
                    continue
                old_player = old_key.player
                current_player = current_key.player
                old_key.player = current_player
                old_key.save()
                if current_player.id == old_player.id:
                    # already merged
                    continue
                for server in servers:
                    for i in XDFSpeedRecord.select().where(XDFSpeedRecord.player == old_player,
                                                           XDFSpeedRecord.server == server):
                        print('Assigning speed record on {}/{} from {} to {}'.format(
                            server.name,
                            i.map,
                            i.player.nickname,
                            current_player.nickname
                        ))
                        i.player = current_player
                        i.save()
                    for i in XDFTimeRecord.select().where(XDFTimeRecord.player == old_player,
                                                          XDFTimeRecord.server == server):
                        try:
                            r = XDFTimeRecord.get(XDFTimeRecord.player == current_player,
                                                  XDFTimeRecord.server == server,
                                                  XDFTimeRecord.map == i.map)
                        except DoesNotExist:
                            i.player = current_player
                            i.save()
                        else:
                            map_name = i.map
                            if r.server_pos < i.server_pos:
                                print('Deleting record {}/{} of {}, as {} is higher'.format(
                                    server.name,
                                    map_name,
                                    i.player.nickname,
                                    r.player.nickname
                                ))
                                i.delete_instance(recursive=True)
                            elif r.server_pos > i.server_pos:
                                print('Assigning time record on {}/{} from {} to {}'.format(
                                    server.name,
                                    i.map,
                                    i.player.nickname,
                                    current_player.nickname
                                ))
                                i.player = current_player
                                i.save()
                                print('Deleting record {}/{} of {}, as {} is higher'.format(
                                    server.name,
                                    map_name,
                                    r.player.nickname,
                                    i.player.nickname
                                ))
                                r.delete_instance(recursive=True)
                            XDFTimeRecord.update_server_pos(server, [map_name])

            for i in XDFPlayer.select():
                try:
                    XDFPlayerKey.get(XDFPlayerKey.player == i)
                except DoesNotExist:
                    print('Removing player with no keys {}'.format(i.nickname))
                    i.delete_instance(recursive=True)
