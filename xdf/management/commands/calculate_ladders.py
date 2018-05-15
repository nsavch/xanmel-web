import math
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings

from xanmel.db import XanmelDB
from xdf.server_db import ServerDB
from xanmel.modules.xonotic.models import *


class Command(BaseCommand):
    help = 'Calculates ladder data'

    def handle(self, *args, **kwargs):
        XanmelDB(settings.XANMEL_CONFIG['settings']['db_url'])
        for algo in LadderAlgo:
            if algo == LadderAlgo.CLASSIC:
                for t in LadderType:
                    if t == LadderType.GLOBAL:
                        ladder, _ = XDFLadder.get_or_create(algo=algo.value, type=t.value, physics=None, server=None)
                        for player in XDFPlayer.select():
                            points = Decimal('0')
                            data = defaultdict(int)
                            for speed_record in XDFSpeedRecord.select().where(XDFSpeedRecord.player == player):
                                if XDFSpeedRecord.select().where(
                                        XDFSpeedRecord.player != player,
                                        XDFSpeedRecord.speed > speed_record.speed).count() == 0:
                                    points += 10
                                    data['speed'] += 1
                            maps_processed = set()
                            for time_record in XDFTimeRecord.select().where(
                                    XDFTimeRecord.player == player,
                                    XDFTimeRecord.global_pos <= 100).order_by(XDFTimeRecord.global_pos):
                                if time_record.map not in maps_processed:
                                    maps_processed.add(time_record.map)
                                    points += math.floor(100 / time_record.global_pos)
                                    data[time_record.global_pos] += 1
                            try:
                                lp = XDFLadderPosition.get(XDFLadderPosition.ladder == ladder,
                                                           XDFLadderPosition.player == player)
                            except DoesNotExist:
                                lp = XDFLadderPosition.create(ladder=ladder, player=player, points=points, data=data)
                            else:
                                lp.points = points
                                lp.data = data
                                lp.save()
                        positions = (XDFLadderPosition.select()
                                     .where(XDFLadderPosition.ladder == ladder)
                                     .order_by(XDFLadderPosition.points.desc()))
                        for i, lp in enumerate(positions, start=1):
                            lp.position = i
                            lp.save()
                    elif t == LadderType.SERVER:
                        for server in XDFServer.select():
                            ladder, _ = XDFLadder.get_or_create(algo=algo.value, type=t.value, physics=None,
                                                                server=server)
                            for player in XDFPlayer.select():
                                points = Decimal('0')
                                data = defaultdict(int)
                                for speed_record in XDFSpeedRecord.select().where(XDFSpeedRecord.player == player,
                                                                                  XDFSpeedRecord.server == server):
                                    points += 10
                                    data['speed'] += 1
                                for time_record in XDFTimeRecord.select().where(XDFTimeRecord.player == player,
                                                                                XDFTimeRecord.server == server,
                                                                                XDFTimeRecord.server_pos <= 100):
                                    points += math.floor(100 / time_record.server_pos)
                                    data[time_record.server_pos] += 1

                                try:
                                    lp = XDFLadderPosition.get(XDFLadderPosition.ladder == ladder,
                                                               XDFLadderPosition.player == player)
                                except DoesNotExist:
                                    lp = XDFLadderPosition.create(ladder=ladder, player=player, points=points,
                                                                  data=data)
                                else:
                                    lp.points = points
                                    lp.data = data
                                    lp.save()
                            positions = (XDFLadderPosition.select()
                                         .where(XDFLadderPosition.ladder == ladder)
                                         .order_by(XDFLadderPosition.points.desc()))
                            for i, lp in enumerate(positions, start=1):
                                lp.position = i
                                lp.save()
